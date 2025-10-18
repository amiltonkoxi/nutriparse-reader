import "./globals.css";
import { ReactNode } from "react";
export const metadata = { title: "Food PDF Extractor", description: "Upload a food PDF and extract allergens & nutrition" };
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-white text-slate-900 antialiased">
        <header className="border-b">
          <div className="mx-auto max-w-5xl px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2"><img src="/logo.svg" alt="logo" className="h-6"/><span className="font-semibold">Food PDF Extractor</span></div>
            <a className="text-sm opacity-80 hover:opacity-100" href="https://github.com/amiltonkoxi/food-pdf-extractor" target="_blank" rel="noreferrer">GitHub</a>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
        <footer className="border-t"><div className="mx-auto max-w-5xl px-4 py-4 text-xs opacity-70">Backend: {process.env.NEXT_PUBLIC_API_URL}</div></footer>
      </body>
    </html>
  );
}
