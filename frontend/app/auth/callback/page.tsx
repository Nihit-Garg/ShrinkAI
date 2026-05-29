"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { useAuth } from '@/lib/auth-context';

export default function AuthCallbackPage() {
  const router = useRouter();
  const { login, checkQuestionnaireStatus } = useAuth();
  const [status, setStatus] = useState('Signing you in...');

  useEffect(() => {
    let handled = false;

    const finishLogin = async (accessToken: string, userId: string, email: string) => {
      if (handled) return;
      handled = true;
      setStatus('Almost there...');
      login(accessToken, { id: userId, email });
      const completed = await checkQuestionnaireStatus();
      router.replace(completed ? '/chat' : '/questionnaire');
    };

    const handleCallback = async () => {
      // ── Strategy 1: Hash fragment (implicit flow) ──────────────────────────
      // Supabase redirects with #access_token=xxx&... in the URL hash
      const hash = window.location.hash;
      if (hash && hash.includes('access_token=')) {
        const params = new URLSearchParams(hash.substring(1)); // strip leading #
        const accessToken = params.get('access_token');
        const userId = params.get('user_id') ?? '';
        // Get user info from Supabase since hash may not include it
        if (accessToken) {
          console.log('[OAuth] Token found in hash — fetching user...');
          setStatus('Verifying...');
          // Set the session so supabase client knows about it
          const { data } = await supabase.auth.getUser(accessToken);
          if (data.user) {
            await finishLogin(accessToken, data.user.id, data.user.email ?? '');
            return;
          }
        }
      }

      // ── Strategy 2: PKCE code in query params ──────────────────────────────
      const params = new URLSearchParams(window.location.search);
      const code = params.get('code');
      if (code) {
        console.log('[OAuth] Code found in query — exchanging...');
        setStatus('Exchanging auth code...');
        const { data, error } = await supabase.auth.exchangeCodeForSession(code);
        if (data?.session) {
          await finishLogin(
            data.session.access_token,
            data.session.user.id,
            data.session.user.email ?? '',
          );
          return;
        }
        if (error) console.error('[OAuth] Code exchange failed:', error.message);
      }

      // ── Strategy 3: Existing session already in Supabase client ───────────
      console.log('[OAuth] No hash/code — checking for existing session...');
      const { data: { session } } = await supabase.auth.getSession();
      if (session) {
        await finishLogin(session.access_token, session.user.id, session.user.email ?? '');
        return;
      }

      // ── Strategy 4: onAuthStateChange — wait for Supabase to process URL ──
      console.log('[OAuth] Waiting for onAuthStateChange...');
      const { data: { subscription } } = supabase.auth.onAuthStateChange(
        async (event, session) => {
          console.log('[OAuth] event:', event);
          if (event === 'SIGNED_IN' && session && !handled) {
            subscription.unsubscribe();
            await finishLogin(session.access_token, session.user.id, session.user.email ?? '');
          }
        }
      );

      // Give up after 8 seconds
      setTimeout(() => {
        if (!handled) {
          subscription.unsubscribe();
          console.error('[OAuth] All strategies failed.');
          setStatus('Something went wrong. Redirecting...');
          setTimeout(() => router.replace('/auth'), 1200);
        }
      }, 8000);
    };

    handleCallback();
  }, []);

  return (
    <div className="flex-1 flex items-center justify-center bg-[var(--color-sand)]">
      <div className="text-center animate-fade-in-up">
        <div className="w-10 h-10 mx-auto mb-4 rounded-full bg-[var(--color-sage)]/30 animate-[breathe_2s_ease-in-out_infinite]" />
        <p className="text-[var(--color-slate)] text-lg">{status}</p>
      </div>
    </div>
  );
}
