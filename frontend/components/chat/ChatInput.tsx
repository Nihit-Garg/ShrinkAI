import React, { useRef, useEffect } from 'react';
import { SendHorizontal } from 'lucide-react';

interface ChatInputProps {
  value: string;
  onChange: (val: string) => void;
  onSend: () => void;
  isLoading: boolean;
}

export function ChatInput({ value, onChange, onSend, isLoading }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !isLoading) {
        onSend();
      }
    }
  };

  return (
    <div className="relative w-full max-w-4xl mx-auto">
      <div className="glass-input rounded-[2rem] p-2 flex items-end shadow-sm">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Share what's on your mind..."
          className="w-full bg-transparent border-none focus:ring-0 resize-none py-3 px-5 text-[var(--color-charcoal)] placeholder-[var(--color-slate)] max-h-[120px] focus:outline-none"
          rows={1}
          disabled={isLoading}
        />
        <button
          onClick={onSend}
          disabled={!value.trim() || isLoading}
          className="p-3 m-1 rounded-full bg-[var(--color-sage)] text-white hover:bg-[#72887c] transition-colors disabled:opacity-50 disabled:hover:bg-[var(--color-sage)] flex-shrink-0"
        >
          <SendHorizontal size={20} />
        </button>
      </div>
    </div>
  );
}
