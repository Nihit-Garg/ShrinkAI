"use client";

import { Clock, ArrowRight, Plus } from 'lucide-react';

interface SessionSummary {
  session_id: string;
  started_at: string;
  last_message_preview: string | null;
  last_message_role: 'user' | 'assistant' | null;
}

interface SessionPickerProps {
  sessions: SessionSummary[];
  userName: string;
  onContinue: (sessionId: string) => void;
  onStartFresh: () => void;
}

function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 2) return 'Just now';
  if (diffMins < 60) return `${diffMins} minutes ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function SessionPicker({ sessions, userName, onContinue, onStartFresh }: SessionPickerProps) {
  const displayName = userName.split('@')[0]; // use part before @ if email

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 bg-[var(--color-sand)] animate-fade-in-up">
      <div className="w-full max-w-lg">

        {/* Greeting */}
        <div className="text-center mb-10">
          <div className="w-14 h-14 mx-auto mb-5 rounded-full bg-[var(--color-sage)]/20 flex items-center justify-center">
            <div className="w-7 h-7 rounded-full bg-[var(--color-sage)] opacity-70" />
          </div>
          <h1 className="text-3xl font-serif text-[var(--color-charcoal)] mb-2">
            Welcome back{displayName ? `, ${displayName}` : ''}.
          </h1>
          <p className="text-[var(--color-slate)] text-base">
            {sessions.length > 0
              ? 'Would you like to pick up where you left off?'
              : 'Ready to continue your journey?'}
          </p>
        </div>

        {/* Past sessions */}
        {sessions.length > 0 && (
          <div className="space-y-3 mb-6">
            {sessions.map((session, i) => (
              <button
                key={session.session_id}
                onClick={() => onContinue(session.session_id)}
                className="w-full text-left p-5 rounded-2xl bg-white/60 hover:bg-white/90 border border-[var(--color-sage)]/15 hover:border-[var(--color-sage)]/30 transition-all duration-200 group shadow-sm hover:shadow-md"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-2">
                      <Clock size={12} className="text-[var(--color-sage)] flex-shrink-0" />
                      <span className="text-xs text-[var(--color-sage)] font-medium">
                        {formatTimeAgo(session.started_at)}
                      </span>
                    </div>
                    <p className="text-sm text-[var(--color-charcoal)] leading-relaxed line-clamp-2 italic opacity-80">
                      {session.last_message_role === 'user' ? '"' : ''}
                      {session.last_message_preview || 'No messages yet'}
                      {session.last_message_role === 'user' ? '"' : ''}
                    </p>
                  </div>
                  <ArrowRight
                    size={18}
                    className="text-[var(--color-sage)]/50 group-hover:text-[var(--color-sage)] group-hover:translate-x-1 transition-all duration-200 flex-shrink-0 mt-1"
                  />
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Start fresh */}
        <button
          onClick={onStartFresh}
          className="w-full flex items-center justify-center gap-2 py-3.5 px-6 rounded-2xl border border-[var(--color-sage)]/20 text-[var(--color-slate)] hover:text-[var(--color-charcoal)] hover:border-[var(--color-sage)]/40 hover:bg-white/40 transition-all duration-200 text-sm font-medium"
        >
          <Plus size={15} />
          Start a new conversation
        </button>
      </div>
    </div>
  );
}
