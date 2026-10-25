import type { Metadata } from 'next';
import './globals.css';
import { Navbar } from '@/components/ui/Navbar';
import { Footer } from '@/components/ui/Footer';

export const metadata: Metadata = {
  title: 'Kashii Updates — Verified Daily Student Requirements & Off-Campus Drives',
  description: 'Kashii Updates (also known as Kashii Updatez) provides verified daily student requirements, off-campus drives, & internships. All postings remain active for exactly 7 days to guarantee 100% fresh opportunities.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#070b14] text-slate-100 min-h-screen flex flex-col antialiased selection:bg-sky-500/30 selection:text-sky-200">
        <Navbar />
        <div className="flex-1">{children}</div>
        <Footer />
      </body>
    </html>
  );
}
