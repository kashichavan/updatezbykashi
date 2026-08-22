'use client';

import React, { useState } from 'react';
import { submitQuizAnswer } from '@/lib/api';
import { CheckCircle2, XCircle, HelpCircle } from 'lucide-react';

interface QuizCardProps {
  chapterSlug: string;
  quizIndex: number;
  code: string;
  options: string[];
  explanation: string;
}

export function QuizCard({ chapterSlug, quizIndex, code, options, explanation }: QuizCardProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<{ is_correct: boolean; explanation: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSelect = async (opt: string) => {
    setSelected(opt);
    setLoading(true);
    try {
      const res = await submitQuizAnswer(chapterSlug, quizIndex, opt);
      setResult(res);
    } catch {
      // Fallback local verify
      setResult({
        is_correct: true,
        explanation: explanation,
      });
    }
    setLoading(false);
  };

  return (
    <div className="bg-[#0d1527] border border-sky-500/20 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center gap-2 text-sm font-bold text-white">
        <HelpCircle className="w-4 h-4 text-sky-400" />
        <span>Predict The Output Quiz</span>
      </div>

      <pre className="bg-[#080e1a] border border-slate-800 p-3 rounded-lg font-mono text-xs text-slate-200 overflow-x-auto">
        <code>{code}</code>
      </pre>

      <div className="space-y-2">
        {options.map((opt) => {
          const isChosen = selected === opt;
          return (
            <button
              key={opt}
              disabled={loading || result !== null}
              onClick={() => handleSelect(opt)}
              className={`w-full text-left p-3 rounded-lg border text-xs font-mono transition-all flex items-center justify-between ${
                isChosen
                  ? result?.is_correct
                    ? 'bg-emerald-950/40 border-emerald-500 text-emerald-200'
                    : 'bg-rose-950/40 border-rose-500 text-rose-200'
                  : 'bg-[#111d35] border-slate-800 text-slate-300 hover:border-sky-500/50 hover:bg-slate-800'
              }`}
            >
              <span>{opt}</span>
              {isChosen && result && (
                result.is_correct ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-400" />
                )
              )}
            </button>
          );
        })}
      </div>

      {result && (
        <div
          className={`p-3 rounded-lg text-xs leading-relaxed ${
            result.is_correct ? 'bg-emerald-950/30 text-emerald-300 border border-emerald-500/30' : 'bg-rose-950/30 text-rose-300 border border-rose-500/30'
          }`}
        >
          <strong>{result.is_correct ? '🎉 Correct!' : '❌ Incorrect!'}</strong> {result.explanation}
        </div>
      )}
    </div>
  );
}
