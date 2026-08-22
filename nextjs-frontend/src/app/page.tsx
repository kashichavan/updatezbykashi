import Link from 'next/link';
import { getFeaturedPosts, getJavaScriptChapters } from '@/lib/api';
import { Sparkles, Code2, BookOpen, Terminal, ArrowRight, Zap, CheckCircle2 } from 'lucide-react';

export default async function HomePage() {
  const [featuredPosts, jsChapters] = await Promise.all([
    getFeaturedPosts(3),
    getJavaScriptChapters(),
  ]);

  return (
    <div className="space-y-20 pb-20">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-16 px-4">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-sky-500/20 via-transparent to-transparent pointer-events-none" />
        
        <div className="max-w-5xl mx-auto text-center space-y-6 relative z-10">
          <div className="inline-flex items-center gap-2 bg-sky-500/10 border border-sky-500/30 text-sky-400 px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" /> Next.js 15 + Django Ninja OpenAPI Stack
          </div>

          <h1 className="text-4xl sm:text-6xl font-black text-white tracking-tight leading-[1.1]">
            Master Modern JavaScript <br />
            <span className="bg-gradient-to-r from-sky-400 via-teal-300 to-indigo-400 bg-clip-text text-transparent">
              With Interactive V8 Step Debuggers
            </span>
          </h1>

          <p className="text-slate-400 text-base sm:text-lg max-w-2xl mx-auto leading-relaxed">
            15 in-depth JavaScript ES6+ masterclass chapters, V8 AST line execution tracers, and Notion-quality engineering deep dives on Next.js, React 19, and Django Ninja.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <Link
              href="/learn/javascript"
              className="bg-sky-500 hover:bg-sky-400 text-white font-bold px-6 py-3 rounded-xl shadow-lg shadow-sky-500/25 flex items-center gap-2 text-sm transition-all"
            >
              <Zap className="w-4 h-4" /> Start JS Masterclass
            </Link>
            <Link
              href="/blog"
              className="bg-[#0d1527] hover:bg-[#152442] border border-slate-800 text-slate-200 font-bold px-6 py-3 rounded-xl text-sm transition-all flex items-center gap-2"
            >
              <BookOpen className="w-4 h-4" /> Read Tech Blog
            </Link>
          </div>
        </div>
      </section>

      {/* JavaScript Curriculum Showcase */}
      <section className="max-w-7xl mx-auto px-4 space-y-8">
        <div className="flex flex-wrap items-end justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <span className="text-xs font-bold text-sky-400 uppercase tracking-wider">Interactive DevAcademy</span>
            <h2 className="text-2xl font-black text-white">JavaScript ES6+ Complete Masterclass</h2>
          </div>
          <Link href="/learn/javascript" className="text-xs font-bold text-sky-400 hover:text-sky-300 flex items-center gap-1">
            View All 15 Chapters <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {jsChapters.slice(0, 6).map((ch) => (
            <Link
              key={ch.slug}
              href={`/learn/javascript/${ch.slug}`}
              className="group bg-[#0d1527] border border-sky-500/15 hover:border-sky-500/50 rounded-xl p-5 transition-all flex flex-col justify-between hover:-translate-y-1 shadow-lg shadow-black/40"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="bg-sky-500/10 text-sky-400 font-mono font-bold px-2 py-0.5 rounded text-[10px]">
                    Chapter {ch.order}
                  </span>
                  <span>{ch.read_time}</span>
                </div>
                <h3 className="font-bold text-white group-hover:text-sky-400 transition-colors text-base line-clamp-2">
                  {ch.title}
                </h3>
                <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                  {ch.takeaway}
                </p>
              </div>

              <div className="pt-4 mt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-500">
                <span>{ch.category}</span>
                <span className="text-sky-400 font-bold flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                  Explore &rarr;
                </span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Featured Engineering Articles */}
      <section className="max-w-7xl mx-auto px-4 space-y-8">
        <div className="flex flex-wrap items-end justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Engineering Articles</span>
            <h2 className="text-2xl font-black text-white">Technical Deep Dives</h2>
          </div>
          <Link href="/blog" className="text-xs font-bold text-emerald-400 hover:text-emerald-300 flex items-center gap-1">
            Browse All Posts <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {featuredPosts.map((post) => (
            <Link
              key={post.slug}
              href={`/blog/${post.slug}`}
              className="group bg-[#0d1527] border border-slate-800 hover:border-emerald-500/40 rounded-xl overflow-hidden transition-all flex flex-col hover:-translate-y-1 shadow-lg"
            >
              {post.cover_image_url && (
                <div className="h-44 overflow-hidden bg-slate-900">
                  <img
                    src={post.cover_image_url}
                    alt={post.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                </div>
              )}
              <div className="p-5 flex-1 flex flex-col justify-between space-y-3">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span className="text-emerald-400 font-bold">{post.category?.name}</span>
                    <span>{post.read_time_minutes} min read</span>
                  </div>
                  <h3 className="font-bold text-white group-hover:text-emerald-400 transition-colors text-base line-clamp-2">
                    {post.title}
                  </h3>
                  <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed">
                    {post.excerpt}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-800 text-xs text-slate-400 flex items-center justify-between">
                  <span>{post.author_name}</span>
                  <span className="text-emerald-400 font-bold">Read &rarr;</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
