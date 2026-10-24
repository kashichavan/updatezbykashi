'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { submitQuizAnswer } from '@/lib/api';
import { CheckCircle2, XCircle, HelpCircle, Loader2 } from 'lucide-react';

interface QuizCardProps {
  chapterSlug: string;
  quizIndex: number;
  code: string;
  options: string[];
  explanation: string;
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 300, damping: 24 } },
};

export function QuizCard({ chapterSlug, quizIndex, code, options, explanation }: QuizCardProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<{ is_correct: boolean; explanation: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSelect = async (opt: string) => {
    if (loading || result !== null) return;
    setSelected(opt);
    setLoading(true);
    try {
      const res = await submitQuizAnswer(chapterSlug, quizIndex, opt);
      setResult(res);
    } catch (error) {
      console.error('Error submitting quiz:', error);
      // Fallback local verify (assuming the first option is correct for demo purposes)
      setResult({
        is_correct: opt === options[0], // Simplified for local fallback
        explanation: explanation,
      });
    }
    setLoading(false);
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={itemVariants}
      className="bg-surface-card border border-sky-500/20 rounded-xl p-6 shadow-lg space-y-5 glass-card-hover"
    >
      <div className="flex items-center gap-2 text-sm font-bold text-white mb-4">
        <HelpCircle className="w-4 h-4 text-sky-400 animate-pulse" />
        <span>Predict The Output Quiz</span>
      </div>

      <pre className="bg-[#080e1a] border border-slate-800 p-4 rounded-lg font-mono text-xs text-slate-200 overflow-x-auto shadow-inner">
        <code>{code}</code>
      </pre>

      <div className="space-y-3">
        {options.map((opt) => {
          const isChosen = selected === opt;
          const isCorrect = result?.is_correct;
          const isDisabled = loading || result !== null;

          const buttonClasses = `w-full text-left p-3 rounded-lg border text-xs font-mono transition-all duration-200 flex items-center justify-between
            ${isChosen
              ? isCorrect
                ? 'bg-emerald-950/40 border-emerald-500 text-emerald-200 shadow-lg shadow-emerald-500/10'
                : 'bg-rose-950/40 border-rose-500 text-rose-200 shadow-lg shadow-rose-500/10'
              : isDisabled
              ? 'bg-[#111d35] border-slate-800 text-slate-500 cursor-not-allowed'
              : 'bg-[#111d35] border-slate-800 text-slate-300 hover:border-sky-500/50 hover:bg-slate-800 hover:text-white'
            }
            ${loading && isChosen ? 'animate-pulse opacity-75' : ''}
          `;

          return (
            <motion.button
              key={opt}
              variants={itemVariants}
              disabled={isDisabled}
              onClick={() => handleSelect(opt)}
              className={buttonClasses}
              aria-checked={isChosen}
              role="radio"
            >
              <span>{opt}</span>
              {isChosen && result && (
                isCorrect ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                )
              )}
              {loading && isChosen && <Loader2 className="w-4 h-4 animate-spin text-sky-400 flex-shrink-0" />}
            </motion.button>
          );
        })}
      </div>

      {result && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className={`p-4 rounded-lg text-xs leading-relaxed transition-all duration-300 shadow-inner ${
            result.is_correct ? 'bg-emerald-950/30 text-emerald-300 border border-emerald-500/30' : 'bg-rose-950/30 text-rose-300 border border-rose-500/30'
          }`}
        >
          <strong>{result.is_correct ? '🎉 Correct!' : '❌ Incorrect!'}</strong> {result.explanation}
        </motion.div>
      )}
    </motion.div>
  );
}
