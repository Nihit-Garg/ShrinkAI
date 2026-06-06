"use client";

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { fetchApi } from '@/lib/api';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { ChatInput } from '@/components/chat/ChatInput';
import { TypingPulse } from '@/components/chat/TypingPulse';
import { SessionPicker } from '@/components/chat/SessionPicker';
import { CrisisBanner } from '@/components/chat/CrisisBanner';
import { LogOut, TrendingUp } from 'lucide-react';
import { ProtectedPage } from '@/components/ProtectedPage';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface SessionSummary {
  session_id: string;
  started_at: string;
  last_message_preview: string | null;
  last_message_role: 'user' | 'assistant' | null;
}

// 'loading'  – fetching sessions from backend
// 'picker'   – user choosing to continue or start fresh
// 'chat'     – active conversation
type ChatView = 'loading' | 'picker' | 'chat';

const WELCOME_MSG: Message = {
  id: 'welcome-msg',
  role: 'assistant',
  content:
    "Hello. I'm here to offer a safe, confidential space for us to explore your thoughts and feelings. Please, take your time and share whatever is on your mind.",
};

export default function ChatPage() {
  return (
    <ProtectedPage>
      <ChatContent />
    </ProtectedPage>
  );
}

function ChatContent() {
  const { user, logout, checkQuestionnaireStatus } = useAuth();
  const router = useRouter();

  const [view, setView] = useState<ChatView>('loading');
  const [pastSessions, setPastSessions] = useState<SessionSummary[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showCrisis, setShowCrisis] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // ── On mount: guard questionnaire, then load sessions ───────────────────────
  useEffect(() => {
    if (!user) return;

    const init = async () => {
      // 1. Ensure questionnaire is done
      const completed = await checkQuestionnaireStatus();
      if (!completed) {
        router.push('/questionnaire');
        return;
      }

      // 2. Fetch past sessions for the picker
      try {
        const data = await fetchApi('/conversation/sessions');
        const sessions: SessionSummary[] = data.sessions ?? [];

        if (sessions.length === 0) {
          // No history — go straight to fresh chat
          setMessages([WELCOME_MSG]);
          setView('chat');
        } else {
          setPastSessions(sessions);
          setView('picker');
        }
      } catch {
        // Fallback: start fresh if sessions endpoint fails
        setMessages([WELCOME_MSG]);
        setView('chat');
      }
    };

    init();
  }, [user]);

  // Auto-scroll
  useEffect(() => {
    if (view === 'chat') {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading, view]);

  // ── Session picker handlers ──────────────────────────────────────────────────
  const handleContinueSession = async (sid: string) => {
    setView('loading');
    try {
      const data = await fetchApi(`/conversation/history?session_id=${sid}`);
      const loaded: Message[] = (data.messages ?? []).map(
        (m: { role: string; content: string; created_at: string }, i: number) => ({
          id: `history-${i}`,
          role: m.role as 'user' | 'assistant',
          content: m.content,
        })
      );
      setMessages(loaded.length > 0 ? loaded : [WELCOME_MSG]);
      setSessionId(sid);
      setView('chat');
    } catch {
      // On error fall back to fresh chat
      setMessages([WELCOME_MSG]);
      setSessionId(null);
      setView('chat');
    }
  };

  const handleStartFresh = () => {
    setMessages([WELCOME_MSG]);
    setSessionId(null);
    setView('chat');
  };

  // ── Send message ─────────────────────────────────────────────────────────────
  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMsgContent = inputValue.trim();
    setInputValue('');

    const tempId = `temp-${Date.now()}`;
    setMessages((prev) => [...prev, { id: tempId, role: 'user', content: userMsgContent }]);
    setIsLoading(true);

    try {
      const payload: { content: string; session_id?: string } = { content: userMsgContent };
      if (sessionId) payload.session_id = sessionId;

      const response = await fetchApi('/conversation/message', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      if (!sessionId) setSessionId(response.session_id);

      // Show crisis helpline banner if the backend flagged it
      if (response.crisis_detected) {
        setShowCrisis(true);
      }

      setMessages((prev) => [
        ...prev,
        { id: response.message_id, role: 'assistant', content: response.content },
      ]);
    } catch (error: any) {
      console.error('Failed to send message:', error);
      setMessages((prev) => prev.filter((m) => m.id !== tempId));
      setInputValue(userMsgContent);
    } finally {
      setIsLoading(false);
    }
  };

  // ── Render: loading spinner ─────────────────────────────────────────────────
  if (view === 'loading') {
    return (
      <div className="flex-1 flex items-center justify-center bg-[var(--color-sand)]">
        <div className="w-8 h-8 rounded-full bg-[var(--color-sage)]/30 animate-[breathe_2s_ease-in-out_infinite]" />
      </div>
    );
  }

  // ── Render: session picker ──────────────────────────────────────────────────
  if (view === 'picker') {
    return (
      <div className="flex-1 flex flex-col h-screen max-h-[100dvh] overflow-hidden bg-[var(--color-sand)]">
        <header className="flex justify-between items-center px-6 py-4 border-b border-[var(--color-sage)]/10 bg-[var(--color-sand)]/80 backdrop-blur-md">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-[var(--color-sage)]/20 flex items-center justify-center">
              <div className="w-4 h-4 rounded-full bg-[var(--color-sage)] opacity-80" />
            </div>
            <h1 className="text-xl font-medium text-[var(--color-charcoal)]">Shrink AI</h1>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push('/mood')}
              className="p-2 text-[var(--color-slate)] hover:text-[var(--color-sage)] transition-colors rounded-full hover:bg-black/5"
              title="Mood trend"
            >
              <TrendingUp size={18} />
            </button>
            <button
              onClick={logout}
              className="p-2 text-[var(--color-slate)] hover:text-[var(--color-charcoal)] transition-colors rounded-full hover:bg-black/5"
              title="Sign Out"
            >
              <LogOut size={20} />
            </button>
          </div>
        </header>

        <SessionPicker
          sessions={pastSessions}
          userName={user?.email ?? ''}
          onContinue={handleContinueSession}
          onStartFresh={handleStartFresh}
        />
      </div>
    );
  }

  // ── Render: active chat ─────────────────────────────────────────────────────
  return (
    <div className="flex-1 flex flex-col h-screen max-h-[100dvh] overflow-hidden bg-[var(--color-sand)]">
      <header className="flex justify-between items-center px-6 py-4 border-b border-[var(--color-sage)]/10 bg-[var(--color-sand)]/80 backdrop-blur-md z-10">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-[var(--color-sage)]/20 flex items-center justify-center">
            <div className="w-4 h-4 rounded-full bg-[var(--color-sage)] opacity-80" />
          </div>
          <h1 className="text-xl font-medium text-[var(--color-charcoal)]">Shrink AI</h1>
        </div>
        <div className="flex items-center gap-3">
          {/* Mood trend link */}
          <button
            onClick={() => router.push('/mood')}
            className="p-2 text-[var(--color-slate)] hover:text-[var(--color-sage)] transition-colors rounded-full hover:bg-black/5"
            title="Mood trend"
          >
            <TrendingUp size={18} />
          </button>
          {/* Go back to session picker if there were past sessions */}
          {pastSessions.length > 0 && (
            <button
              onClick={() => setView('picker')}
              className="text-xs text-[var(--color-slate)] hover:text-[var(--color-charcoal)] transition-colors px-3 py-1.5 rounded-full hover:bg-black/5"
            >
              Past sessions
            </button>
          )}
          <button
            onClick={logout}
            className="p-2 text-[var(--color-slate)] hover:text-[var(--color-charcoal)] transition-colors rounded-full hover:bg-black/5"
            title="Sign Out"
          >
            <LogOut size={20} />
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-4 sm:px-6 py-8">
        <div className="max-w-3xl mx-auto flex flex-col">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} content={msg.content} role={msg.role} />
          ))}

          {/* Crisis helpline banner — appears inline after the AI crisis response */}
          {showCrisis && <CrisisBanner />}

          {isLoading && (
            <div className="flex justify-start mb-6 animate-fade-in-up">
              <div className="bg-[var(--color-sage-light)] rounded-3xl rounded-tl-sm px-6 py-5 shadow-sm">
                <TypingPulse />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} className="h-4" />
        </div>
      </main>

      <footer className="p-4 sm:p-6 pb-6 sm:pb-8 bg-gradient-to-t from-[var(--color-sand)] via-[var(--color-sand)] to-transparent pt-12 z-10 mt-auto">
        <ChatInput
          value={inputValue}
          onChange={setInputValue}
          onSend={handleSendMessage}
          isLoading={isLoading}
        />
      </footer>
    </div>
  );
}
