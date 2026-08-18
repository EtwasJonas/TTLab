import type { Metadata } from "next";
import "./globals.css";
import { LanguageProvider } from "../lib/LanguageContext";
import LanguageSwitcher from "../components/LanguageSwitcher";

export const metadata: Metadata = {
  title: "TTLab - Table Tennis Intelligence",
  description: "AI-powered table tennis video analysis",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <LanguageProvider>
          <nav className="border-b border-white/10 bg-[#0a0e17]/80 backdrop-blur-xl sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 py-5 flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-black tracking-tight text-white"><span className="text-pink-400">●</span> TTLab</h1>
                <p className="text-xs uppercase tracking-[0.25em] text-slate-500">Table tennis intelligence</p>
              </div>
              <div className="flex items-center gap-3">
                <LanguageSwitcher />
                <span className="hidden sm:block rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs text-emerald-300">LOCAL • PRIVATE</span>
              </div>
            </div>
          </nav>
          <main className="max-w-7xl mx-auto px-4 py-8">
            {children}
          </main>
        </LanguageProvider>
      </body>
    </html>
  );
}
