import Link from 'next/link';
import { Github, Twitter, Book, Heart } from 'lucide-react';

const API_DOCS_URL =
  process.env.NEXT_PUBLIC_API_DOCS_URL || 'http://localhost:8000/api/v1/docs';
const API_SPEC_URL =
  process.env.NEXT_PUBLIC_API_SPEC_URL || 'http://localhost:8000/api/v1/openapi.json';

const footerLinks = {
  curriculum: [
    { label: 'JavaScript ES6+ Masterclass', href: '/learn/javascript' },
    { label: 'V8 Engine Internals', href: '/blog?category=javascript-engines' },
    { label: 'Django Ninja & APIs', href: '/blog?category=backend-saas' },
  ],
  resources: [
    { label: 'Swagger API Docs', href: API_DOCS_URL, external: true },
    { label: 'OpenAPI Spec (JSON)', href: API_SPEC_URL, external: true },
    { label: 'Engineering Blog', href: '/blog', external: false },
  ],
};

const social = [
  { href: 'https://github.com', icon: Github, label: 'GitHub' },
  { href: 'https://twitter.com', icon: Twitter, label: 'Twitter' },
  { href: '/blog', icon: Book, label: 'Blog' },
];

export function Footer() {
  return (
    <footer className="border-t border-slate-800/60 bg-[var(--background-footer)] py-16 text-slate-400 text-sm relative overflow-hidden">
      {/* Top accent line */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-2/3 h-px bg-gradient-to-r from-transparent via-sky-500/25 to-transparent" />

      <div className="max-w-7xl mx-auto px-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10">

        {/* Brand column */}
        <div className="lg:col-span-2 space-y-4">
          <Link href="/" className="flex items-center gap-2 group w-fit">
            <span className="text-2xl animate-glow" aria-hidden="true">⚡</span>
            <span className="font-extrabold text-lg text-white tracking-tight">
              Kashii<span className="text-sky-400">Updatez</span>
            </span>
          </Link>
          <p className="text-xs text-slate-400 max-w-sm leading-relaxed">
            Kashii Updates (also known as Kashii Updatez) provides verified daily student requirements, off-campus drives, &amp; internships. All postings remain active for exactly 7 days to guarantee 100% fresh opportunities.
          </p>
          <div className="flex items-center gap-3 pt-2">
            {social.map(({ href, icon: Icon, label }) => (
              <a
                key={label}
                href={href}
                target={href.startsWith('http') ? '_blank' : undefined}
                rel={href.startsWith('http') ? 'noopener noreferrer' : undefined}
                className="p-2 rounded-lg bg-slate-800/50 text-slate-400 hover:text-sky-400 hover:bg-sky-500/10 transition-all duration-200 focus-visible:ring-2 focus-visible:ring-sky-500/50 active-press"
                aria-label={label}
              >
                <Icon className="w-4 h-4" aria-hidden="true" />
              </a>
            ))}
          </div>
        </div>

        {/* Curriculum column */}
        <div>
          <h4 className="font-semibold text-white mb-4 text-xs uppercase tracking-wider">Curriculum</h4>
          <ul className="space-y-3 text-xs">
            {footerLinks.curriculum.map((link) => (
              <li key={link.label}>
                <Link href={link.href} className="hover:text-sky-400 transition-colors flex items-center gap-1.5 group">
                  <span className="text-slate-600 group-hover:text-sky-500 transition-colors">→</span>
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Resources column */}
        <div>
          <h4 className="font-semibold text-white mb-4 text-xs uppercase tracking-wider">Developer Resources</h4>
          <ul className="space-y-3 text-xs">
            {footerLinks.resources.map((link) => (
              <li key={link.label}>
                {link.external ? (
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-emerald-400 transition-colors flex items-center gap-1.5 group"
                  >
                    <span className="text-slate-600 group-hover:text-emerald-500 transition-colors">→</span>
                    {link.label}
                  </a>
                ) : (
                  <Link href={link.href} className="hover:text-emerald-400 transition-colors flex items-center gap-1.5 group">
                    <span className="text-slate-600 group-hover:text-emerald-500 transition-colors">→</span>
                    {link.label}
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="max-w-7xl mx-auto px-4 mt-12 pt-8 border-t border-slate-800/60 text-xs text-center text-slate-500">
        <p className="flex items-center justify-center gap-1.5 flex-wrap">
          <span>© {new Date().getFullYear()} Kashii DevAcademy.</span>
          <span className="hidden sm:inline">All rights reserved.</span>
          <span className="text-slate-700">·</span>
          <span className="flex items-center gap-1">
            Built with <Heart className="w-3 h-3 text-rose-400" aria-hidden="true" /> Django Ninja &amp; Next.js
          </span>
        </p>
      </div>
    </footer>
  );
}
