import Link from 'next/link';
import { getJavaScriptRoadmap, getJavaScriptChapters } from '@/lib/api';
import type { RoadmapStage, ChapterSummary } from '@/lib/types';
import { Zap, Clock, PlayCircle } from 'lucide-react';

export const dynamic = 'force-dynamic';

export default async function JavaScriptCurriculumPage() {
  let roadmap: RoadmapStage[] = [];
  let chapters: ChapterSummary[] = [];

  await Promise.all([
    getJavaScriptRoadmap().then((d) => { roadmap = d; }).catch(() => {}),
    getJavaScriptChapters().then((d) => { chapters = d; }).catch(() => {}),
  ]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-14 space-y-14">

      {/* ── Page header ── */}
      <div className="text-center space-y-5 max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-1.5 bg-sky-500/10 text-sky-400 border border-sky-500/25 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider">
          <Zap className="w-3.5 h-3.5" aria-hidden="true" /> DevAcademy Masterclass
        </div>
        <h1 className="text-4xl sm:text-6xl font-black text-white tracking-[-0.035em] leading-[1.05] text-balance">
          JavaScript (ES6+) Masterclass
        </h1>
        <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
          15 deep-dive modules engineered for full-stack mastery: V8 engine mechanics, execution contexts, lexical scoping, prototype chains, and asynchronous microtasks.
        </p>

        {/* Stats row */}
        <div className="flex flex-wrap items-center justify-center gap-6 text-xs text-slate-500 pt-2">
          {[
            { v: `${chapters.length} Chapters`, c: 'text-sky-400' },
            { v: `${roadmap.length} Stages`, c: 'text-teal-400' },
            { v: 'Interactive IDE', c: 'text-indigo-400' },
            { v: 'Quizzes & Challenges', c: 'text-emerald-400' },
          ].map(({ v, c }) => (
            <span key={v} className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${c} bg-current`} />
              {v}
            </span>
          ))}
        </div>
      </div>

      {/* ── Roadmap stages ── */}
      {roadmap.length > 0 && (
        <div className="space-y-6">
          <h2 className="text-xl font-extrabold text-white flex items-center gap-2 border-b border-slate-800/70 pb-4">
            <span aria-hidden="true">🛣️</span> 7-Stage Structured Learning Journey
          </h2>

          <div className="space-y-5">
            {roadmap.map((stage) => (
              <div
                key={stage.stage_number}
                className="craft-card p-6 space-y-5"
              >
                {/* Stage header */}
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span
                      className="w-8 h-8 rounded-lg flex items-center justify-center font-black text-xs text-white shrink-0"
                      style={{ backgroundColor: stage.badge_color }}
                      aria-label={`Stage ${stage.stage_number}`}
                    >
                      {stage.stage_number}
                    </span>
                    <h3 className="font-extrabold text-lg text-white">{stage.stage_title}</h3>
                  </div>
                  <span className="text-xs font-mono text-slate-400 bg-slate-800/50 px-2.5 py-1 rounded-lg">
                    {stage.chapters.length} Chapters
                  </span>
                </div>

                <p className="text-xs text-slate-400 leading-relaxed max-w-2xl">{stage.description}</p>

                {/* Chapter cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {stage.chapters.map((ch: ChapterSummary) => (
                    <Link
                      key={ch.slug}
                      href={`/learn/javascript/${ch.slug}`}
                      className="group bg-[var(--surface-input)] hover:bg-[var(--surface-hover)] border border-slate-800/70 hover:border-sky-500/40 rounded-xl p-4 transition-all flex flex-col justify-between active-press"
                      style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.04)' }}
                    >
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between text-[11px] text-slate-400">
                          <span className="font-mono text-sky-400 font-bold">Ch.{String(ch.order).padStart(2, '0')}</span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" aria-hidden="true" /> {ch.read_time}
                          </span>
                        </div>
                        <h4 className="font-bold text-white text-sm group-hover:text-sky-400 transition-colors line-clamp-2 leading-snug">
                          {ch.title}
                        </h4>
                      </div>

                      <div className="pt-3 mt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500">
                        <span className="flex items-center gap-1">
                          <PlayCircle className="w-3 h-3" aria-hidden="true" /> {ch.videos_count} ·
                          {ch.quizzes_count} Q
                        </span>
                        <span className="text-sky-400 font-bold group-hover:translate-x-1 transition-transform">
                          →
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fallback: flat chapter list if no roadmap */}
      {roadmap.length === 0 && chapters.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-extrabold text-white border-b border-slate-800/70 pb-4">All Chapters</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {chapters.map((ch) => (
              <Link
                key={ch.slug}
                href={`/learn/javascript/${ch.slug}`}
                className="craft-card group p-5 flex flex-col justify-between active-press"
              >
                <div className="space-y-1.5">
                  <span className="font-mono text-sky-400 font-bold text-[11px]">Ch.{String(ch.order).padStart(2, '0')}</span>
                  <h3 className="font-bold text-white text-sm group-hover:text-sky-400 transition-colors line-clamp-2">{ch.title}</h3>
                </div>
                <div className="pt-3 mt-3 border-t border-slate-800/60 text-[11px] text-slate-500 flex items-center justify-between">
                  <span>{ch.read_time}</span>
                  <span className="text-sky-400 font-bold group-hover:translate-x-1 transition-transform">→</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {roadmap.length === 0 && chapters.length === 0 && (
        <div className="text-center py-24 space-y-3">
          <p className="text-slate-400">Curriculum data unavailable — make sure the Django API is running.</p>
          <a
            href={process.env.NEXT_PUBLIC_API_DOCS_URL || 'http://localhost:8000/api/v1/docs'}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-sky-400 hover:text-sky-300 underline underline-offset-2"
          >
            Open API Docs →
          </a>
        </div>
      )}
    </div>
  );
}
