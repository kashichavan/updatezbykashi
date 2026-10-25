import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion'; // Import motion
import { getFeaturedPosts, getJavaScriptChapters } from '@/lib/api';
import { Sparkles, BookOpen, ArrowRight, Zap, Code2 } from 'lucide-react';
import type { BlogPost, ChapterSummary } from '@/lib/types';

export const dynamic = 'force-dynamic';

/* ── Empty-state placeholder cards ── */
function ChapterSkeleton() {
  return (
    <div className="craft-card p-5 space-y-3 animate-pulse">
      <div className="h-3 skeleton w-20" />
      <div className="h-4 skeleton w-3/4" />
      <div className="h-3 skeleton w-full" />
      <div className="h-3 skeleton w-2/3" />
    </div>
  );
}

function PostSkeleton() {
  return (
    <div className="craft-card overflow-hidden animate-pulse">
      <div className="h-44 skeleton" />
      <div className="p-5 space-y-3">
        <div className="h-3 skeleton w-24" />
        <div className="h-4 skeleton w-3/4" />
        <div className="h-3 skeleton w-full" />
      </div>
    </div>
  );
}

export default async function HomePage() {
  let featuredPosts: BlogPost[] = [];
  let jsChapters: ChapterSummary[] = [];

  await Promise.all([
    getFeaturedPosts(3)
      .then((d) => { featuredPosts = d; })
      .catch(() => {}),
    getJavaScriptChapters()
      .then((d) => { jsChapters = d; })
      .catch(() => {}),
  ]);

  return (
    <div className="space-y-24 pb-24">

      {/* ══════════════════════════════════════════
          HERO
      ══════════════════════════════════════════ */}
      <section className="relative overflow-hidden pt-28 pb-20 px-4">
        {/* Ambient radial spotlight */}
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-10%,rgba(56,189,248,0.15),transparent)]" />
        {/* Noise grain */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.025] mix-blend-overlay"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
          }}
        />

        <div className="max-w-5xl mx-auto text-center space-y-7 relative z-10">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-sky-500/10 border border-sky-500/25 text-sky-400 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider animate-fade-in-up">
            <Sparkles className="w-3.5 h-3.5" aria-hidden="true" />
            FRESH DAILY STUDENT REQUIREMENTS
          </div>

          {/* Headline */}
          <h1
            className="text-4xl sm:text-6xl font-black text-white tracking-[-0.035em] leading-[1.1] text-balance animate-fade-in-up"
            style={{ animationDelay: '60ms' }}
          >
            Kashii Updates — Daily Student Jobs &amp;{' '}
            <span className="bg-gradient-to-r from-sky-400 via-teal-300 to-indigo-400 bg-clip-text text-transparent italic">
              Internship Requirements
            </span>
          </h1>

          {/* Sub-copy */}
          <p
            className="text-slate-300 text-base sm:text-lg max-w-2xl mx-auto leading-relaxed animate-fade-in-up font-normal"
            style={{ animationDelay: '120ms' }}
          >
            <strong className="text-white font-bold">Kashii Updates</strong> (also known as <strong className="text-white font-bold">Kashii Updatez</strong>) provides verified daily student requirements, off-campus drives, &amp; internships. All postings remain active for exactly 7 days to guarantee 100% fresh opportunities.
          </p>

          {/* Trust pills */}
          <div
            className="flex flex-wrap items-center justify-center gap-2.5 pt-1 animate-fade-in-up text-xs text-slate-300 font-semibold"
            style={{ animationDelay: '150ms' }}
          >
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 shadow-sm">
              ⚡ Auto 7-Day Fresh Rule
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 shadow-sm">
              💻 Software &amp; Tech
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 shadow-sm">
              🔗 Official Direct Links
            </span>
          </div>

          {/* CTAs */}
          <div
            className="flex flex-wrap items-center justify-center gap-4 pt-2 animate-fade-in-up"
            style={{ animationDelay: '180ms' }}
          >
            <Link href="/learn/javascript">
              <motion.div
                whileHover={{ y: -3, rotateX: 5, z: 20 }}
                whileTap={{ scale: 0.98 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
                className="active-press inline-flex items-center gap-2 bg-gradient-to-r from-sky-500 via-blue-500 to-indigo-500 hover:from-sky-400 hover:via-blue-400 hover:to-indigo-400 text-white font-bold px-7 py-3.5 rounded-xl text-sm shadow-lg shadow-sky-500/30 hover:shadow-sky-500/50 transition-all duration-300"
                style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2), 0 4px 14px -2px rgba(56,189,248,0.45)' }}
              >
                <Zap className="w-4 h-4" aria-hidden="true" /> Start JS Masterclass
              </motion.div>
            </Link>
            <Link href="/blog">
              <motion.div
                whileHover={{ y: -3, rotateX: 5, z: 20 }}
                whileTap={{ scale: 0.98 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
                className="active-press inline-flex items-center gap-2 bg-[var(--surface-card)] hover:bg-[var(--surface-hover)] border border-slate-700/60 hover:border-slate-600 text-slate-200 font-bold px-7 py-3.5 rounded-xl text-sm transition-all"
                style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.06)' }}
              >
                <BookOpen className="w-4 h-4" aria-hidden="true" /> Read Tech Blog
              </motion.div>
            </Link>
          </div>

          {/* Quick stats row */}
          <div
            className="flex flex-wrap items-center justify-center gap-6 pt-4 text-xs text-slate-500 animate-fade-in-up"
            style={{ animationDelay: '240ms' }}
          >
            {[
              { label: '15 Chapters', color: 'text-sky-400' },
              { label: 'V8 Step Tracer', color: 'text-teal-400' },
              { label: 'Live Code Editor', color: 'text-indigo-400' },
              { label: 'Django Ninja API', color: 'text-emerald-400' },
            ].map(({ label, color }) => (
              <span key={label} className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${color} bg-current`} />
                {label}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════
          JS CURRICULUM SHOWCASE
      ══════════════════════════════════════════ */}
      <section className="max-w-7xl mx-auto px-4 space-y-8">
        <div className="flex flex-wrap items-end justify-between gap-4 border-b border-slate-800/70 pb-5">
          <div>
            <span className="text-xs font-bold text-sky-400 uppercase tracking-wider">Interactive DevAcademy</span>
            <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight mt-1">
              JavaScript ES6+ Complete Masterclass
            </h2>
          </div>
          <Link
            href="/learn/javascript"
            className="active-press text-xs font-bold text-sky-400 hover:text-sky-300 flex items-center gap-1 transition-colors"
          >
            View All 15 Chapters <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {jsChapters.length === 0
            ? Array.from({ length: 6 }).map((_, i) => <ChapterSkeleton key={i} />)
            : jsChapters.slice(0, 6).map((ch) => (
                <Link
                  key={ch.slug}
                  href={`/learn/javascript/${ch.slug}`}
                  className="craft-card group p-5 flex flex-col justify-between min-h-[160px]"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span className="bg-sky-500/10 text-sky-400 font-mono font-bold px-2 py-0.5 rounded text-[10px]">
                        Ch.{String(ch.order).padStart(2, '0')}
                      </span>
                      <span>{ch.read_time}</span>
                    </div>
                    <h3 className="font-bold text-white group-hover:text-sky-400 transition-colors text-sm leading-snug line-clamp-2">
                      {ch.title}
                    </h3>
                    <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">{ch.takeaway}</p>
                  </div>

                  <div className="pt-4 mt-4 border-t border-slate-800/70 flex items-center justify-between text-[11px] text-slate-500">
                    <span>{ch.category}</span>
                    <span className="text-sky-400 font-bold flex items-center gap-0.5 group-hover:translate-x-1 transition-transform">
                      Explore →
                    </span>
                  </div>
                </Link>
              ))}
        </div>
      </section>

      {/* ══════════════════════════════════════════
          FEATURED ENGINEERING ARTICLES
      ══════════════════════════════════════════ */}
      <section className="max-w-7xl mx-auto px-4 space-y-8">
        <div className="flex flex-wrap items-end justify-between gap-4 border-b border-slate-800/70 pb-5">
          <div>
            <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Engineering Articles</span>
            <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight mt-1">Technical Deep Dives</h2>
          </div>
          <Link
            href="/blog"
            className="active-press text-xs font-bold text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition-colors"
          >
            Browse All Posts <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {featuredPosts.length === 0
            ? Array.from({ length: 3 }).map((_, i) => <PostSkeleton key={i} />)
            : featuredPosts.map((post) => (
                <Link
                  key={post.slug}
                  href={`/blog/${post.slug}`}
                  className="craft-card group overflow-hidden flex flex-col"
                >
                  {post.cover_image_url && (
                    <div className="relative h-44 bg-slate-900 overflow-hidden">
                      <Image
                        src={post.cover_image_url}
                        alt={post.title}
                        fill
                        className="object-cover group-hover:scale-105 transition-transform duration-500"
                        sizes="(max-width: 768px) 100vw, 33vw"
                      />
                    </div>
                  )}
                  <div className="p-5 flex-1 flex flex-col justify-between space-y-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-[11px] text-slate-400">
                        <span className="text-emerald-400 font-bold">{post.category?.name}</span>
                        <span>{post.read_time_minutes} min read</span>
                      </div>
                      <h3 className="font-bold text-white group-hover:text-emerald-400 transition-colors text-sm leading-snug line-clamp-2">
                        {post.title}
                      </h3>
                      <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed">{post.excerpt}</p>
                    </div>
                    <div className="pt-3 border-t border-slate-800/70 text-xs text-slate-400 flex items-center justify-between">
                      <span>{post.author_name}</span>
                      <span className="text-emerald-400 font-bold group-hover:translate-x-1 transition-transform">Read →</span>
                    </div>
                  </div>
                </Link>
              ))}
        </div>
      </section>

      {/* ══════════════════════════════════════════
          BOTTOM CTA BANNER
      ══════════════════════════════════════════ */}
      <section className="max-w-4xl mx-auto px-4">
        <div
          className="relative overflow-hidden rounded-2xl border border-sky-500/20 p-10 text-center space-y-5"
          style={{
            background: 'radial-gradient(120% 120% at 50% 0%, rgba(56,189,248,0.08) 0%, rgba(8,14,26,0.95) 100%)',
            boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.08)',
          }}
        >
          <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(ellipse_60%_40%_at_50%_0%,rgba(56,189,248,0.1),transparent)]" />
          <Code2 className="w-8 h-8 text-sky-400 mx-auto" aria-hidden="true" />
          <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Ready to go deep on JavaScript?
          </h2>
          <p className="text-slate-400 text-sm max-w-xl mx-auto">
            Jump into the interactive masterclass — step through V8 execution with real-time AST tracing, tackle quizzes, and build intuition that sticks.
          </p>
          <Link
            href="/learn/javascript"
            className="active-press inline-flex items-center gap-2 bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 text-white font-bold px-8 py-3.5 rounded-xl text-sm shadow-lg shadow-sky-500/30 transition-all"
            style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2), 0 4px 14px -2px rgba(56,189,248,0.4)' }}
          >
            <Zap className="w-4 h-4" aria-hidden="true" /> Begin Masterclass
          </Link>
        </div>
      </section>
    </div>
  );
}
