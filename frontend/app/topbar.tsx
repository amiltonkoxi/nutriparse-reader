"use client";

export default function TopBar() {
  return (
    <header className="sticky top-0 z-40 border-b bg-white/90 backdrop-blur supports-[backdrop-filter]:bg-white/70">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <img src="/logo.png" alt="NutriParse Logo" className="h-7 w-auto" />
          <div className="flex items-baseline gap-2">
            <span className="font-semibold tracking-tight">NutriParse Reader</span>
            <span className="rounded bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
              v0.2 • Demo
            </span>
          </div>
        </div>

        <a
          href="https://github.com/amiltonkoxi/nutriparse-reader"
          target="_blank"
          rel="noreferrer noopener"
          className="inline-flex items-center gap-2 rounded-xl border border-slate-300/80 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 active:bg-slate-100 focus-visible:ring-2 focus-visible:ring-emerald-500/50"
        >
          {/* GitHub icon */}
          <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" className="opacity-80">
            <path
              fill="currentColor"
              d="M12 .5a12 12 0 0 0-3.79 23.4c.6.11.82-.26.82-.58c0-.29-.01-1.06-.02-2.08c-3.34.73-4.04-1.61-4.04-1.61c-.55-1.39-1.35-1.76-1.35-1.76c-1.1-.75.09-.74.09-.74c1.22.09 1.86 1.25 1.86 1.25c1.08 1.85 2.84 1.32 3.53 1.01c.11-.78.42-1.32.76-1.63c-2.66-.3-5.47-1.33-5.47-5.9c0-1.3.46-2.36 1.22-3.19c-.12-.3-.53-1.52.12-3.17c0 0 1.01-.32 3.3 1.22c.96-.27 1.98-.4 3-.41c1.02.01 2.04.14 3 .41c2.29-1.54 3.3-1.22 3.3-1.22c.65 1.65.24 2.87.12 3.17c.76.83 1.22 1.88 1.22 3.19c0 4.58-2.81 5.59-5.49 5.89c.43.37.81 1.1.81 2.22c0 1.6-.01 2.88-.01 3.27c0 .32.22.7.82.58A12 12 0 0 0 12 .5"
            />
          </svg>
          <span>GitHub →</span>
        </a>
      </div>
    </header>
  );
}
