import React from 'react';

interface MessageBubbleProps {
  content: string;
  role: 'user' | 'assistant';
  isTyping?: boolean;
}

export function MessageBubble({ content, role, isTyping }: MessageBubbleProps) {
  const isAssistant = role === 'assistant';
  
  return (
    <div className={`flex w-full ${isAssistant ? 'justify-start' : 'justify-end'} mb-6 animate-fade-in-up`}>
      <div 
        className={`
          max-w-[85%] sm:max-w-[75%] px-6 py-4 rounded-3xl text-[17px] leading-relaxed shadow-sm
          ${isAssistant 
            ? 'bg-[var(--color-sage-light)] text-[var(--color-charcoal)] rounded-tl-sm' 
            : 'bg-[var(--color-user-bubble)] text-[var(--color-charcoal)] rounded-tr-sm'
          }
        `}
      >
        {isTyping ? content : content.split('\n').map((line, i) => (
          <React.Fragment key={i}>
            {line}
            {i !== content.split('\n').length - 1 && <br />}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}
