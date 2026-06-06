"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { fetchApi } from '@/lib/api';
import { MoodChart } from '@/components/MoodChart';
import { ProtectedPage } from '@/components/ProtectedPage';
import { ArrowLeft, TrendingUp } from 'lucide-react';

interface MoodEntry {
  score: number;
  recorded_at: string;
  session_id: string;
}

export default function MoodPage() {
  return (
    <ProtectedPage>
      <MoodContent />
    </ProtectedPage>
  );
}

function MoodContent() {
  const { user } = useAuth();
  const router = useRouter();
  const [entries, setEntries] = useState<MoodEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchApi('/mood/trend')
      .then((data) => setEntries(data.entries ?? []))
      .catch(() => setEntries([]))
      .finally(() => setIsLoading(false));
  }, []);

  // Derive a human-readable overall trend
  const trendSummary = (() => {
    if (entries.length < 2) return null;
    const recent = entries.slice(-3).map((e) => e.score);
    const older = entries.slice(0, -3).map((e) => e.score);
    if (older.length === 0) return null;
    const avgRecent = recent.reduce((a, b) => a + b, 0) / recent.length;
    const avgOlder = older.reduce((a, b) => a + b, 0) / older.length;
    const delta = avgRecent - avgOlder;
    if (delta > 0.15) return { text: 'Your mood has been trending upward lately. That matters.', positive: true };
    if (delta < -0.15) return { text: 'Things have felt heavier recently. Be gentle with yourself.', positive: false };
    return { text: 'Your emotional tone has been steady across recent sessions.', positive: null };
  })();

  return (
    <div className="min-h-screen bg-[var(--color-sand)]">
      {/* Header */}
      <header className="flex items-center gap-4 px-6 py-4 border-b border-[var(--color-sage)]/10 bg-[var(--color-sand)]/80 backdrop-blur-md sticky top-0 z-10">
        <button
          onClick={() => router.push('/chat')}
          className="p-2 text-[var(--color-slate)] hover:text-[var(--color-charcoal)] transition-colors rounded-full hover:bg-black/5"
          title="Back to chat"
        >
          <ArrowLeft size={20} />
        </button>
        <div className="flex items-center gap-2">
          <TrendingUp size={18} className="text-[var(--color-sage)]" />
          <h1 className="text-lg font-medium text-[var(--color-charcoal)]">Mood over time</h1>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-10">
        {/* Intro */}
        <div className="mb-8">
          <p className="text-sm text-[var(--color-slate)] leading-relaxed">
            After each conversation, Shrink AI rates the emotional tone of your session
            on a scale from <span className="font-medium text-[var(--color-charcoal)]">−1</span> (very distressed) to{' '}
            <span className="font-medium text-[var(--color-charcoal)]">+1</span> (hopeful/positive).
            This chart shows how that score has changed over time.
          </p>
        </div>

        {/* Trend summary callout */}
        {!isLoading && trendSummary && (
          <div
            className={`rounded-2xl px-5 py-4 mb-8 text-sm font-medium leading-relaxed ${
              trendSummary.positive === true
                ? 'bg-[var(--color-sage)]/10 text-[var(--color-charcoal)] border border-[var(--color-sage)]/20'
                : trendSummary.positive === false
                ? 'bg-amber-50 text-amber-900 border border-amber-100'
                : 'bg-white/50 text-[var(--color-charcoal)] border border-[var(--color-sage)]/10'
            }`}
          >
            {trendSummary.text}
          </div>
        )}

        {/* Chart card */}
        <div className="bg-white/50 rounded-3xl border border-[var(--color-sage)]/10 shadow-sm px-6 py-8">
          {isLoading ? (
            <div className="flex justify-center items-center h-40">
              <div className="w-6 h-6 rounded-full bg-[var(--color-sage)]/30 animate-[breathe_2s_ease-in-out_infinite]" />
            </div>
          ) : (
            <MoodChart data={entries} />
          )}
        </div>

        {/* Context note */}
        {!isLoading && entries.length > 0 && (
          <p className="text-xs text-[var(--color-slate)]/60 text-center mt-6 leading-relaxed">
            Scores are generated automatically after each session using AI analysis.
            They reflect the emotional tone of the conversation, not a clinical assessment.
          </p>
        )}
      </main>
    </div>
  );
}
