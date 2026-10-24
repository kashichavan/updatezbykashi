'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { getBlogPosts, getBlogCategories } from '@/lib/api';
import { BookOpen, Clock, Eye, Sparkles, Search, Loading, CheckCircle2 } from 'lucide-react';

export default function BlogIndexPage() {
  const searchParams = useSearchParams();
  const category = searchParams.get('category') || '';
  const search = searchParams.get('search') || '';

  const [posts, setPosts] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setIsError(false);
    try {
      const postsRes = await getBlogPosts({ category: category || undefined, search: search || undefined });
      setPosts(postsRes.posts);
      const catsRes = await getBlogCategories();
      setCategories(catsRes);
    } catch (err) {
      console.error('Failed to load blog data:', err);
      setIsError(true);
    } finally {
      setIsLoading(false);
    }
  }, [category, search]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Debounced category filter change
  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newCategory = e.target.value;
    // Update URL without reloading
    const url = new URL(window.location.href);
    if (newCategory) {
      url.searchParams.set('category', newCategory);
    } else {
      url.searchParams.delete('category');
    }
    window.history.pushState({}, '', url.toString());
    // Trigger reload
    sessionStorage.setItem('blog_reload', Date.now().toString());
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12">
        {/* Hero */}
        <div className="text-center space-y-4 mb-8">
          <div className="inline-flex items-center gap-1.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-3 py-1 rounded-full text-xs font-bold uppercase">
            <BookOpen className="w-3 h-3" /> Engineering & Architecture
          </div>
          <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight">Technical Blog & Deep Dives</h1>
        </div>

        <SkeletonGrid />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="text-center">
          <p className="text-red-400 mb-4">Failed to load content.</p>
          <button onClick={loadData} className="bg-sky-500 text-white px-6 py-2 rounded-lg hover:bg-sky-400 transition-colors">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-12 space-y-10">
      {/* Blog Header */}
      <div className="text-center space-y-4 max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-1.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-3 py-1 rounded-full text-xs font-bold uppercase">
          <Sparkles className="w-3 h-3" /> Engineering & Architecture
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight">Technical Blog & Deep Dives</h1>
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
          All Topics ({categories.length})
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
          <article
            key={post.id}
            className="group bg-[#0d1527] border border-sky-500/15 hover:border-sky-500/50 rounded-xl overflow-hidden transition-all flex flex-col hover:-translate-y-1 shadow-lg"
          >
            {post.cover_image_url && (
              <div className="h-44 overflow-hidden bg-slate-900">
                <img
                  src={post.cover_image_url}
                  alt={post.title}
                  loading="lazy"
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
          </article>
        ))}
      </div>

      {/* Bottom CTA */}
      <div className="mt-8 max-w-3xl mx-auto text-center pb-12 pt-6">
        <p className="text-sm text-slate-400 mb-4 inline-block pb-1 px-2 border-b border-slate-800">
          Ready to level up your engineering game?
        </p>
      </div>
    </div>
  );
}

function SkeletonGrid() {
  return (
    <>
      {[0, 1, 2].map((i) => (
        <div key={i} className="bg-[#0d1527] border border-slate-800/60 rounded-xl p-5 my-4">
          <div className="h-4 bg-slate-800/50 rounded mb-4 w-32"></div>
          <div className="h-5 bg-slate-800/30 rounded mb-3 w-2/3"></div>
          <div className="h-3 bg-slate-800/30 rounded mb-2 w-1/2"></div>
        </div>
      ))}
    </>
  );
}