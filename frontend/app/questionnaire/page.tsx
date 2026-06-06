"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { QuestionStep } from '@/components/questionnaire/QuestionStep';
import { fetchApi } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { ProtectedPage } from '@/components/ProtectedPage';
import { ArrowRight, Plus, Sparkles } from 'lucide-react';

const MIN_QUESTIONS = 5; // Show early-exit option after this many questions

interface QuestionDef {
  id: string;
  text: string;
}

export default function QuestionnairePage() {
  return (
    <ProtectedPage>
      <QuestionnaireContent />
    </ProtectedPage>
  );
}

function QuestionnaireContent() {
  const [framingStatement, setFramingStatement] = useState('');
  const [questions, setQuestions] = useState<QuestionDef[]>([]);

  const [showFraming, setShowFraming] = useState(true);
  const [showEarlyExit, setShowEarlyExit] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);

  const [answers, setAnswers] = useState<Record<string, string | null>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    const loadQuestions = async () => {
      try {
        const data = await fetchApi('/questionnaire/questions');
        setFramingStatement(data.framing_statement);
        setQuestions(data.questions);

        // Restore partial progress from localStorage
        const savedAnswers = localStorage.getItem('shrink_answers');
        if (savedAnswers) {
          try {
            const parsed = JSON.parse(savedAnswers);
            setAnswers(parsed);

            // Find first unanswered question
            let firstUnanswered = 0;
            for (let i = 0; i < data.questions.length; i++) {
              if (parsed[data.questions[i].id] === undefined) {
                firstUnanswered = i;
                break;
              }
            }
            if (firstUnanswered > 0) {
              setCurrentIndex(firstUnanswered);
              setShowFraming(false);
            }
          } catch {
            console.error('Failed to parse saved answers');
          }
        }
      } catch (err: any) {
        console.error('[Questionnaire] Failed to load questions:', err);
        const msg = err?.message || '';
        if (msg.includes('fetch') || msg.includes('network') || msg.includes('Failed to fetch')) {
          setError('Cannot reach the server. Make sure the backend is running, then refresh.');
        } else {
          setError(`Failed to load questionnaire: ${msg || 'Unknown error'}. Please try refreshing.`);
        }
      } finally {
        setIsLoading(false);
      }
    };
    loadQuestions();
  }, []);

  const saveToLocal = (newAnswers: Record<string, string | null>) => {
    localStorage.setItem('shrink_answers', JSON.stringify(newAnswers));
  };

  const handleAnswerChange = (value: string) => {
    const qId = questions[currentIndex].id;
    setAnswers((prev) => ({ ...prev, [qId]: value }));
  };

  /** Advance after answering — show early exit after MIN_QUESTIONS, or submit at end */
  const advanceOrExit = async (updatedAnswers: Record<string, string | null>, nextIndex: number) => {
    const justCompletedMinimum = nextIndex === MIN_QUESTIONS;
    const isLastQuestion = nextIndex >= questions.length;

    if (isLastQuestion) {
      await submitQuestionnaire(updatedAnswers);
    } else if (justCompletedMinimum) {
      setShowEarlyExit(true);
    } else {
      setCurrentIndex(nextIndex);
    }
  };

  const handleNext = async () => {
    const qId = questions[currentIndex].id;
    const updatedAnswers = { ...answers, [qId]: answers[qId] || '' };
    setAnswers(updatedAnswers);
    saveToLocal(updatedAnswers);
    await advanceOrExit(updatedAnswers, currentIndex + 1);
  };

  const handleSkip = async () => {
    const qId = questions[currentIndex].id;
    const updatedAnswers = { ...answers, [qId]: null };
    setAnswers(updatedAnswers);
    saveToLocal(updatedAnswers);
    await advanceOrExit(updatedAnswers, currentIndex + 1);
  };

  const handleBack = () => {
    if (showEarlyExit) {
      setShowEarlyExit(false);
      setCurrentIndex(MIN_QUESTIONS - 1);
    } else if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const submitQuestionnaire = async (finalAnswers: Record<string, string | null>) => {
    setIsSubmitting(true);
    setError('');

    const payloadAnswers: Record<string, string | null> = {};
    for (const q of questions) {
      if (finalAnswers[q.id] !== undefined) {
        payloadAnswers[q.id] = finalAnswers[q.id];
      }
    }

    try {
      await fetchApi('/questionnaire/submit', {
        method: 'POST',
        body: JSON.stringify({ answers: payloadAnswers }),
      });
      localStorage.removeItem('shrink_answers');
      router.push('/chat');
    } catch (err: any) {
      setError(err.message || 'Failed to save questionnaire. Please try again.');
      setIsSubmitting(false);
    }
  };

  // ── Loading ──────────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="animate-pulse w-8 h-8 rounded-full bg-[var(--color-sage)]/40" />
      </div>
    );
  }

  if (error && questions.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  // ── Framing screen ───────────────────────────────────────────────────────────
  if (showFraming) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 bg-[var(--color-sand)]">
        <div className="max-w-2xl text-center animate-fade-in-up">
          <p className="text-2xl md:text-3xl text-[var(--color-charcoal)] leading-relaxed mb-12 font-serif italic opacity-90">
            &ldquo;{framingStatement}&rdquo;
          </p>
          <Button onClick={() => setShowFraming(false)} className="px-10 py-4 text-lg">
            I&apos;m ready
          </Button>
        </div>
      </div>
    );
  }

  // ── Early exit screen (after MIN_QUESTIONS answered) ────────────────────────
  if (showEarlyExit) {
    const answeredCount = Object.values(answers).filter((v) => v !== undefined).length;
    const remainingCount = questions.length - MIN_QUESTIONS;

    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 bg-[var(--color-sand)]">
        <div className="max-w-lg w-full text-center animate-fade-in-up">
          {/* Icon */}
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-[var(--color-sage)]/15 flex items-center justify-center">
            <Sparkles size={28} className="text-[var(--color-sage)]" />
          </div>

          <h2 className="text-2xl font-serif text-[var(--color-charcoal)] mb-3">
            You&apos;re ready to begin.
          </h2>
          <p className="text-[var(--color-slate)] text-base leading-relaxed mb-2">
            Shrink has a meaningful picture of you already.
          </p>

          {/* Nudge */}
          <div className="mt-4 mb-8 px-5 py-4 rounded-2xl bg-[var(--color-sage)]/8 border border-[var(--color-sage)]/20">
            <p className="text-sm text-[var(--color-charcoal)] leading-relaxed">
              💡 The more you share, the more personal every conversation becomes.{' '}
              <span className="font-medium">{remainingCount} more questions</span> would help Shrink
              understand you even better — your patterns, your relationships, what really matters to you.
            </p>
          </div>

          {/* Primary: go to chat */}
          <button
            onClick={() => submitQuestionnaire(answers)}
            disabled={isSubmitting}
            className="w-full flex items-center justify-center gap-2 py-4 px-6 rounded-2xl bg-[var(--color-sage)] text-white font-medium text-base hover:opacity-90 active:scale-[0.98] transition-all duration-150 mb-3 shadow-sm disabled:opacity-60"
          >
            {isSubmitting ? 'Starting…' : 'Start chatting now'}
            {!isSubmitting && <ArrowRight size={18} />}
          </button>

          {/* Secondary: answer more */}
          <button
            onClick={() => {
              setShowEarlyExit(false);
              setCurrentIndex(MIN_QUESTIONS);
            }}
            className="w-full flex items-center justify-center gap-2 py-3.5 px-6 rounded-2xl border border-[var(--color-sage)]/25 text-[var(--color-charcoal)] text-sm font-medium hover:bg-[var(--color-sage)]/5 hover:border-[var(--color-sage)]/40 transition-all duration-150"
          >
            <Plus size={15} />
            Answer {remainingCount} more questions first
          </button>

          {/* Back link */}
          <button
            onClick={handleBack}
            className="mt-5 text-xs text-[var(--color-slate)] hover:text-[var(--color-charcoal)] transition-colors"
          >
            ← Back to previous question
          </button>

          {error && (
            <p className="mt-4 text-sm text-red-500">{error}</p>
          )}
        </div>
      </div>
    );
  }

  // ── Question screen ──────────────────────────────────────────────────────────
  const totalShown = currentIndex < MIN_QUESTIONS ? MIN_QUESTIONS : questions.length;
  const progress = (currentIndex / totalShown) * 100;
  const currentQuestion = questions[currentIndex];
  const isExtendedMode = currentIndex >= MIN_QUESTIONS;

  return (
    <div className="flex-1 flex flex-col pt-12 px-6 bg-[var(--color-sand)] min-h-screen">
      <div className="max-w-3xl w-full mx-auto mb-16">
        <div className="h-1 w-full bg-[var(--color-sage-light)] rounded-full overflow-hidden">
          <div
            className="h-full bg-[var(--color-sage)] transition-all duration-700 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-xs text-[var(--color-slate)] mt-3 text-right">
          {isExtendedMode
            ? `Question ${currentIndex + 1} of ${questions.length}`
            : `Step ${currentIndex + 1} of ${MIN_QUESTIONS}`}
        </p>
      </div>

      <div className="flex-1 flex flex-col justify-center pb-32">
        {error && (
          <div className="max-w-2xl mx-auto mb-6 p-4 bg-red-50 text-red-600 rounded-xl text-center">
            {error}
          </div>
        )}

        {currentQuestion && (
          <QuestionStep
            key={currentQuestion.id}
            question={currentQuestion.text}
            value={answers[currentQuestion.id] || ''}
            onChange={handleAnswerChange}
            onNext={handleNext}
            onSkip={handleSkip}
            onBack={currentIndex > 0 ? handleBack : undefined}
            isLast={currentIndex === questions.length - 1}
            isLoading={isSubmitting}
          />
        )}
      </div>
    </div>
  );
}
