import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TTLab - Tischtennis Analyse",
  description: "KI-gestützte Tischtennis-Videoanalyse",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de">
      <body className="antialiased">
        <nav className="border-b border-white/10 bg-[#0a0e17]/80 backdrop-blur-xl">
          <div className="max-w-7xl mx-auto px-4 py-5 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-black tracking-tight text-white"><span className="text-pink-400">●</span> TTLab</h1>
              <p className="text-xs uppercase tracking-[0.25em] text-slate-500">Table tennis intelligence</p>
            </div>
            <span className="hidden sm:block rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs text-emerald-300">LOCAL • PRIVATE</span>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
