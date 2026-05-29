import React, { forwardRef } from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', ...props }, ref) => {
    return (
      <div className="flex flex-col space-y-2 w-full">
        {label && (
          <label className="text-sm font-medium text-[var(--color-slate)] ml-2">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`
            w-full px-5 py-4 rounded-2xl bg-white/60 
            border border-gray-200 shadow-sm
            text-[var(--color-charcoal)] placeholder-[var(--color-slate)]
            focus:outline-none focus:ring-2 focus:ring-[var(--color-sage)]/30 focus:border-[var(--color-sage)]/50
            transition-all duration-300 ease-in-out
            disabled:opacity-50 disabled:bg-gray-100
            ${error ? 'border-red-300 focus:ring-red-200 focus:border-red-400' : ''}
            ${className}
          `}
          {...props}
        />
        {error && (
          <span className="text-xs text-red-500 ml-2 mt-1">{error}</span>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
