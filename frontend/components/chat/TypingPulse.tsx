import React from 'react';

export function TypingPulse() {
  return (
    <div className="flex items-center space-x-2 h-6 px-2">
      <div className="w-2.5 h-2.5 bg-[var(--color-sage)] rounded-full animate-breathe" style={{ animationDelay: '0s' }}></div>
      <div className="w-2.5 h-2.5 bg-[var(--color-sage)] rounded-full animate-breathe" style={{ animationDelay: '0.4s' }}></div>
      <div className="w-2.5 h-2.5 bg-[var(--color-sage)] rounded-full animate-breathe" style={{ animationDelay: '0.8s' }}></div>
    </div>
  );
}
