import { notFound } from 'next/navigation';
import Link from 'next/link';
import { getJavaScriptChapterDetail } from '@/lib/api';
import { CodeEditor } from '@/components/ui/CodeEditor';
import { QuizCard } from '@/components/ui/QuizCard';
import { ArrowLeft, ArrowRight, CheckCircle, Video, AlertTriangle, BookOpen, Zap } from 'lucide-react';
import type { ChapterDetail } from '@/lib/types';

interface ChapterPageProps {
  params: Promise<{ slug: string }>;
}

export default async function JavaScriptChapterDetailPage({ params }: ChapterPageProps) {
  const { slug } = await params;
  const chapter: ChapterDetail | null = await getJavaScriptChapterDetail(slug);

  if (!chapter) notFound();

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 space-y-10">

      {/* ── Breadcrumb ── */}
      <div className="flex items-center justify-between text-xs text-slate-400 font-bold">
        <Link
          href="/learn/javascript"
          className="hover:text-sky-400 flex items-center gap-1 transition-colors active-press"
        >
          <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" /> Back to All Chapters
        </Link>
        <span className="bg-sky-500/10 text-sky-400 border border-sky-500/25 px-2.5 py-0.5 rounded font-mono">
          Chapter {chapter.order} / 15
        </span>
      </div>

      {/* ── Chapter header ── */}
      <header className="space-y-3">
        <div className="flex items-center gap-2 text-xs font-bold text-sky-400 uppercase tracking-wider">
          <Zap className="w-3.5 h-3.5" aria-hidden="true" />
          <span>{chapter.category}</span>
          <span className="text-slate-600">·</span>
          <span>{chapter.read_time}</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-white tracking-[-0.03em] leading-[1.08] text-balance">
          {chapter.title}
        </h1>
        <p className="text-slate-300 text-sm sm:text-base leading-relaxed max-w-3xl">{chapter.takeaway}</p>
      </header>

      {/* ── Interactive Monaco IDE ── */}
      <section className="space-y-3">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <span aria-hidden="true">💻</span> Interactive Code Playground &amp; V8 Step Tracer
        </h2>
        <CodeEditor initialCode={chapter.starter_code} topicTitle={chapter.title} />
      </section>

      {/* ── Introduction ── */}
      <section className="craft-card p-6 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-sky-400" aria-hidden="true" /> Concept Overview &amp; Architecture
        </h2>
        <div
          className="prose prose-invert prose-sm max-w-none text-slate-300 leading-relaxed"
          dangerouslySetInnerHTML={{ __html: chapter.introduction }}
        />
      </section>

      {/* ── Mental Model ── */}
      {chapter.mental_model && (
        <section className="space-y-3">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span aria-hidden="true">🧠</span> V8 Runtime Mental Model
          </h2>
          <div
            className="rounded-xl overflow-hidden border border-slate-800/70"
            dangerouslySetInnerHTML={{ __html: chapter.mental_model }}
          />
        </section>
      )}

      {/* ── Real-World Analogy ── */}
      {chapter.analogy && (
        <section
          className="relative rounded-xl border border-sky-500/20 p-6 space-y-4 overflow-hidden"
          style={{
            background: 'radial-gradient(120% 120% at 50% 0%, rgba(56,189,248,0.07) 0%, rgba(8,14,26,0.95) 100%)',
            boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.07)',
          }}
        >
          <h3 className="text-base font-bold text-sky-400 flex items-center gap-2">
            <span aria-hidden="true">💡</span> Real-World Analogy: {chapter.analogy.title}
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">{chapter.analogy.text}</p>

          {chapter.analogy.mapping && chapter.analogy.mapping.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              {chapter.analogy.mapping.map((m, idx) => (
                <div key={idx} className="bg-[var(--surface-card-deep)] border border-slate-800/70 p-3 rounded-lg text-xs space-y-1">
                  <div className="text-slate-400 font-medium">🌍 {m.real}</div>
                  <div className="text-sky-400 font-mono font-bold">💻 {m.prog}</div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* ── Common Mistakes ── */}
      {(chapter.common_mistakes?.length ?? 0) > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" aria-hidden="true" /> Common Pitfalls &amp; How to Fix Them
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {chapter.common_mistakes.map((m, idx) => (
              <div key={idx} className="craft-card p-5 space-y-3">
                <h3 className="font-bold text-white text-sm">{m.title}</h3>
                <div className="space-y-1">
                  <span className="text-[10px] uppercase font-bold text-rose-400">❌ Anti-Pattern</span>
                  <pre className="bg-[var(--surface-card-deep)] border border-rose-500/20 p-3 rounded-lg text-xs font-mono text-rose-300 overflow-x-auto">
                    <code>{m.bad}</code>
                  </pre>
                  <p className="text-xs text-slate-400">{m.why_bad}</p>
                </div>
                <div className="space-y-1 pt-2">
                  <span className="text-[10px] uppercase font-bold text-emerald-400">✅ Recommended</span>
                  <pre className="bg-[var(--surface-card-deep)] border border-emerald-500/20 p-3 rounded-lg text-xs font-mono text-emerald-300 overflow-x-auto">
                    <code>{m.good}</code>
                  </pre>
                  <p className="text-xs text-slate-400">{m.why_good}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── Prediction Quizzes ── */}
      {(chapter.predict_quizzes?.length ?? 0) > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span aria-hidden="true">🎯</span> Interactive Prediction Quizzes
          </h2>
          {chapter.predict_quizzes.map((quiz, qIdx) => (
            <QuizCard
              key={qIdx}
              chapterSlug={chapter.slug}
              quizIndex={qIdx}
              code={quiz.code}
              options={quiz.options}
              answer={quiz.answer}
              explanation={quiz.explanation}
            />
          ))}
        </section>
      )}

      {/* ── Video Masterclasses ── */}
      {(chapter.video_tutorials?.length ?? 0) > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Video className="w-5 h-5 text-rose-400" aria-hidden="true" /> Curated Video Masterclasses
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {chapter.video_tutorials.map((vid, idx) => (
              <div key={idx} className="craft-card overflow-hidden">
                <div className="aspect-video bg-black">
                  <iframe
                    src={`https://www.youtube-nocookie.com/embed/${vid.youtube_id}`}
                    title={vid.title}
                    className="w-full h-full border-0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                    loading="lazy"
                  />
                </div>
                <div className="p-4 space-y-1.5">
                  <span className="text-[10px] font-bold text-sky-400 font-mono">{vid.channel} · {vid.duration}</span>
                  <h3 className="font-bold text-white text-sm line-clamp-2">{vid.title}</h3>
                  <p className="text-xs text-slate-400 line-clamp-2">{vid.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── Quick Revision ── */}
      {(chapter.quick_revision?.length ?? 0) > 0 && (
        <section className="craft-card p-6 space-y-3 border-sky-500/20">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span aria-hidden="true">⚡</span> Quick Revision Checklist
          </h3>
          <ul className="space-y-2 text-xs text-slate-300">
            {chapter.quick_revision.map((bullet, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" aria-hidden="true" />
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* ── Chapter navigation ── */}
      <footer className="flex flex-wrap items-center justify-between gap-4 pt-6 border-t border-slate-800/70">
        {chapter.prev_chapter ? (
          <Link
            href={`/learn/javascript/${chapter.prev_chapter.slug}`}
            className="active-press flex items-center gap-2 text-xs font-bold text-slate-300 hover:text-sky-400 bg-[var(--surface-card)] border border-slate-800 hover:border-sky-500/30 px-4 py-2.5 rounded-xl transition-all max-w-[45%]"
            style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05)' }}
          >
            <ArrowLeft className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
            <span className="truncate">← {chapter.prev_chapter.title}</span>
          </Link>
        ) : (
          <div />
        )}

        {chapter.next_chapter && (
          <Link
            href={`/learn/javascript/${chapter.next_chapter.slug}`}
            className="active-press flex items-center gap-2 text-xs font-bold text-white bg-sky-600 hover:bg-sky-500 px-5 py-2.5 rounded-xl shadow-lg shadow-sky-500/20 transition-all max-w-[45%]"
            style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.15)' }}
          >
            <span className="truncate">{chapter.next_chapter.title} →</span>
            <ArrowRight className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          </Link>
        )}
      </footer>
    </div>
  );
}
