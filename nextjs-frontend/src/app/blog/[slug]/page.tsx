import { notFound } from 'next/navigation';
import Link from 'next/link';
import { getBlogPostBySlug } from '@/lib/api';
import { Clock, Calendar, Eye, ArrowLeft } from 'lucide-react';

interface BlogPostPageProps {
  params: Promise<{ slug: string }>;
}

export default async function BlogPostDetailPage({ params }: BlogPostPageProps) {
  const { slug } = await params;
  const post = await getBlogPostBySlug(slug);

  if (!post) {
    notFound();
  }

  return (
    <article className="max-w-4xl mx-auto px-4 py-12 space-y-8">
      <Link
        href="/blog"
        className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-sky-400 font-bold transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back to all articles
      </Link>

      {/* Header */}
      <header className="space-y-4">
        {post.category && (
          <span className="inline-flex items-center gap-1.5 bg-sky-500/10 text-sky-400 border border-sky-500/30 px-3 py-1 rounded-full text-xs font-bold">
            {post.category.icon} {post.category.name}
          </span>
        )}
        <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight leading-tight">
          {post.title}
        </h1>

        <div className="flex flex-wrap items-center justify-between gap-4 py-4 border-y border-slate-800 text-xs text-slate-400">
          <div className="flex items-center gap-3">
            {post.author_avatar_url && (
              <img
                src={post.author_avatar_url}
                alt={post.author_name}
                className="w-9 h-9 rounded-full object-cover border border-sky-400"
              />
            )}
            <div>
              <div className="font-bold text-white">{post.author_name}</div>
              <div className="text-[11px] text-slate-400">{post.author_title}</div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" /> {post.read_time_minutes} min read
            </span>
            <span className="flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5" /> {new Date(post.published_at).toLocaleDateString()}
            </span>
            <span className="flex items-center gap-1">
              <Eye className="w-3.5 h-3.5" /> {post.views_count}
            </span>
          </div>
        </div>
      </header>

      {/* Cover Image */}
      {post.cover_image_url && (
        <div className="rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
          <img src={post.cover_image_url} alt={post.title} className="w-full max-h-[420px] object-cover" />
        </div>
      )}

      {/* Content */}
      <div
        className="prose prose-invert max-w-none text-slate-300 text-base leading-relaxed space-y-6"
        dangerouslySetInnerHTML={{ __html: post.content || '' }}
      />

      {/* Tags */}
      {post.tags && post.tags.length > 0 && (
        <div className="pt-6 border-t border-slate-800 flex flex-wrap gap-2 items-center">
          <span className="text-xs text-slate-500 font-bold">Tags:</span>
          {post.tags.map((t) => (
            <span key={t.slug} className="bg-slate-900 border border-slate-800 text-slate-400 text-xs px-2.5 py-1 rounded-md">
              #{t.name}
            </span>
          ))}
        </div>
      )}
    </article>
  );
}
