'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BookOpen, Zap, ExternalLink, Menu, X } from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';

const API_DOCS_URL =
  process.env.NEXT_PUBLIC_API_DOCS_URL || 'http://localhost:8000/api/v1/docs';

const navLinks = [
  { href: '/learn/javascript', label: 'JS Masterclass', icon: Zap },
  { href: '/blog', label: 'Tech Blog', icon: BookOpen },
  { href: API_DOCS_URL, label: 'API Docs', icon: ExternalLink, external: true },
];

export function Navbar() {
  const pathname = usePathname();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const handleScroll = useCallback(() => setIsScrolled(window.scrollY > 10), []);

  useEffect(() => {
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  /* Close mobile menu when viewport becomes desktop-width */
  useEffect(() => {
    const onResize = () => { if (window.innerWidth >= 768) setIsMobileOpen(false); };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  /* Prevent body scroll while mobile menu is open */
  useEffect(() => {
    document.body.style.overflow = isMobileOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [isMobileOpen]);

  const isActive = useCallback(
    (href: string) => {
      if (href === '/learn/javascript') return pathname.startsWith('/learn/javascript');
      if (href === '/blog') return pathname.startsWith('/blog');
      return false;
    },
    [pathname],
  );

  const linkClass = (href: string) =>
    `flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-semibold transition-all active-press ${
      isActive(href)
        ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
        : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
    }`;

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? 'bg-[var(--background)]/95 backdrop-blur-md border-b border-sky-500/10 shadow-lg shadow-black/20'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">

        {/* ── Brand ── */}
        <Link
          href="/"
          className="flex items-center gap-2 focus-visible:ring-2 focus-visible:ring-sky-500/50 rounded-lg px-2 py-1"
          aria-label="Kashii Updates Home"
        >
          <span className="text-xl animate-glow" aria-hidden="true">⚡</span>
          <span className="font-extrabold text-lg text-white tracking-tight hidden sm:block">
            Kashii<span className="text-sky-400">Updatez</span>
          </span>
          <span className="font-extrabold text-lg text-white tracking-tight sm:hidden">Kashii</span>
        </Link>

        {/* ── Desktop nav ── */}
        <nav className="hidden md:flex items-center gap-1" role="navigation" aria-label="Main navigation">
          {navLinks.map(({ href, label, icon: Icon, external }) =>
            external ? (
              <a
                key={href}
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className={linkClass(href)}
              >
                <Icon className="w-4 h-4" aria-hidden="true" />
                <span>{label}</span>
              </a>
            ) : (
              <Link key={href} href={href} className={linkClass(href)} aria-current={isActive(href) ? 'page' : undefined}>
                <Icon className="w-4 h-4" aria-hidden="true" />
                <span>{label}</span>
              </Link>
            ),
          )}
        </nav>

        {/* ── Desktop CTA ── */}
        <div className="hidden md:flex items-center gap-3">
          <Link
            href="/learn/javascript"
            className="active-press bg-gradient-to-r from-sky-500 via-blue-500 to-indigo-500 hover:from-sky-400 hover:via-blue-400 hover:to-indigo-400 text-white text-xs font-bold px-5 py-2.5 rounded-xl shadow-lg shadow-sky-500/25 hover:shadow-sky-500/40 transition-all duration-300 flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-sky-500/50"
            style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2), 0 4px 14px -2px rgba(56,189,248,0.4)' }}
          >
            <Zap className="w-3.5 h-3.5" aria-hidden="true" />
            Start Learning
          </Link>
        </div>

        {/* ── Mobile hamburger ── */}
        <button
          className="md:hidden p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/50 focus-visible:ring-2 focus-visible:ring-sky-500/50 active-press"
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          aria-expanded={isMobileOpen}
          aria-controls="mobile-menu"
          aria-label={isMobileOpen ? 'Close menu' : 'Open menu'}
        >
          {isMobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* ── Mobile menu overlay ── */}
      {isMobileOpen && (
        <div
          id="mobile-menu"
          className="md:hidden fixed inset-0 z-40 bg-[var(--background)]/98 backdrop-blur-xl flex flex-col items-center justify-start pt-24 gap-6 animate-fade-in-up"
        >
          <nav className="flex flex-col items-center gap-3 w-full max-w-sm px-6" role="navigation" aria-label="Mobile navigation">
            {navLinks.map(({ href, label, icon: Icon, external }) =>
              external ? (
                <a
                  key={href}
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => setIsMobileOpen(false)}
                  className="flex items-center justify-center gap-3 px-4 py-3.5 rounded-xl text-base font-semibold transition-all w-full text-slate-300 hover:text-white hover:bg-slate-800/50 border border-transparent"
                >
                  <Icon className="w-5 h-5" aria-hidden="true" />
                  <span>{label}</span>
                </a>
              ) : (
                <Link
                  key={href}
                  href={href}
                  onClick={() => setIsMobileOpen(false)}
                  className={`flex items-center justify-center gap-3 px-4 py-3.5 rounded-xl text-base font-semibold transition-all w-full border ${
                    isActive(href)
                      ? 'bg-sky-500/15 text-sky-400 border-sky-500/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/50 border-transparent'
                  }`}
                  aria-current={isActive(href) ? 'page' : undefined}
                >
                  <Icon className="w-5 h-5" aria-hidden="true" />
                  <span>{label}</span>
                </Link>
              ),
            )}
          </nav>

          <Link
            href="/learn/javascript"
            onClick={() => setIsMobileOpen(false)}
            className="active-press bg-gradient-to-r from-sky-500 via-blue-500 to-indigo-500 text-white font-bold px-6 py-3.5 rounded-xl shadow-lg shadow-sky-500/25 w-full max-w-sm text-center text-sm focus-visible:ring-2 focus-visible:ring-sky-500/50"
          >
            Start Learning →
          </Link>
        </div>
      )}
    </header>
  );
}
