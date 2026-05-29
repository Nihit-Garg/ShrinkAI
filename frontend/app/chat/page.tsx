"use client";

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { fetchApi } from '@/lib/api';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { ChatInput } from '@/components/chat/ChatInput';
import { TypingPulse } from '@/components/chat/TypingPulse';
import { LogOut } from 'lucide-react';
import { ProtectedPage } from '@/components/ProtectedPage';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

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
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check auth and questionnaire status on mount
  useEffect(() => {
    if (user) {
      checkQuestionnaireStatus().then((completed) => {
        if (!completed) {
          router.push('/questionnaire');
        } else {
          // Add a gentle welcome message if the chat is empty
          setMessages([
            {
              id: 'welcome-msg',
              role: 'assistant',
              content: "Hello. I'm here to offer a safe, confidential space for us to explore your thoughts and feelings. Please, take your time and share whatever is on your mind."
            }
          ]);
        }
      });
    }
  }, [user, router, checkQuestionnaireStatus]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
    
    const userMsgContent = inputValue.trim();
    setInputValue('');
    
    const tempUserMsgId = `temp-${Date.now()}`;
    setMessages(prev => [...prev, { id: tempUserMsgId, role: 'user', content: userMsgContent }]);
    setIsLoading(true);
    
    try {
      const payload: any = { content: userMsgContent };
      if (sessionId) {
        payload.session_id = sessionId;
      }
      
      const response = await fetchApi('/conversation/message', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      
      if (!sessionId) {
        setSessionId(response.session_id);
      }
      
      setMessages(prev => [
        ...prev, 
        { id: response.message_id, role: 'assistant', content: response.content }
      ]);
      
    } catch (error: any) {
      console.error("Failed to send message:", error);
      // Revert optimistic UI on failure
      setMessages(prev => prev.filter(m => m.id !== tempUserMsgId));
      setInputValue(userMsgContent);
      alert("Failed to send message. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen max-h-[100dvh] overflow-hidden bg-[var(--color-sand)]">
      
      {/* Header */}
      <header className="flex justify-between items-center px-6 py-4 border-b border-[var(--color-sage)]/10 bg-[var(--color-sand)]/80 backdrop-blur-md z-10">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-[var(--color-sage)]/20 flex items-center justify-center">
            <div className="w-4 h-4 rounded-full bg-[var(--color-sage)] opacity-80" />
          </div>
          <h1 className="text-xl font-medium text-[var(--color-charcoal)]">Shrink AI</h1>
        </div>
        <button 
          onClick={logout}
          className="p-2 text-[var(--color-slate)] hover:text-[var(--color-charcoal)] transition-colors rounded-full hover:bg-black/5"
          title="Sign Out"
        >
          <LogOut size={20} />
        </button>
      </header>
      
      {/* Messages Area */}
      <main className="flex-1 overflow-y-auto px-4 sm:px-6 py-8">
        <div className="max-w-3xl mx-auto flex flex-col">
          {messages.map((msg) => (
            <MessageBubble 
              key={msg.id}
              content={msg.content}
              role={msg.role}
            />
          ))}
          
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
      
      {/* Input Area */}
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
