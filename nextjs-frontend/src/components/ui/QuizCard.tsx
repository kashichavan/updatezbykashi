'use client';

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { submitQuizAnswer } from '@/lib/api';
import { CheckCircle2, XCircle, HelpCircle, Loader2 } from 'lucide-react';

interface QuizCardProps {
  chapterSlug: string;
  quizIndex: number;
  code: string;
  options: string[];
  /** Correct answer string — used as local fallback if API is unreachable */
  answer: string;
  explanation: string;
}

const itemVariants = {
  hidden:  { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 320, damping: 26 } },
};

export function QuizCard({ chapterSlug, quizIndex, code, options, answer, explanation }: QuizCardProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<{ is_correct: boolean; explanation: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSelect = useCallback(
    async (opt: string) => {
      if (loading || result !== null) return;
      setSelected(opt);
      setLoading(true);
      try {
        const res = await submitQuizAnswer(chapterSlug, quizIndex, opt);
        setResult(res);
      } catch {
        /* API unreachable — fall back to local answer field */
        setResult({
          is_correct: opt === answer,
          explanation,
        });
      } finally {
        setLoading(false);
      }
    },
    [loading, result, chapterSlug, quizIndex, answer, explanation],
  );

  const handleReset = useCallback(() => {
    setSelected(null);
    setResult(null);
    setLoading(false);
  }, []);

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={itemVariants}
      className="craft-card p-6 space-y-5"
    >
      {/* Quiz label */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-bold text-white">
          <HelpCircle className="w-4 h-4 text-sky-400 animate-pulse" aria-hidden="true" />
          <span>Predict The Output</span>
        </div>
        {result && (
          <button
            onClick={handleReset}
            className="text-[10px] text-slate-500 hover:text-slate-300 underline underline-offset-2 transition-colors"
          >
            Try again
          </button>
        )}
      </div>

      {/* Code snippet */}
      <pre
        className="bg-[var(--surface-card-deep)] border border-slate-800/70 p-4 rounded-lg font-mono text-xs text-slate-200 overflow-x-auto shadow-inner"
        style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.04)' }}
      >
        <code>{code}</code>
      </pre>

      {/* Options */}
      <div className="space-y-2.5" role="radiogroup" aria-label="Select the correct output">
        {options.map((opt) => {
          const isChosen   = selected === opt;
          const isCorrect  = result?.is_correct;
          const isDisabled = loading || result !== null;

          let btnClass =
            'w-full text-left p-3 rounded-xl border text-xs font-mono transition-all duration-200 flex items-center justify-between active-press ';

          if (isChosen && result) {
            btnClass += isCorrect
              ? 'bg-emerald-950/40 border-emerald-500/70 text-emerald-200 shadow-lg shadow-emerald-500/10'
              : 'bg-rose-950/40 border-rose-500/70 text-rose-200 shadow-lg shadow-rose-500/10';
          } else if (isDisabled) {
            btnClass += 'bg-[var(--surface-input)] border-slate-800/70 text-slate-500 cursor-not-allowed';
          } else {
            btnClass +=
              'bg-[var(--surface-input)] border-slate-800/70 text-slate-300 hover:border-sky-500/50 hover:bg-slate-800 hover:text-white cursor-pointer';
          }

          if (loading && isChosen) btnClass += ' animate-pulse opacity-75';

          return (
            <motion.button
              key={opt}
              variants={itemVariants}
              disabled={isDisabled}
              onClick={() => handleSelect(opt)}
              className={btnClass}
              role="radio"
              aria-checked={isChosen}
              aria-disabled={isDisabled}
            >
              <span>{opt}</span>
              {isChosen && result && (
                isCorrect
                  ? <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" aria-label="Correct" />
                  : <XCircle className="w-4 h-4 text-rose-400 shrink-0" aria-label="Incorrect" />
              )}
              {loading && isChosen && (
                <Loader2 className="w-4 h-4 animate-spin text-sky-400 shrink-0" aria-label="Checking…" />
              )}
            </motion.button>
          );
        })}
      </div>

      {/* Result explanation */}
      <AnimatePresence>
        {result && (
          <motion.div
            key="result"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            className={`p-4 rounded-xl text-xs leading-relaxed border ${
              result.is_correct
                ? 'bg-emerald-950/30 text-emerald-300 border-emerald-500/25'
                : 'bg-rose-950/30 text-rose-300 border-rose-500/25'
            }`}
          >
            <strong>{result.is_correct ? '🎉 Correct!' : '❌ Incorrect!'}</strong>{' '}
            {result.explanation}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
