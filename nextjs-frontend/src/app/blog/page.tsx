import Link from 'next/link';
import { getBlogPosts, getBlogCategories } from '@/lib/api';
import { BookOpen, Clock, Eye, Sparkles } from 'lucide-react';

interface BlogPageProps {
  searchParams: Promise<{ category?: string; search?: string }>;
}

export default async function BlogIndexPage({ searchParams }: BlogPageProps) {
  const { category, search } = await searchParams;
  const [{ posts, total }, categories] = await Promise.all([
    getBlogPosts({ category, search, limit: 12 }),
    getBlogCategories(),
  ]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-12 space-y-10">
      {/* Blog Header */}
      <div className="text-center space-y-4 max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-1.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-3 py-1 rounded-full text-xs font-bold uppercase">
          <BookOpen className="w-3.5 h-3.5" /> Engineering &amp; Architecture
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight">
          Technical Blog &amp; Deep Dives
        </h1>
        <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
          Comprehensive guides covering V8 internals, Next.js 15, React 19 Server Components, Django Ninja, and PostgreSQL optimization.
        </p>
      </div>

      {/* Category Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        <Link
          href="/blog"
          className={`px-3.5 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition-all ${
            !category
              ? 'bg-sky-500 text-white shadow-lg shadow-sky-500/25'
              : 'bg-[#0d1527] border border-slate-800 text-slate-400 hover:text-white'
          }`}
        >
          All Topics ({total})
        </Link>
        {categories.map((c) => (
          <Link
            key={c.slug}
            href={`/blog?category=${c.slug}`}
            className={`px-3.5 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition-all flex items-center gap-1.5 ${
              category === c.slug
                ? 'bg-sky-500 text-white shadow-lg shadow-sky-500/25'
                : 'bg-[#0d1527] border border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            <span>{c.icon}</span> {c.name} ({c.posts_count})
          </Link>
        ))}
      </div>

      {/* Posts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {posts.map((post) => (
          <Link
            key={post.slug}
            href={`/blog/${post.slug}`}
            className="group bg-[#0d1527] border border-sky-500/15 hover:border-sky-500/50 rounded-xl overflow-hidden transition-all flex flex-col justify-between hover:-translate-y-1 shadow-lg"
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
            <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="text-sky-400 font-bold">{post.category?.name}</span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" /> {post.read_time_minutes} min read
                  </span>
                </div>
                <h2 className="font-bold text-white group-hover:text-sky-400 transition-colors text-base line-clamp-2">
                  {post.title}
                </h2>
                <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed">
                  {post.excerpt}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-800 text-xs text-slate-400 flex items-center justify-between">
                <span>{post.author_name}</span>
                <span className="flex items-center gap-1 text-slate-500">
                  <Eye className="w-3 h-3" /> {post.views_count}
                </span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
