"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

export default function Home() {
  const router = useRouter();
  const { user, isLoading, checkQuestionnaireStatus } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      if (user) {
        checkQuestionnaireStatus().then((completed) => {
          if (completed) {
            router.push('/chat');
          } else {
            router.push('/questionnaire');
          }
        });
      } else {
        router.push('/auth');
      }
    }
  }, [user, isLoading, router, checkQuestionnaireStatus]);

  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="animate-pulse">
        <div className="w-12 h-12 bg-[var(--color-sage)]/20 rounded-full flex items-center justify-center">
          <div className="w-8 h-8 bg-[var(--color-sage)]/40 rounded-full flex items-center justify-center">
            <div className="w-4 h-4 bg-[var(--color-sage)] rounded-full"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
