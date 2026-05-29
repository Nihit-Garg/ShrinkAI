"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

/**
 * Wraps any page that requires authentication.
 * - Shows a neutral loading spinner while auth state is being resolved
 * - Redirects to /auth if no token found after resolution
 * - Only renders children once the user is confirmed authenticated
 *
 * This prevents the page content from flashing before the redirect fires.
 */
export function ProtectedPage({ children }: { children: React.ReactNode }) {
  const { token, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !token) {
      router.replace('/auth');
    }
  }, [token, isLoading, router]);

  // While checking auth — show nothing (no flash of protected content)
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[var(--color-sand)]">
        <div className="w-8 h-8 rounded-full bg-[var(--color-sage)]/30 animate-[breathe_2s_ease-in-out_infinite]" />
      </div>
    );
  }

  // Not authenticated — render nothing while redirect fires
  if (!token) {
    return null;
  }

  return <>{children}</>;
}
