"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { GlassCard } from '@/components/ui/GlassCard';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/lib/auth-context';
import { fetchApi } from '@/lib/api';
import { supabase } from '@/lib/supabase';

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const { login, checkQuestionnaireStatus } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setMessage('');

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/signup';
      const data = await fetchApi(endpoint, {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      if (data.access_token) {
        login(data.access_token, { id: data.user_id, email: data.email });
        const completed = await checkQuestionnaireStatus();
        router.push(completed ? '/chat' : '/questionnaire');
      } else if (data.message) {
        setMessage(data.message);
        setIsLogin(true);
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setIsGoogleLoading(true);
    setError('');
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
    if (error) {
      setError('Google sign-in failed. Please try again.');
      setIsGoogleLoading(false);
    }
    // On success, browser redirects to Google — no further action needed here
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md animate-fade-in-up">
        <div className="text-center mb-10">
          <h1 className="text-4xl text-[var(--color-sage)] mb-2">Shrink AI</h1>
          <p className="text-[var(--color-slate)] text-lg">A safe space for your thoughts.</p>
        </div>

        <GlassCard>
          <h2 className="text-2xl mb-6 text-center text-[var(--color-charcoal)]">
            {isLogin ? 'Welcome back' : 'Create your space'}
          </h2>

          {/* Google OAuth Button */}
          <button
            id="google-signin-btn"
            onClick={handleGoogleSignIn}
            disabled={isGoogleLoading || isLoading}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-2xl border border-[var(--color-sage)]/20 bg-white/60 hover:bg-white/90 transition-all duration-200 text-[var(--color-charcoal)] font-medium text-sm shadow-sm mb-5 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGoogleLoading ? (
              <span className="w-5 h-5 border-2 border-[var(--color-sage)]/40 border-t-[var(--color-sage)] rounded-full animate-spin" />
            ) : (
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
            )}
            {isGoogleLoading ? 'Redirecting...' : 'Continue with Google'}
          </button>

          {/* Divider */}
          <div className="flex items-center gap-3 mb-5">
            <div className="flex-1 h-px bg-[var(--color-sage)]/20" />
            <span className="text-xs text-[var(--color-slate)]">or</span>
            <div className="flex-1 h-px bg-[var(--color-sage)]/20" />
          </div>

          {/* Email / Password form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              type="email"
              placeholder="Email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            {error && <p className="text-red-500 text-sm text-center">{error}</p>}
            {message && <p className="text-[var(--color-sage)] text-sm text-center">{message}</p>}

            <Button type="submit" className="w-full mt-4" isLoading={isLoading}>
              {isLogin ? 'Sign In' : 'Sign Up'}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-[var(--color-slate)]">
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
                setMessage('');
              }}
              className="text-[var(--color-sage)] font-medium hover:underline focus:outline-none"
            >
              {isLogin ? 'Sign Up' : 'Sign In'}
            </button>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
