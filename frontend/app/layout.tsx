// frontend/app/layout.tsx
import type { Metadata } from "next";
import Image from "next/image";
import "./globals.css";

export const metadata: Metadata = {
  title: "NutriParse Reader",
  description: "Extract allergens & nutrition facts from food PDFs.",
};

const BADGE = process.env.NEXT_PUBLIC_APP_BADGE; // e.g. "v0.2 • Demo" (optional)

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        {/* HEADER */}
        <header
          role="banner"
          className="sticky top-0 z-40 border-b border-slate-800/80 bg-slate-900/90 backdrop-blur supports-[backdrop-filter]:bg-slate-900/70"
        >
          <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
            {/* Brand */}
            <a href="/" className="flex items-center gap-3 text-slate-100 hover:text-white">
                <Image
                  src="/logo.png"
                  alt="NutriParse logo"
                  width={28}
                  height={28}
                  priority
                  className="h-7 w-auto"
                />
                <div className="flex items-baseline gap-2">
                  <span className="font-semibold tracking-tight">
                    NutriParse Reader
                  </span>
                  {/* Optional badge via env; remove or leave empty to hide */}
                  {BADGE ? (
                    <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-xs font-medium text-emerald-200">
                      {BADGE}
                    </span>
                  ) : null}
                </div>
              </a>

              {/* GitHub link */}
              <a
                href="https://github.com/amiltonkoxi/nutriparse-reader"
                target="_blank"
                rel="noreferrer noopener"
                aria-label="View project on GitHub"
                className="inline-flex items-center gap-2 rounded-xl border border-slate-700/70 px-4 py-2 text-sm font-medium text-slate-100 transition hover:bg-slate-800/70 active:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50"
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                  className="opacity-80"
                >
                  <path
                    fill="currentColor"
                    d="M12 .5a12 12 0 0 0-3.79 23.4c.6.11.82-.26.82-.58c0-.29-.01-1.06-.02-2.08c-3.34.73-4.04-1.61-4.04-1.61c-.55-1.39-1.35-1.76-1.35-1.76c-1.1-.75.09-.74.09-.74c1.22.09 1.86 1.25 1.86 1.25c1.08 1.85 2.84 1.32 3.53 1.01c.11-.78.42-1.32.76-1.63c-2.66-.3-5.47-1.33-5.47-5.9c0-1.3.46-2.36 1.22-3.19c-.12-.3-.53-1.52.12-3.17c0 0 1.01-.32 3.3 1.22c.96-.27 1.98-.4 3-.41c1.02.01 2.04.14 3 .41c2.29-1.54 3.3-1.22 3.3-1.22c.65 1.65.24 2.87.12 3.17c.76.83 1.22 1.88 1.22 3.19c0 4.58-2.81 5.59-5.49 5.89c.43.37.81 1.1.81 2.22c0 1.6-.01 2.88-.01 3.27c0 .32.22.7.82.58A12 12 0 0 0 12 .5"
                  />
                </svg>
                <span>GitHub →</span>
              </a>
            </div>
          </header>

        {/* MAIN */}
        <main role="main" className="mx-auto max-w-6xl px-4 py-8 text-slate-200">
          {children}
        </main>

        {/* FOOTER */}
        <footer role="contentinfo" className="border-t border-slate-800/80 bg-slate-950">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5 text-sm text-slate-400">
            <span>© 2025 NutriParse Reader — All rights reserved.</span>
            <span className="text-slate-500">Built with ❤️ using FastAPI + Next.js</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
