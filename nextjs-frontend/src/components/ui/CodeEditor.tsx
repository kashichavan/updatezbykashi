'use client';

import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { executeJavaScriptCode } from '@/lib/api';
import { CodeTraceStep } from '@/lib/types';
import { Play, SkipForward, SkipBack, RefreshCw, Sparkles, Terminal } from 'lucide-react';

interface CodeEditorProps {
  initialCode: string;
  topicTitle?: string;
}

export function CodeEditor({ initialCode, topicTitle }: CodeEditorProps) {
  const [code, setCode] = useState(initialCode);
  const [isExecuting, setIsExecuting] = useState(false);
  const [steps, setSteps] = useState<CodeTraceStep[]>([]);
  const [currentStepIdx, setCurrentStepIdx] = useState(0);
  const [stdout, setStdout] = useState('');
  const [execTime, setExecTime] = useState<number | null>(null);

  const handleRun = async () => {
    setIsExecuting(true);
    const res = await executeJavaScriptCode(code);
    setIsExecuting(false);

    if (res.success) {
      setSteps(res.steps);
      setCurrentStepIdx(0);
      setStdout(res.output);
      setExecTime(res.execution_time_ms);
    } else {
      setStdout(res.error || 'Execution failed.');
      setSteps([]);
    }
  };

  const currentStep = steps[currentStepIdx];

  return (
    <div className="rounded-xl border border-sky-500/20 bg-[#0d1527] overflow-hidden shadow-2xl">
      {/* Editor Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-[#080e1a] px-4 py-2.5 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="text-sky-400 font-mono text-xs font-bold">⚡ V8 AST Interactive IDE</span>
          {execTime !== null && (
            <span className="text-[11px] text-emerald-400 font-mono bg-emerald-500/10 px-2 py-0.5 rounded">
              {execTime} ms
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRun}
            disabled={isExecuting}
            className="flex items-center gap-1.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-bold text-xs px-3.5 py-1.5 rounded-lg shadow transition-all"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            {isExecuting ? 'Tracing...' : 'Run & Step-Trace'}
          </button>
          <button
            onClick={() => {
              setCode(initialCode);
              setSteps([]);
              setStdout('');
            }}
            className="flex items-center gap-1 text-slate-400 hover:text-white text-xs px-2.5 py-1.5 rounded bg-slate-800/60"
            title="Reset code"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Monaco Code Editor */}
      <div className="h-64 w-full">
        <Editor
          height="100%"
          language="javascript"
          theme="vs-dark"
          value={code}
          onChange={(val) => setCode(val || '')}
          options={{
            fontSize: 13,
            fontFamily: "'JetBrains Mono', monospace",
            minimap: { enabled: false },
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
      </div>

      {/* Step Stepper Navigation Controls */}
      {steps.length > 0 && (
        <div className="bg-[#0b1222] border-t border-slate-800 p-3 space-y-3">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentStepIdx((prev) => Math.max(0, prev - 1))}
                disabled={currentStepIdx === 0}
                className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-white"
                title="Previous step"
              >
                <SkipBack className="w-4 h-4" />
              </button>
              <span className="font-mono text-xs text-sky-400 font-bold">
                Step {currentStepIdx + 1} / {steps.length}
              </span>
              <button
                onClick={() => setCurrentStepIdx((prev) => Math.min(steps.length - 1, prev + 1))}
                disabled={currentStepIdx === steps.length - 1}
                className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-white"
                title="Next step"
              >
                <SkipForward className="w-4 h-4" />
              </button>
            </div>

            <div className="text-xs font-mono text-slate-400">
              Line <span className="text-white font-bold">{currentStep?.line_number}</span>
            </div>
          </div>

          {/* AI Explanation Banner */}
          {currentStep?.explanation && (
            <div className="flex items-start gap-2 bg-sky-950/40 border border-sky-500/30 rounded-lg p-2.5 text-xs text-slate-200">
              <Sparkles className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
              <div>{currentStep.explanation}</div>
            </div>
          )}

          {/* Live Variable Scope Table */}
          {currentStep?.variables && Object.keys(currentStep.variables).length > 0 && (
            <div className="bg-[#080e1a] rounded-lg border border-slate-800 p-2 overflow-x-auto font-mono text-xs">
              <div className="text-[10px] text-slate-400 uppercase font-bold mb-1">Active Memory Scope (V8 Variables)</div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(currentStep.variables).map(([k, v]: [string, any]) => (
                  <div key={k} className="bg-slate-900 border border-slate-700/80 px-2 py-1 rounded text-xs">
                    <span className="text-sky-400 font-bold">{k}: </span>
                    <span className="text-emerald-300">{v.value || v.raw}</span>
                    <span className="text-[9px] text-slate-500 ml-1">({v.type})</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Terminal Output */}
      {stdout && (
        <div className="bg-[#050811] p-3 border-t border-slate-800/80 font-mono text-xs text-slate-300">
          <div className="flex items-center gap-1.5 text-slate-500 text-[11px] mb-1">
            <Terminal className="w-3.5 h-3.5" /> Console Output
          </div>
          <pre className="text-emerald-400 whitespace-pre-wrap">{stdout}</pre>
        </div>
      )}
    </div>
  );
}
