import Link from 'next/link';
import { getJavaScriptRoadmap, getJavaScriptChapters } from '@/lib/api';
import { Zap, BookOpen, CheckCircle2, PlayCircle, Trophy, Sparkles } from 'lucide-react';

export default async function JavaScriptCurriculumPage() {
  const [roadmap, chapters] = await Promise.all([
    getJavaScriptRoadmap(),
    getJavaScriptChapters(),
  ]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-12 space-y-12">
      {/* Header */}
      <div className="text-center space-y-4 max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-1.5 bg-sky-500/10 text-sky-400 border border-sky-500/30 px-3.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
          <Zap className="w-3.5 h-3.5" /> DevAcademy Masterclass
        </div>
        <h1 className="text-4xl sm:text-6xl font-black text-white tracking-tight">
          JavaScript (ES6+) Masterclass
        </h1>
        <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
          15 deep-dive modules engineered for full-stack mastery: V8 engine mechanics, execution contexts, lexical scoping, prototype chains, and asynchronous microtasks.
        </p>
      </div>

      {/* 7-Stage Visual Roadmap */}
      <div className="space-y-8">
        <h2 className="text-xl font-extrabold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
          <span>🛣️</span> 7-Stage Structured Learning Journey
        </h2>

        <div className="space-y-6">
          {roadmap.map((stage) => (
            <div
              key={stage.stage_number}
              className="bg-[#0d1527] border border-sky-500/20 rounded-2xl p-6 shadow-xl space-y-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span
                    className="w-7 h-7 rounded-lg flex items-center justify-center font-black text-xs text-white"
                    style={{ backgroundColor: stage.badge_color }}
                  >
                    {stage.stage_number}
                  </span>
                  <h3 className="font-extrabold text-lg text-white">{stage.stage_title}</h3>
                </div>
                <span className="text-xs font-mono text-slate-400">
                  {stage.chapters.length} Chapters
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed max-w-2xl">{stage.description}</p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                {stage.chapters.map((ch) => (
                  <Link
                    key={ch.slug}
                    href={`/learn/javascript/${ch.slug}`}
                    className="group bg-[#111d35] hover:bg-[#172442] border border-slate-800 hover:border-sky-500/50 rounded-xl p-4 transition-all flex flex-col justify-between"
                  >
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-[11px] text-slate-400">
                        <span className="font-mono text-sky-400 font-bold">Ch. {ch.order}</span>
                        <span>{ch.read_time}</span>
                      </div>
                      <h4 className="font-bold text-white text-sm group-hover:text-sky-400 transition-colors line-clamp-2">
                        {ch.title}
                      </h4>
                    </div>

                    <div className="pt-3 mt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
                      <span>{ch.videos_count} Videos &bull; {ch.quizzes_count} Quizzes</span>
                      <span className="text-sky-400 font-bold group-hover:translate-x-1 transition-transform">
                        &rarr;
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
