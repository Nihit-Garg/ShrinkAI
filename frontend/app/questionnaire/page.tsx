"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { QuestionStep } from '@/components/questionnaire/QuestionStep';
import { fetchApi } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { ProtectedPage } from '@/components/ProtectedPage';

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
  
  // States for flow
  const [showFraming, setShowFraming] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  
  // Store answers as question_id -> string (or null if skipped)
  const [answers, setAnswers] = useState<Record<string, string | null>>({});
  
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    // Load questions from backend
    const loadQuestions = async () => {
      try {
        const data = await fetchApi('/questionnaire/questions');
        setFramingStatement(data.framing_statement);
        setQuestions(data.questions);
        
        // Restore partial progress from localStorage if it exists
        const savedAnswers = localStorage.getItem('shrink_answers');
        if (savedAnswers) {
          try {
            const parsed = JSON.parse(savedAnswers);
            setAnswers(parsed);
            
            // Find first unanswered question to jump to
            let firstUnanswered = 0;
            for (let i = 0; i < data.questions.length; i++) {
              if (parsed[data.questions[i].id] === undefined) {
                firstUnanswered = i;
                break;
              }
            }
            if (firstUnanswered > 0) {
              setCurrentIndex(firstUnanswered);
              setShowFraming(false); // Skip framing if returning
            }
          } catch (e) {
            console.error("Failed to parse saved answers");
          }
        }
      } catch (err) {
        setError('Failed to load questionnaire. Please try refreshing.');
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
    setAnswers(prev => ({
      ...prev,
      [qId]: value
    }));
  };

  const handleNext = async () => {
    const qId = questions[currentIndex].id;
    const currentVal = answers[qId] || '';
    
    // Save locally on every step
    const updatedAnswers = { ...answers, [qId]: currentVal };
    setAnswers(updatedAnswers);
    saveToLocal(updatedAnswers);

    if (currentIndex < questions.length - 1) {
      setCurrentIndex(prev => prev + 1);
    } else {
      await submitQuestionnaire(updatedAnswers);
    }
  };

  const handleSkip = async () => {
    const qId = questions[currentIndex].id;
    
    // Set to null explicitly to mark as skipped
    const updatedAnswers = { ...answers, [qId]: null };
    setAnswers(updatedAnswers);
    saveToLocal(updatedAnswers);

    if (currentIndex < questions.length - 1) {
      setCurrentIndex(prev => prev + 1);
    } else {
      await submitQuestionnaire(updatedAnswers);
    }
  };

  const handleBack = () => {
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
    }
  };

  const submitQuestionnaire = async (finalAnswers: Record<string, string | null>) => {
    setIsSubmitting(true);
    setError('');
    
    // Clean up answers dict (remove anything undefined, keep nulls)
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
      
      // Clear saved progress on success
      localStorage.removeItem('shrink_answers');
      router.push('/chat');
    } catch (err: any) {
      setError(err.message || 'Failed to save questionnaire. Please try again.');
      setIsSubmitting(false);
    }
  };

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

  // Framing statement screen
  if (showFraming) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 bg-[var(--color-sand)]">
        <div className="max-w-2xl text-center animate-fade-in-up">
          <p className="text-2xl md:text-3xl text-[var(--color-charcoal)] leading-relaxed mb-12 font-serif italic opacity-90">
            "{framingStatement}"
          </p>
          <Button onClick={() => setShowFraming(false)} className="px-10 py-4 text-lg">
            I'm ready
          </Button>
        </div>
      </div>
    );
  }

  const progress = ((currentIndex) / questions.length) * 100;
  const currentQuestion = questions[currentIndex];

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
          Step {currentIndex + 1} of {questions.length}
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
            key={currentQuestion.id} // forces re-animation
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
