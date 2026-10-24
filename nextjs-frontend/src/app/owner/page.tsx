'use client';

import Link from 'next/link';
import { useState, useEffect, useCallback } from 'react';
import { Search, Filter, Zap, BookOpen, ExternalLink } from 'lucide-react';

export default function OwnerDashboard() {
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [expFilter, setExpFilter] = useState('ALL');
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  const categories = [
    { id: '1', name: 'Web Dev', slug: 'web-development', icon: '💻' },
    { id: '2', name: 'DevOps', slug: 'devops', icon: '⚙️' },
    { id: '3', name: 'Mobile', slug: 'mobile', icon: '📱' },
    { id: '4', name: 'Data', slug: 'data', icon: '📊' },
  ];

  const expOptions = [
    { value: 'ALL', label: 'All Experience Levels' },
    { value: 'FRESHER', label: 'Freshers (0-1 Yrs)' },
    { value: 'EXPERIENCED', label: 'Experienced (1-5+ Yrs)' },
    { value: 'INTERNSHIP', label: 'Internships' },
  ];

  const filteredCategories = categoryFilter
    ? categories.filter((c) => c.slug === categoryFilter)
    : categories;

  const filteredExpOptions = expFilter === 'ALL'
    ? expOptions
    : expOptions.filter((e) => e.value === expFilter);

  const handleOrganize = async () => {
    try {
      // TODO: Implement actual auto-organize call via API
      console.log('Auto-organize triggered');
    } catch (err) {
      console.error('Auto-organize failed:', err);
    }
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-white">
      {/* Header */}
      <div className="bg-[#0d1527] border-b border-slate-800/60">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-white">Owner Studio</h1>
          <p className="text-sm text-slate-400 mt-1">Manage your hiring pipeline and job postings</p>
        </div>
      </div>
      
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="flex-1">
            <div className="relative">
              <input
                type="text"
                placeholder="Search jobs, companies, locations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full p-3 pr-10 bg-[#141c2e] text-slate-300 rounded-lg border border-slate-800/70 focus:ring-2 focus:ring-sky-500/50 focus:border-transparent transition-all"
              />
              <Search className="absolute left-3 top-3.5 w-4 h-4 text-slate-500" />
            </div>
          </div>
          
          <div className="flex-1">
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full p-3 bg-[#141c2e] text-slate-300 rounded-lg border border-slate-800/70 focus:ring-2 focus:ring-sky-500/50 focus:border-transparent transition-all"
            >
              <option value="">All Categories</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.slug}>
                  {cat.icon} {cat.name}
                </option>
              ))}
            </select>
          </div>
          
          <div className="flex-1">
            <div className="relative">
              <select
                value={expFilter}
                onChange={(e) => setExpFilter(e.target.value)}
                className="w-full p-3 bg-[#141c2e] text-slate-300 rounded-lg border border-slate-800/70 focus:ring-2 focus:ring-sky-500/50 focus:border-transparent transition-all appearance-none pr-8"
              >
                {filteredExpOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <Filter className="absolute right-3 top-3.5 w-4 h-4 text-slate-500 pointer-events-none" />
            </div>
          </div>
        </div>

        {/* Jobs Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="bg-[#0d1527] border border-slate-800/60 rounded-xl overflow-hidden shadow-sm transition-all duration-300 hover:shadow-md hover:scale-105"
            >
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-white">Senior Frontend Engineer</h3>
                    <span className="text-xs text-sky-400 font-medium">TechCorp</span>
                  </div>
                  <span className="text-xs text-slate-400">
                    Full-Time • SENIOR_LEVEL
                  </span>
                </div>
                
                <div className="text-sm text-slate-400 line-clamp-2">
                  Building modern web applications with React and Next.js. Looking for experienced engineers.
                </div>
                
                <div className="flex items-center justify-between mt-4">
                  <span className="text-xs text-slate-300">
                    <span className="bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full text-xs font-semibold">
                      🟢 ACTIVE
                    </span>
                  </span>
                  <span className="text-xs text-slate-500">
                    Oct 30, 2026
                  </span>
                </div>
              </div>
            </div>
          ))}
          
          {/* Empty state */}
          <div className="col-span-1 md:col-span-2 lg:col-span-3 text-center p-8 bg-[#0d1527] border border-dashed border-slate-800/60 rounded-xl">
            <div className="text-2xl mb-2">📋</div>
            <p className="text-slate-400">No jobs found yet. Post your first job to get started.</p>
          </div>
        </div>

        {/* Experience Segregation Bar */}
        <div className="mt-12 bg-[#0d1527] border border-slate-800/60 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Experience Segregation</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {expOptions.filter((e) => e.value !== 'ALL').map((exp) => (
              <button
                key={exp.value}
                className="p-4 rounded-xl border border-slate-800/60 bg-[#0d1527] text-left transition-all duration-200 hover:border-slate-600 hover:shadow-md"
                onClick={() => setExpFilter(exp.value)}
              >
                <div className="text-2xl mb-2">{exp.value === 'FRESHER' ? '🎓' : '💼'}</div>
                <div className="font-semibold text-white text-sm mb-1">{exp.label}</div>
                <div className="text-xs text-slate-400">
                  View segregated jobs by experience level
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Call to Action */}
        <div className="mt-12">
          <button
            onClick={handleOrganize}
            className="w-full bg-gradient-to-r from-sky-500 to-indigo-500 text-white text-sm font-medium px-6 py-3 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 focus-visible:ring-2 focus-visible:ring-sky-500/50"
          >
            <span className="flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Organize & Segregate Jobs
            </span>
          </button>
        </div>
      </main>

      {/* Footer */}
      <div className="border-t border-slate-800/60 py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <Link href="/" className="text-sm text-slate-400 hover:text-sky-400 transition-colors">
            ← Back to Home
          </Link>
          <div className="flex items-center gap-6 text-sm">
            <a href="http://127.0.0.1:8000/api/v1/docs" target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:text-emerald-300 transition-colors flex items-center gap-1">
              OpenAPI Docs
            </a>
            <Link href="/blog" className="text-sky-400 hover:text-sky-300 transition-colors">
              Tech Blog
            </Link>
            <Link href="/learn/javascript" className="text-slate-300 hover:text-white transition-colors">
              JS Masterclass
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}