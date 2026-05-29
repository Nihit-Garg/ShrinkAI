import React, { useEffect, useRef } from 'react';
import { Button } from '@/components/ui/Button';

interface QuestionStepProps {
  question: string;
  value: string;
  onChange: (val: string) => void;
  onNext: () => void;
  onBack?: () => void;
  onSkip: () => void;
  isLast?: boolean;
  isLoading?: boolean;
}

export function QuestionStep({ 
  question, 
  value, 
  onChange, 
  onNext, 
  onBack,
  onSkip,
  isLast = false,
  isLoading = false 
}: QuestionStepProps) {
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [question]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      if (value.trim()) onNext();
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto flex flex-col animate-fade-in-up">
      <h2 className="text-3xl md:text-4xl text-[var(--color-charcoal)] mb-8 font-medium leading-tight">
        {question}
      </h2>
      
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your answer here..."
        className="w-full min-h-[150px] p-6 rounded-3xl bg-white/70 border border-[var(--color-sage)]/20 shadow-sm text-lg text-[var(--color-charcoal)] placeholder-[var(--color-slate)] focus:outline-none focus:ring-2 focus:ring-[var(--color-sage)]/40 focus:bg-white transition-all resize-none mb-8"
      />
      
      <div className="flex justify-between items-center">
        <div className="flex space-x-2">
          {onBack && (
            <button 
              onClick={onBack}
              className="text-[var(--color-slate)] hover:text-[var(--color-charcoal)] font-medium transition-colors px-4 py-2"
              disabled={isLoading}
            >
              Back
            </button>
          )}
          <button 
            onClick={onSkip}
            className="text-[var(--color-slate)] hover:text-[var(--color-sage)] font-medium transition-colors px-4 py-2"
            disabled={isLoading}
          >
            Skip
          </button>
        </div>
        <Button 
          onClick={onNext} 
          disabled={!value.trim() || isLoading}
          isLoading={isLoading}
        >
          {isLast ? 'Complete Setup' : 'Next'}
        </Button>
      </div>
      <p className="text-xs text-[var(--color-slate)]/70 text-right mt-4">
        Press Cmd + Enter to continue
      </p>
    </div>
  );
}
