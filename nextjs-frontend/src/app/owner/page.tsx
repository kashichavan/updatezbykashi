'use client';

import Link from 'next/link';
import { useState, useCallback } from 'react';
import { Search, Filter, Zap, BookOpen, RefreshCw, ExternalLink } from 'lucide-react';
import { getOwnerJobs, getOwnerGroups, autoOrganizeGroups } from '@/lib/api';
import type { OwnerJob } from '@/lib/types';

const API_DOCS_URL =
  process.env.NEXT_PUBLIC_API_DOCS_URL || 'http://localhost:8000/api/v1/docs';

const CATEGORIES = [
  { id: '1', name: 'Web Dev',  slug: 'web-development', icon: '💻' },
  { id: '2', name: 'DevOps',   slug: 'devops',          icon: '⚙️' },
  { id: '3', name: 'Mobile',   slug: 'mobile',          icon: '📱' },
  { id: '4', name: 'Data',     slug: 'data',            icon: '📊' },
];

const EXP_OPTIONS = [
  { value: 'ALL',        label: 'All Experience Levels' },
  { value: 'FRESHER',    label: 'Freshers (0–1 yr)' },
  { value: 'EXPERIENCED',label: 'Experienced (1–5+ yrs)' },
  { value: 'INTERNSHIP', label: 'Internships' },
];

const EXP_ICONS: Record<string, string> = {
  FRESHER:    '🎓',
  EXPERIENCED:'💼',
  INTERNSHIP: '🏫',
};

export default function OwnerDashboard() {
  const [searchQuery, setSearchQuery]   = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [expFilter, setExpFilter]       = useState('ALL');
  const [jobs, setJobs]                 = useState<OwnerJob[]>([]);
  const [isFetching, setIsFetching]     = useState(false);
  const [fetchError, setFetchError]     = useState<string | null>(null);
  const [organizeMsg, setOrganizeMsg]   = useState<string | null>(null);
  const [isOrganizing, setIsOrganizing] = useState(false);

  /* ── Load jobs from API ── */
  const loadJobs = useCallback(async () => {
    setIsFetching(true);
    setFetchError(null);
    try {
      const res = await getOwnerJobs({
        search:     searchQuery || undefined,
        category:   categoryFilter || undefined,
        experience: (expFilter as any) || undefined,
        page_size:  12,
      });
      setJobs(res.jobs);
    } catch (err: unknown) {
      setFetchError(err instanceof Error ? err.message : 'Failed to fetch jobs.');
    } finally {
      setIsFetching(false);
    }
  }, [searchQuery, categoryFilter, expFilter]);

  /* ── Auto-organize ── */
  const handleOrganize = useCallback(async () => {
    setIsOrganizing(true);
    setOrganizeMsg(null);
    try {
      const res = await autoOrganizeGroups();
      setOrganizeMsg(`✅ ${res.message} (${res.groups_created} groups · ${res.jobs_organized} jobs)`);
      await loadJobs();
    } catch (err: unknown) {
      setOrganizeMsg(`❌ ${err instanceof Error ? err.message : 'Auto-organize failed.'}`);
    } finally {
      setIsOrganizing(false);
    }
  }, [loadJobs]);

  return (
    <div className="min-h-screen bg-[var(--background)] text-white">

      {/* ── Page header ── */}
      <div
        className="border-b border-slate-800/60"
        style={{
          background: 'radial-gradient(120% 60% at 50% 0%, rgba(56,189,248,0.06) 0%, var(--surface-card) 100%)',
          boxShadow: 'inset 0 -1px 0 rgba(255,255,255,0.04)',
        }}
      >
        <div className="max-w-7xl mx-auto px-4 py-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black text-white tracking-tight">Owner Studio</h1>
            <p className="text-sm text-slate-400 mt-1">Manage your hiring pipeline and job postings</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={loadJobs}
              disabled={isFetching}
              className="active-press flex items-center gap-2 text-xs font-bold px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} aria-hidden="true" />
              {isFetching ? 'Loading…' : 'Load Jobs'}
            </button>
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 py-8 space-y-8">

        {/* ── Filters ── */}
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" aria-hidden="true" />
            <input
              type="text"
              placeholder="Search jobs, companies, locations…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && loadJobs()}
              className="w-full pl-9 pr-4 py-2.5 bg-[var(--surface-card)] text-slate-300 placeholder:text-slate-600 rounded-xl border border-slate-800/70 focus:ring-2 focus:ring-sky-500/40 focus:border-sky-500/40 outline-none transition-all text-sm"
              style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.04)' }}
            />
          </div>

          {/* Category */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="py-2.5 px-3 bg-[var(--surface-card)] text-slate-300 rounded-xl border border-slate-800/70 focus:ring-2 focus:ring-sky-500/40 outline-none transition-all text-sm sm:w-48"
            style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.04)' }}
          >
            <option value="">All Categories</option>
            {CATEGORIES.map((cat) => (
              <option key={cat.id} value={cat.slug}>{cat.icon} {cat.name}</option>
            ))}
          </select>

          {/* Experience */}
          <div className="relative sm:w-52">
            <select
              value={expFilter}
              onChange={(e) => setExpFilter(e.target.value)}
              className="w-full py-2.5 pl-3 pr-8 bg-[var(--surface-card)] text-slate-300 rounded-xl border border-slate-800/70 focus:ring-2 focus:ring-sky-500/40 outline-none transition-all text-sm appearance-none"
              style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.04)' }}
            >
              {EXP_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
            <Filter className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" aria-hidden="true" />
          </div>
        </div>

        {/* ── Organize message ── */}
        {organizeMsg && (
          <div className={`text-xs font-bold px-4 py-3 rounded-xl border ${
            organizeMsg.startsWith('✅')
              ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-950/40 border-rose-500/30 text-rose-300'
          }`}>
            {organizeMsg}
          </div>
        )}

        {/* ── Fetch error ── */}
        {fetchError && (
          <div className="text-xs font-bold px-4 py-3 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300">
            {fetchError}
          </div>
        )}

        {/* ── Jobs grid ── */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {isFetching ? (
            Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="craft-card p-6 animate-pulse space-y-3">
                <div className="h-4 skeleton w-3/4" />
                <div className="h-3 skeleton w-1/2" />
                <div className="h-3 skeleton w-full" />
              </div>
            ))
          ) : jobs.length > 0 ? (
            jobs.map((job) => (
              <div
                key={job.id}
                className="craft-card p-5 space-y-3 flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-bold text-white line-clamp-1">{job.title}</h3>
                      <span className="text-xs text-sky-400 font-medium">{job.company_name}</span>
                    </div>
                    <span className="text-[10px] text-slate-500 whitespace-nowrap shrink-0 mt-0.5">
                      {job.job_type}
                    </span>
                  </div>
                  {job.description && (
                    <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">{job.description}</p>
                  )}
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {job.skills?.slice(0, 3).map((s) => (
                      <span key={s} className="text-[10px] bg-slate-800 border border-slate-700 text-slate-400 px-2 py-0.5 rounded-full">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-xs">
                  <span className="inline-flex items-center gap-1 bg-emerald-500/15 text-emerald-400 px-2 py-0.5 rounded-full font-semibold">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    {job.status}
                  </span>
                  <span className="text-slate-500">{job.location}</span>
                </div>
              </div>
            ))
          ) : (
            <>
              {/* Prompt to load */}
              <div className="col-span-1 md:col-span-2 lg:col-span-3 text-center py-16 craft-card border-dashed space-y-3">
                <div className="text-3xl" aria-hidden="true">📋</div>
                <p className="text-slate-400 text-sm">
                  {fetchError ? 'Could not load jobs.' : 'Click "Load Jobs" to fetch from the API.'}
                </p>
                <button
                  onClick={loadJobs}
                  className="active-press text-xs text-sky-400 hover:text-sky-300 underline underline-offset-2"
                >
                  Load Jobs →
                </button>
              </div>
            </>
          )}
        </div>

        {/* ── Experience segregation cards ── */}
        <div className="craft-card p-6 space-y-5">
          <h3 className="text-base font-bold text-white">Experience Tier Overview</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {EXP_OPTIONS.filter((e) => e.value !== 'ALL').map((exp) => (
              <button
                key={exp.value}
                onClick={() => { setExpFilter(exp.value); loadJobs(); }}
                className={`active-press p-4 rounded-xl border text-left transition-all ${
                  expFilter === exp.value
                    ? 'border-sky-500/50 bg-sky-500/10'
                    : 'border-slate-800/60 bg-[var(--surface-input)] hover:border-slate-600'
                }`}
                style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.04)' }}
              >
                <div className="text-2xl mb-2" aria-hidden="true">{EXP_ICONS[exp.value] ?? '💼'}</div>
                <div className="font-bold text-white text-sm">{exp.label}</div>
                <div className="text-xs text-slate-400 mt-0.5">Filter jobs by this level</div>
              </button>
            ))}
          </div>
        </div>

        {/* ── Auto-organize CTA ── */}
        <button
          onClick={handleOrganize}
          disabled={isOrganizing}
          className="active-press w-full bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 disabled:opacity-50 text-white text-sm font-bold px-6 py-3.5 rounded-xl shadow-lg shadow-sky-500/25 transition-all flex items-center justify-center gap-2"
          style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2)' }}
        >
          <Zap className="w-4 h-4" aria-hidden="true" />
          {isOrganizing ? 'Organising…' : 'Auto-Organize & Segregate Jobs'}
        </button>
      </main>

      {/* ── Bottom nav ── */}
      <div className="border-t border-slate-800/60 py-6 mt-8">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm">
          <Link href="/" className="text-slate-400 hover:text-sky-400 transition-colors active-press">
            ← Back to Home
          </Link>
          <div className="flex items-center gap-6">
            <a
              href={API_DOCS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="active-press text-emerald-400 hover:text-emerald-300 transition-colors flex items-center gap-1"
            >
              <ExternalLink className="w-3.5 h-3.5" aria-hidden="true" /> API Docs
            </a>
            <Link href="/blog" className="text-sky-400 hover:text-sky-300 transition-colors active-press">Tech Blog</Link>
            <Link href="/learn/javascript" className="text-slate-300 hover:text-white transition-colors active-press">JS Masterclass</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
