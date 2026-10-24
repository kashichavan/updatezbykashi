import Link from 'next/link';
import { Github, Twitter, Book, Code, Heart } from 'lucide-react';

const footerLinks = {
  curriculum: [
    { label: 'JavaScript ES6+ Masterclass', href: '/learn/javascript' },
    { label: 'V8 Engine Internals', href: '/blog?category=javascript-engines' },
    { label: 'Django Ninja & APIs', href: '/blog?category=backend-saas' },
  ],
  resources: [
    { label: 'Swagger API Docs', href: 'http://127.0.0.1:8000/api/v1/docs' },
    { label: 'OpenAPI Spec (JSON)', href: 'http://127.0.0.1:8000/api/v1/openapi.json' },
    { label: 'Engineering Blog', href: '/blog' },
  ],
};

export function Footer() {
  return (
    <footer className="border-t border-slate-800/60 bg-[#050811] py-16 text-slate-400 text-sm relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-2/3 h-px bg-gradient-to-r from-transparent via-sky-500/30 to-transparent" />

      <div className="max-w-7xl mx-auto px-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10">
        {/* Brand Column */}
        <div className="lg:col-span-2 space-y-4">
          <Link href="/" className="flex items-center gap-2 group">
            <span className="text-2xl animate-glow">⚡</span>
            <span className="font-extrabold text-lg text-white tracking-tight">
              Kashii<span className="text-sky-400">DevAcademy</span>
            </span>
          </Link>
          <p className="text-xs text-slate-400 max-w-sm leading-relaxed">
            High-converting interactive developer education powered by Django Ninja OpenAPI, Python V8 Execution Tracers, and Next.js React 19 UI.
          </p>
          <div className="flex items-center gap-3 pt-2">
            {[
              { href: 'https://github.com', icon: Github, label: 'GitHub' },
              { href: 'https://twitter.com', icon: Twitter, label: 'Twitter' },
              { href: '/blog', icon: Book, label: 'Blog' },
            ].map(({ href, icon: Icon, label }) => (
              <a
                key={label}
                href={href}
                target={href.startsWith('http') ? '_blank' : undefined}
                rel={href.startsWith('http') ? 'noopener noreferrer' : undefined}
                className="p-2 rounded-lg bg-slate-800/50 text-slate-400 hover:text-sky-400 hover:bg-sky-500/10 transition-all duration-200 focus-visible:ring-2 focus-visible:ring-sky-500/50"
                aria-label={label}
              >
                <Icon className="w-4 h-4" aria-hidden="true" />
              </a>
            ))}
          </div>
        </div>

        {/* Curriculum Column */}
        <div>
          <h4 className="font-semibold text-white mb-4 text-xs uppercase tracking-wider">Curriculum</h4>
          <ul className="space-y-3 text-xs">
            {footerLinks.curriculum.map((link) => (
              <li key={link.label}>
                <Link href={link.href} className="hover:text-sky-400 transition-colors flex items-center gap-1.5">
                  <span className="text-slate-500">→</span> {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Resources Column */}
        <div>
          <h4 className="font-semibold text-white mb-4 text-xs uppercase tracking-wider">Developer Resources</h4>
          <ul className="space-y-3 text-xs">
            {footerLinks.resources.map((link) => (
              <li key={link.label}>
                <a
                  href={link.href}
                  target={link.href.startsWith('http') ? '_blank' : undefined}
                  rel={link.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                  className="hover:text-emerald-400 transition-colors flex items-center gap-1.5"
                >
                  <span className="text-slate-500">→</span> {link.label}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 mt-12 pt-8 border-t border-slate-800/60 text-xs text-center text-slate-500">
        <p className="flex items-center justify-center gap-1.5">
          <span>&copy; {new Date().getFullYear()} Kashii DevAcademy.</span>
          <span className="hidden sm:inline">All rights reserved.</span>
          <span className="text-slate-600">·</span>
          <span className="flex items-center gap-1">
            Built with <Heart className="w-3 h-3 text-rose-400" /> Django Ninja & Next.js
          </span>
        </p>
      </div>
    </footer>
  );
}