import Link from 'next/link';

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-[#070b14]/80 border-b border-sky-500/15">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <span className="text-xl">⚡</span>
          <span className="font-extrabold text-lg text-white tracking-tight">
            Kashii<span className="text-sky-400">DevAcademy</span>
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-6 text-sm font-semibold">
          <Link href="/learn/javascript" className="text-slate-300 hover:text-sky-400 transition-colors flex items-center gap-1.5">
            <span>⚡</span> JS Masterclass
          </Link>
          <Link href="/blog" className="text-slate-300 hover:text-sky-400 transition-colors flex items-center gap-1.5">
            <span>📰</span> Tech Blog
          </Link>
          <a
            href="http://127.0.0.1:8000/api/v1/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="text-emerald-400 hover:text-emerald-300 transition-colors flex items-center gap-1.5 text-xs font-mono bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/20"
          >
            <span>📜</span> OpenAPI Docs
          </a>
        </nav>

        <div className="flex items-center gap-3">
          <Link
            href="/learn/javascript"
            className="bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white text-xs font-bold px-4 py-2 rounded-lg shadow-lg shadow-sky-500/20 transition-all"
          >
            Start Learning &rarr;
          </Link>
        </div>
      </div>
    </header>
  );
}

