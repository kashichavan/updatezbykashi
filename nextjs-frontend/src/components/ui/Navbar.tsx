'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BookOpen, Code, Zap, ExternalLink, Menu, X } from 'lucide-react';
import { useState, useEffect } from 'react';

export function Navbar() {
  const pathname = usePathname();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 10);
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { href: '/learn/javascript', label: 'JS Masterclass', icon: Zap },
    { href: '/blog', label: 'Tech Blog', icon: BookOpen },
    {
      href: 'http://127.0.0.1:8000/api/v1/docs',
      label: 'OpenAPI Docs',
      icon: ExternalLink,
      external: true
    },
  ];

  const isActive = (href: string) => {
    if (href === '/learn/javascript') return pathname.startsWith('/learn/javascript');
    if (href === '/blog') return pathname.startsWith('/blog');
    return false;
  };

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      isScrolled
        ? 'bg-[#070b14]/95 backdrop-blur-md border-b border-sky-500/15 shadow-lg shadow-sky-500/5'
        : 'bg-transparent'
    }`}>
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link
          href="/"
          className="flex items-center gap-2 group focus-visible:ring-2 focus-visible:ring-sky-500/50 rounded-lg px-2 py-1"
          aria-label="Kashii DevAcademy Home"
        >
          <span className="text-xl animate-glow">⚡</span>
          <span className="font-extrabold text-lg text-white tracking-tight hidden sm:block">
            Kashii<span className="text-sky-400">DevAcademy</span>
          </span>
          <span className="font-extrabold text-lg text-white tracking-tight sm:hidden">KDA</span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-1" role="navigation" aria-label="Main navigation">
          {navLinks.map(({ href, label, icon: Icon, external }) => (
            <a
              key={href}
              href={href}
              target={external ? '_blank' : undefined}
              rel={external ? 'noopener noreferrer' : undefined}
              className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-semibold transition-all ${
                isActive(href)
                  ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
              }`}
              aria-current={isActive(href) ? 'page' : undefined}
            >
              <Icon className="w-4 h-4" aria-hidden="true" />
              <span>{label}</span>
            </a>
          ))}
        </nav>

        {/* Mobile Menu Button */}
        <button
          className="md:hidden p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/50 focus-visible:ring-2 focus-visible:ring-sky-500/50"
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          aria-expanded={isMobileOpen}
          aria-controls="mobile-menu"
          aria-label={isMobileOpen ? 'Close menu' : 'Open menu'}
        >
          {isMobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        {/* CTA Button - Desktop */}
        <div className="hidden md:flex items-center gap-3">
          <Link
            href="/learn/javascript"
            className="bg-gradient-to-r from-sky-500 via-blue-500 to-indigo-500 hover:from-sky-400 hover:via-blue-400 hover:to-indigo-400 text-white text-xs font-bold px-5 py-2.5 rounded-xl shadow-lg shadow-sky-500/25 hover:shadow-xl transition-all duration-300 flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-sky-500/50"
          >
            <Zap className="w-3.5 h-3.5" aria-hidden="true" />
            Start Learning
          </Link>
        </div>

        {/* Mobile Menu */}
        {isMobileOpen && (
          <div id="mobile-menu" className="md:hidden fixed inset-0 z-40 bg-[#070b14]/98 backdrop-blur-xl flex flex-col items-center justify-start pt-20 gap-6 animate-fade-in-up">
            <nav className="flex flex-col items-center gap-4 w-full max-w-sm px-4" role="navigation" aria-label="Mobile navigation">
              {navLinks.map(({ href, label, icon: Icon, external }) => (
                <a
                  key={href}
                  href={href}
                  target={external ? '_blank' : undefined}
                  rel={external ? 'noopener noreferrer' : undefined}
                  onClick={() => setIsMobileOpen(false)}
                  className={`flex items-center justify-center gap-3 px-4 py-3 rounded-xl text-base font-semibold transition-all w-full ${
                    isActive(href)
                      ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                  }`}
                  aria-current={isActive(href) ? 'page' : undefined}
                >
                  <Icon className="w-5 h-5" aria-hidden="true" />
                  <span>{label}</span>
                </a>
              ))}
            </nav>
            <Link
              href="/learn/javascript"
              onClick={() => setIsMobileOpen(false)}
              className="bg-gradient-to-r from-sky-500 via-blue-500 to-indigo-500 text-white font-bold px-6 py-3 rounded-xl shadow-lg shadow-sky-500/25 w-full max-w-sm text-center focus-visible:ring-2 focus-visible:ring-sky-500/50"
            >
              Start Learning →
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}