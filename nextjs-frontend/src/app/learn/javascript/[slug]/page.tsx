import { notFound } from 'next/navigation';
import Link from 'next/link';
import { getJavaScriptChapterDetail } from '@/lib/api';
import { CodeEditor } from '@/components/ui/CodeEditor';
import { QuizCard } from '@/components/ui/QuizCard';
import { ArrowLeft, ArrowRight, Zap, BookOpen, CheckCircle, Video, AlertTriangle } from 'lucide-react';

interface ChapterPageProps {
  params: Promise<{ slug: string }>;
}

export default async function JavaScriptChapterDetailPage({ params }: ChapterPageProps) {
  const { slug } = await params;
  const chapter = await getJavaScriptChapterDetail(slug);

  if (!chapter) {
    notFound();
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 space-y-10">
      {/* Top Breadcrumb */}
      <div className="flex items-center justify-between text-xs text-slate-400 font-bold">
        <Link href="/learn/javascript" className="hover:text-sky-400 flex items-center gap-1">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to All 15 Chapters
        </Link>
        <span className="bg-sky-500/10 text-sky-400 border border-sky-500/30 px-2.5 py-0.5 rounded font-mono">
          Chapter {chapter.order} / 15
        </span>
      </div>

      {/* Chapter Title & Header */}
      <header className="space-y-3">
        <div className="flex items-center gap-2 text-xs font-bold text-sky-400 uppercase tracking-wider">
          <span>⚡ {chapter.category}</span>
          <span>&bull;</span>
          <span>{chapter.read_time}</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight leading-tight">
          {chapter.title}
        </h1>
        <p className="text-slate-300 text-sm sm:text-base leading-relaxed max-w-3xl">
          {chapter.takeaway}
        </p>
      </header>

      {/* Interactive Monaco IDE & V8 AST Stepper */}
      <section className="space-y-3">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <span>💻</span> Interactive Code Playground &amp; V8 Step Tracer
        </h2>
        <CodeEditor initialCode={chapter.starter_code} topicTitle={chapter.title} />
      </section>

      {/* Introduction HTML */}
      <section className="bg-[#0d1527] border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <span>📖</span> Concept Overview &amp; Architecture
        </h2>
        <div
          className="prose prose-invert max-w-none text-sm text-slate-300 leading-relaxed"
          dangerouslySetInnerHTML={{ __html: chapter.introduction }}
        />
      </section>

      {/* Mental Model */}
      {chapter.mental_model && (
        <section className="space-y-3">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span>🧠</span> V8 Runtime Mental Model
          </h2>
          <div
            className="rounded-xl overflow-hidden border border-slate-800"
            dangerouslySetInnerHTML={{ __html: chapter.mental_model }}
          />
        </section>
      )}

      {/* Real-World Analogy */}
      {chapter.analogy && (
        <section className="bg-gradient-to-br from-[#0d1527] to-[#152442] border border-sky-500/20 rounded-xl p-6 space-y-4">
          <h3 className="text-base font-bold text-sky-400 flex items-center gap-2">
            <span>💡</span> Real-World Mental Model: {chapter.analogy.title}
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">{chapter.analogy.text}</p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            {chapter.analogy.mapping?.map((m, idx) => (
              <div key={idx} className="bg-[#080e1a] border border-slate-800 p-3 rounded-lg text-xs space-y-1">
                <div className="text-slate-400 font-medium">🌍 {m.real}</div>
                <div className="text-sky-400 font-mono font-bold">💻 {m.prog}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Common Mistakes */}
      {chapter.common_mistakes?.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" /> Common Pitfalls &amp; How to Fix Them
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {chapter.common_mistakes.map((m, idx) => (
              <div key={idx} className="bg-[#0d1527] border border-slate-800 rounded-xl p-5 space-y-3">
                <h3 className="font-bold text-white text-sm">{m.title}</h3>
                <div className="space-y-1">
                  <span className="text-[10px] uppercase font-bold text-rose-400">❌ Anti-Pattern</span>
                  <pre className="bg-[#080e1a] border border-rose-500/20 p-2.5 rounded text-xs font-mono text-rose-300 overflow-x-auto">
                    <code>{m.bad}</code>
                  </pre>
                  <p className="text-xs text-slate-400">{m.why_bad}</p>
                </div>
                <div className="space-y-1 pt-2">
                  <span className="text-[10px] uppercase font-bold text-emerald-400">✅ Recommended Solution</span>
                  <pre className="bg-[#080e1a] border border-emerald-500/20 p-2.5 rounded text-xs font-mono text-emerald-300 overflow-x-auto">
                    <code>{m.good}</code>
                  </pre>
                  <p className="text-xs text-slate-400">{m.why_good}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Prediction Quizzes */}
      {chapter.predict_quizzes?.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span>🎯</span> Interactive Prediction Quizzes
          </h2>
          {chapter.predict_quizzes.map((quiz, qIdx) => (
            <QuizCard
              key={qIdx}
              chapterSlug={chapter.slug}
              quizIndex={qIdx}
              code={quiz.code}
              options={quiz.options}
              explanation={quiz.explanation}
            />
          ))}
        </section>
      )}

      {/* Video Masterclasses */}
      {chapter.video_tutorials?.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Video className="w-5 h-5 text-rose-400" /> Curated Video Masterclasses
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {chapter.video_tutorials.map((vid, idx) => (
              <div key={idx} className="bg-[#0d1527] border border-slate-800 rounded-xl overflow-hidden shadow-lg">
                <div className="aspect-video bg-black">
                  <iframe
                    src={`https://www.youtube-nocookie.com/embed/${vid.youtube_id}`}
                    title={vid.title}
                    className="w-full h-full border-0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                </div>
                <div className="p-4 space-y-1.5">
                  <span className="text-[10px] font-bold text-sky-400 font-mono">{vid.channel} &bull; {vid.duration}</span>
                  <h3 className="font-bold text-white text-sm line-clamp-2">{vid.title}</h3>
                  <p className="text-xs text-slate-400 line-clamp-2">{vid.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Quick Revision Bullets */}
      {chapter.quick_revision?.length > 0 && (
        <section className="bg-[#0d1527] border border-sky-500/30 rounded-xl p-6 space-y-3">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span>⚡</span> Quick Revision Checklist
          </h3>
          <ul className="space-y-2 text-xs text-slate-300">
            {chapter.quick_revision.map((bullet, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Next & Previous Chapter Navigation Bar */}
      <footer className="flex flex-wrap items-center justify-between gap-4 pt-6 border-t border-slate-800">
        {chapter.prev_chapter ? (
          <Link
            href={`/learn/javascript/${chapter.prev_chapter.slug}`}
            className="flex items-center gap-2 text-xs font-bold text-slate-300 hover:text-sky-400 bg-slate-900 border border-slate-800 px-4 py-2.5 rounded-xl transition-all"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Previous: {chapter.prev_chapter.title}
          </Link>
        ) : <div />}

        {chapter.next_chapter && (
          <Link
            href={`/learn/javascript/${chapter.next_chapter.slug}`}
            className="flex items-center gap-2 text-xs font-bold text-white bg-sky-600 hover:bg-sky-500 px-5 py-2.5 rounded-xl shadow-lg shadow-sky-500/20 transition-all"
          >
            Next: {chapter.next_chapter.title} <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        )}
      </footer>
    </div>
  );
}
