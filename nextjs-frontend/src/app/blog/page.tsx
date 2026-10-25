'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter, useSearchParams } from 'next/navigation';
import { getBlogPosts, getBlogCategories } from '@/lib/api';
import { BookOpen, Clock, Eye, Sparkles, RefreshCw } from 'lucide-react';
import type { BlogPost, Category } from '@/lib/types';

/* ── Skeleton card ── */
function CardSkeleton() {
  return (
    <div className="craft-card overflow-hidden animate-pulse">
      <div className="h-44 skeleton" />
      <div className="p-5 space-y-3">
        <div className="h-3 skeleton w-24" />
        <div className="h-4 skeleton w-3/4" />
        <div className="h-3 skeleton w-full" />
        <div className="h-3 skeleton w-2/3" />
      </div>
    </div>
  );
}

function BlogContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const category = searchParams.get('category') || '';
  const search = searchParams.get('search') || '';

  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setIsError(false);
    try {
      const [postsRes, catsRes] = await Promise.all([
        getBlogPosts({ category: category || undefined, search: search || undefined }),
        getBlogCategories(),
      ]);
      setPosts(postsRes.posts);
      setCategories(catsRes);
    } catch (err) {
      console.error('Failed to load blog data:', err);
      setIsError(true);
    } finally {
      setIsLoading(false);
    }
  }, [category, search]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleCategoryChange = (slug: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (slug) params.set('category', slug);
    else params.delete('category');
    router.push(`/blog?${params.toString()}`);
  };

  /* ── Error state ── */
  if (isError) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-24 text-center space-y-4">
        <p className="text-rose-400 font-semibold">Failed to load content. Check your API connection.</p>
        <button
          onClick={loadData}
          className="inline-flex items-center gap-2 active-press bg-sky-500 hover:bg-sky-400 text-white px-6 py-2.5 rounded-xl text-sm font-bold transition-colors"
        >
          <RefreshCw className="w-4 h-4" aria-hidden="true" /> Retry
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-14 space-y-10">

      {/* ── Header ── */}
      <div className="text-center space-y-4 max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-1.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5" aria-hidden="true" /> Engineering &amp; Architecture
        </div>
        <h1 className="text-4xl sm:text-5xl font-black text-white tracking-[-0.03em]">
          Technical Blog &amp; Deep Dives
        </h1>
        <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
          Comprehensive guides covering V8 internals, Next.js&nbsp;15, React&nbsp;19 Server Components, Django Ninja, and PostgreSQL optimisation.
        </p>
      </div>

      {/* ── Category pills ── */}
      <div
        className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none"
        role="navigation"
        aria-label="Filter by category"
      >
        <button
          onClick={() => handleCategoryChange('')}
          className={`active-press px-4 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition-all ${
            !category
              ? 'bg-sky-500 text-white shadow-lg shadow-sky-500/25'
              : 'bg-[var(--surface-card)] border border-slate-800 text-slate-400 hover:text-white'
          }`}
          aria-current={!category ? 'true' : undefined}
        >
          All Topics ({categories.length})
        </button>
        {categories.map((c) => (
          <button
            key={c.slug}
            onClick={() => handleCategoryChange(c.slug)}
            className={`active-press px-4 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition-all flex items-center gap-1.5 ${
              category === c.slug
                ? 'bg-sky-500 text-white shadow-lg shadow-sky-500/25'
                : 'bg-[var(--surface-card)] border border-slate-800 text-slate-400 hover:text-white'
            }`}
            aria-current={category === c.slug ? 'true' : undefined}
          >
            <span aria-hidden="true">{c.icon}</span> {c.name}
            {c.posts_count !== undefined && <span className="opacity-60">({c.posts_count})</span>}
          </button>
        ))}
      </div>

      {/* ── Posts grid ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)
          : posts.length === 0
          ? (
              <div className="col-span-3 text-center py-20 space-y-3">
                <p className="text-slate-400 text-sm">No posts found for this filter.</p>
                <button
                  onClick={() => handleCategoryChange('')}
                  className="text-xs text-sky-400 hover:text-sky-300 underline underline-offset-2"
                >
                  Clear filter
                </button>
              </div>
            )
          : posts.map((post) => (
              <Link
                key={post.id}
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
                      loading="lazy"
                    />
                  </div>
                )}
                <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span className="text-sky-400 font-bold">{post.category?.name}</span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" aria-hidden="true" /> {post.read_time_minutes} min
                      </span>
                    </div>
                    <h2 className="font-bold text-white group-hover:text-sky-400 transition-colors text-sm leading-snug line-clamp-2">
                      {post.title}
                    </h2>
                    <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed">{post.excerpt}</p>
                  </div>
                  <div className="pt-3 border-t border-slate-800/70 text-xs text-slate-400 flex items-center justify-between">
                    <span>{post.author_name}</span>
                    <span className="flex items-center gap-1 text-slate-500">
                      <Eye className="w-3 h-3" aria-hidden="true" /> {post.views_count}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
      </div>
    </div>
  );
}

export default function BlogIndexPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-7xl mx-auto px-4 py-14">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="craft-card overflow-hidden animate-pulse">
                <div className="h-44 skeleton" />
                <div className="p-5 space-y-3">
                  <div className="h-3 skeleton w-24" />
                  <div className="h-4 skeleton w-3/4" />
                </div>
              </div>
            ))}
          </div>
        </div>
      }
    >
      <BlogContent />
    </Suspense>
  );
}
