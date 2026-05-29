import React from 'react';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
}

export function GlassCard({ children, className = '' }: GlassCardProps) {
  return (
    <div className={`glass rounded-3xl p-8 sm:p-10 ${className}`}>
      {children}
    </div>
  );
}
