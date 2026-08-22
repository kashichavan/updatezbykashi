import Link from 'next/link';

export function Footer() {
  return (
    <footer className="border-t border-slate-800 bg-[#050811] py-12 text-slate-400 text-sm">
      <div className="max-w-7xl mx-auto px-4 grid grid-cols-1 md:grid-cols-4 gap-8">
        <div className="md:col-span-2 space-y-3">
          <div className="flex items-center gap-2 font-bold text-white text-lg">
            <span>⚡</span> Kashii DevAcademy &amp; Tech Blog
          </div>
          <p className="text-xs text-slate-400 max-w-sm leading-relaxed">
            High-converting interactive developer education powered by Django Ninja OpenAPI, Python V8 Execution Tracers, and Next.js React 19 UI.
          </p>
        </div>

        <div>
          <h4 className="font-semibold text-white mb-3 text-xs uppercase tracking-wider">Curriculum</h4>
          <ul className="space-y-2 text-xs">
            <li><Link href="/learn/javascript" className="hover:text-sky-400">JavaScript ES6+ Masterclass</Link></li>
            <li><Link href="/blog?category=javascript-engines" className="hover:text-sky-400">V8 Engine Internals</Link></li>
            <li><Link href="/blog?category=backend-saas" className="hover:text-sky-400">Django Ninja &amp; APIs</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="font-semibold text-white mb-3 text-xs uppercase tracking-wider">Developer Resources</h4>
          <ul className="space-y-2 text-xs">
            <li><a href="http://127.0.0.1:8000/api/v1/docs" target="_blank" className="hover:text-emerald-400">Swagger API Docs</a></li>
            <li><a href="http://127.0.0.1:8000/api/v1/openapi.json" target="_blank" className="hover:text-sky-400">OpenAPI Spec (JSON)</a></li>
            <li><Link href="/blog" className="hover:text-sky-400">Engineering Blog</Link></li>
          </ul>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 mt-8 pt-6 border-t border-slate-800/60 text-xs text-center text-slate-500">
        &copy; {new Date().getFullYear()} Kashii DevAcademy. All rights reserved. Built with Django Ninja &amp; Next.js.
      </div>
    </footer>
  );
}
