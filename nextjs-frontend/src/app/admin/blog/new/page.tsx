'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Sparkles, Send, Eye, FileText, Image as ImageIcon } from 'lucide-react';

export default function NextAdminNewBlogPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [excerpt, setExcerpt] = useState('');
  const [content, setContent] = useState('');
  const [coverUrl, setCoverUrl] = useState('');
  const [tagsStr, setTagsStr] = useState('');
  const [isFeatured, setIsFeatured] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !content) {
      alert('Title and content are required!');
      return;
    }

    setIsPublishing(true);
    setStatusMsg('Publishing to Django Ninja API...');

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
      const tags = tagsStr.split(',').map((t) => t.trim()).filter(Boolean);

      const res = await fetch(`${apiUrl}/blog/posts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          excerpt: excerpt || title,
          content,
          cover_image_url: coverUrl || 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=1200',
          tags,
          is_featured: isFeatured,
          is_published: true,
        }),
      });

      if (!res.ok) throw new Error('API request failed');
      const data = await res.json();

      setStatusMsg('✨ Article published successfully!');
      setTimeout(() => {
        router.push(`/blog/${data.slug}`);
      }, 1000);
    } catch (err: any) {
      setStatusMsg(`❌ Error: ${err.message}`);
    } finally {
      setIsPublishing(false);
    }
  };

  const wordCount = content.trim().split(/\s+/).filter(Boolean).length;
  const readMins = Math.max(1, Math.ceil(wordCount / 200));

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 space-y-8">
      <div className="flex items-center justify-between">
        <Link href="/blog" className="text-xs text-slate-400 hover:text-sky-400 flex items-center gap-1 font-bold">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Blog
        </Link>
        <span className="bg-sky-500/10 text-sky-400 border border-sky-500/30 px-3 py-1 rounded-full text-xs font-bold font-mono">
          ⚡ Next.js + Django Ninja API Admin
        </span>
      </div>

      <header className="space-y-1">
        <h1 className="text-3xl font-black text-white">Create Technical Article</h1>
        <p className="text-xs text-slate-400">Post engineering deep dives directly to your live Django backend.</p>
      </header>

      {statusMsg && (
        <div className="p-3 bg-sky-950/60 border border-sky-500/40 rounded-xl text-xs font-bold text-sky-300">
          {statusMsg}
        </div>
      )}

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-5 bg-[#0d1527] border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="space-y-1.5">
            <label className="text-xs font-bold uppercase text-slate-400">Article Title *</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Deep Dive into V8 Engine & JIT Compiler"
              className="w-full bg-[#080e1a] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-sky-400 outline-none"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold uppercase text-slate-400">Summary / Excerpt (150-250 chars) *</label>
            <textarea
              rows={2}
              required
              value={excerpt}
              onChange={(e) => setExcerpt(e.target.value)}
              placeholder="Concise breakdown shown on cards..."
              className="w-full bg-[#080e1a] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-sky-400 outline-none"
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <label className="font-bold uppercase">Article Content (Markdown / HTML) *</label>
              <span className="font-mono text-sky-400 font-bold">⏱️ ~{readMins} min read ({wordCount} words)</span>
            </div>
            <textarea
              rows={14}
              required
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="## 1. Overview&#10;&#10;Write your technical deep dive here...&#10;&#10;```javascript&#10;let count = 10;&#10;```"
              className="w-full bg-[#080e1a] border border-slate-700/80 rounded-xl p-4 font-mono text-xs text-slate-200 focus:border-sky-400 outline-none leading-relaxed"
            />
          </div>
        </div>

        {/* Sidebar Settings */}
        <div className="space-y-6">
          <div className="bg-[#0d1527] border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl">
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-sky-400" /> Publication Settings
            </h3>

            <label className="flex items-center gap-2 text-xs font-semibold text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={isFeatured}
                onChange={(e) => setIsFeatured(e.target.checked)}
                className="accent-amber-500 rounded"
              />
              <span>⭐ Mark as Featured Hero Post</span>
            </label>

            <div className="space-y-1.5">
              <label className="text-[11px] font-bold uppercase text-slate-400">Tags (comma-separated)</label>
              <input
                type="text"
                value={tagsStr}
                onChange={(e) => setTagsStr(e.target.value)}
                placeholder="javascript, v8, nodejs"
                className="w-full bg-[#080e1a] border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:border-sky-400 outline-none"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-[11px] font-bold uppercase text-slate-400">Cover Image URL</label>
              <input
                type="url"
                value={coverUrl}
                onChange={(e) => setCoverUrl(e.target.value)}
                placeholder="https://images.unsplash.com/..."
                className="w-full bg-[#080e1a] border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:border-sky-400 outline-none"
              />
              {coverUrl && (
                <img src={coverUrl} alt="Preview" className="w-full h-28 object-cover rounded-lg mt-2 border border-slate-800" />
              )}
            </div>

            <button
              type="submit"
              disabled={isPublishing}
              className="w-full bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-bold py-3 rounded-xl text-xs flex items-center justify-center gap-2 shadow-lg shadow-sky-500/25 transition-all disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              {isPublishing ? 'Publishing...' : 'Publish Article Live'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
