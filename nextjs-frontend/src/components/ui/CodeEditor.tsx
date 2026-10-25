'use client';

import React, { useState, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import { executeJavaScriptCode } from '@/lib/api';
import type { CodeTraceStep } from '@/lib/types';
import { Play, SkipForward, SkipBack, RefreshCw, Sparkles, Terminal, AlertCircle } from 'lucide-react';

interface CodeEditorProps {
  initialCode: string;
  topicTitle?: string;
  language?: string; // Added language prop
}

export function CodeEditor({ initialCode, topicTitle, language = 'javascript' }: CodeEditorProps) {
  const [code, setCode] = useState(initialCode);
  const [isExecuting, setIsExecuting] = useState(false);
  const [steps, setSteps] = useState<CodeTraceStep[]>([]);
  const [currentStepIdx, setCurrentStepIdx] = useState(0);
  const [stdout, setStdout] = useState('');
  const [execTime, setExecTime] = useState<number | null>(null);
  const [execError, setExecError] = useState<string | null>(null);

  const handleRun = useCallback(async () => {
    if (isExecuting) return;
    setIsExecuting(true);
    setExecError(null);
    setSteps([]);
    setStdout('');
    setExecTime(null);

    try {
      // NOTE: This currently only executes JavaScript. For other languages, a separate backend endpoint is needed.
      if (language !== 'javascript') {
        setExecError(`Execution for ${language} is not supported by the current backend API.`);
        return;
      }
      const res = await executeJavaScriptCode(code);
      if (res.success) {
        setSteps(res.steps);
        setCurrentStepIdx(0);
        setStdout(res.output);
        setExecTime(res.execution_time_ms);
      } else {
        setExecError(res.error || 'Execution failed — check your code and try again.');
        setStdout(res.output || '');
      }
    } catch (err: unknown) {
      setExecError(err instanceof Error ? err.message : 'Network error — is the API server running?');
    } finally {
      setIsExecuting(false);
    }
  }, [code, isExecuting, language]);

  const handleReset = useCallback(() => {
    setCode(initialCode);
    setSteps([]);
    setStdout('');
    setExecTime(null);
    setExecError(null);
    setCurrentStepIdx(0);
  }, [initialCode]);

  const stepPrev = useCallback(() => setCurrentStepIdx((p) => Math.max(0, p - 1)), []);
  const stepNext = useCallback(
    () => setCurrentStepIdx((p) => Math.min(steps.length - 1, p + 1)),
    [steps.length],
  );

  const currentStep = steps[currentStepIdx];

  return (
    <div
      className="rounded-xl border border-sky-500/20 overflow-hidden shadow-2xl flex flex-col h-full md:h-[min(80vh,700px)]"
      style={{
        background: 'var(--surface-card)',
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.06), 0 20px 40px -10px rgba(0,0,0,0.6)',
      }}
    >
      {/* ── Header bar ── */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-[var(--surface-card-deep)] px-4 py-2.5 border-b border-slate-800/70">
        <div className="flex items-center gap-2.5">
          {/* Traffic-light dots */}
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-rose-500/70" />
            <span className="w-3 h-3 rounded-full bg-amber-500/70" />
            <span className="w-3 h-3 rounded-full bg-emerald-500/70" />
          </div>
          <span className="text-sky-400 font-mono text-xs font-bold">
            ⚡ {language.charAt(0).toUpperCase() + language.slice(1)} Interactive IDE{topicTitle ? ` — ${topicTitle}` : ''}
          </span>
          {execTime !== null && (
            <span className="text-[11px] text-emerald-400 font-mono bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
              {execTime} ms
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRun}
            disabled={isExecuting}
            aria-label="Run and step-trace code"
            className="active-press flex items-center gap-1.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-xs px-3.5 py-1.5 rounded-lg shadow transition-all"
            style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2)' }}
          >
            <Play className="w-3.5 h-3.5 fill-current" aria-hidden="true" />
            {isExecuting ? 'Tracing…' : 'Run & Step-Trace'}
          </button>
          <button
            onClick={handleReset}
            aria-label="Reset code to initial state"
            className="active-press flex items-center gap-1 text-slate-400 hover:text-white text-xs px-2.5 py-1.5 rounded bg-slate-800/60 hover:bg-slate-700/60 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        </div>
      </div>

      {/* ── Monaco editor ── */}
      <div className="flex-1 w-full min-h-[16rem]"> {/* Changed from h-64 to flex-1 and min-h */}
        <Editor
          height="100%"
          language={language}
          theme="vs-dark"
          value={code}
          onChange={(val) => setCode(val ?? '')}
          options={{
            fontSize: 13,
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            fontLigatures: true,
            minimap: { enabled: false },
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
            padding: { top: 12 },
            renderLineHighlight: 'gutter',
            smoothScrolling: true,
            cursorSmoothCaretAnimation: 'on',
          }}
        />
      </div>

      {/* ── Execution error ── */}
      {execError && (
        <div className="flex items-start gap-2.5 bg-rose-950/40 border-t border-rose-500/30 px-4 py-3 text-xs text-rose-300 font-mono">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" aria-hidden="true" />
          <pre className="whitespace-pre-wrap">{execError}</pre>
        </div>
      )}

      {/* ── Step stepper ── */}
      {steps.length > 0 && (
        <div className="bg-[var(--surface-input)] border-t border-slate-800/70 p-3 space-y-3">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <button
                onClick={stepPrev}
                disabled={currentStepIdx === 0}
                aria-label="Previous step"
                className="active-press p-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed text-white transition-colors"
              >
                <SkipBack className="w-4 h-4" aria-hidden="true" />
              </button>
              <span className="font-mono text-xs text-sky-400 font-bold tabular-nums">
                Step {currentStepIdx + 1} / {steps.length}
              </span>
              <button
                onClick={stepNext}
                disabled={currentStepIdx === steps.length - 1}
                aria-label="Next step"
                className="active-press p-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed text-white transition-colors"
              >
                <SkipForward className="w-4 h-4" aria-hidden="true" />
              </button>
            </div>

            <div className="text-xs font-mono text-slate-400">
              Line <span className="text-white font-bold">{currentStep?.line_number}</span>
              {currentStep?.event && (
                <span className="ml-2 text-slate-500">({currentStep.event})</span>
              )}
            </div>
          </div>

          {/* Step progress bar */}
          <div className="w-full h-0.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-sky-500 rounded-full transition-all duration-200"
              style={{ width: `${((currentStepIdx + 1) / steps.length) * 100}%` }}
            />
          </div>

          {/* AI explanation */}
          {currentStep?.explanation && (
            <div className="flex items-start gap-2 bg-sky-950/40 border border-sky-500/25 rounded-lg p-2.5 text-xs text-slate-200">
              <Sparkles className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" aria-hidden="true" />
              <div>{currentStep.explanation}</div>
            </div>
          )}

          {/* Live variable scope table */}
          {currentStep?.variables && Object.keys(currentStep.variables).length > 0 && (
            <div className="bg-[var(--surface-card-deep)] rounded-lg border border-slate-800/70 p-2 overflow-x-auto font-mono text-xs">
              <div className="text-[10px] text-slate-400 uppercase font-bold mb-2 tracking-wider">
                Active Memory Scope
              </div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(currentStep.variables).map(([k, v]: [string, any]) => (
                  <div key={k} className="bg-slate-900 border border-slate-700/60 px-2 py-1 rounded text-xs">
                    <span className="text-sky-400 font-bold">{k}: </span>
                    <span className="text-emerald-300">{v?.value ?? v?.raw ?? (v === null ? 'null' : v === undefined ? 'undefined' : String(v))}</span>
                    {v?.type && <span className="text-[9px] text-slate-500 ml-1">({v.type})</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Terminal output ── */}
      {stdout && (
        <div className="bg-[var(--background-footer)] p-3 border-t border-slate-800/70 font-mono text-xs text-slate-300">
          <div className="flex items-center gap-1.5 text-slate-500 text-[11px] mb-1.5">
            <Terminal className="w-3.5 h-3.5" aria-hidden="true" /> Console Output
          </div>
          <pre className="text-emerald-400 whitespace-pre-wrap">{stdout}</pre>
        </div>
      )}
    </div>
  );
}
