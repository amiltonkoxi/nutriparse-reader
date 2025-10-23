"use client";

/**
 * NutriParse Reader — Home Page
 *
 * - Uses <Dropzone /> for clean drag & drop / picker UI
 * - Manages queue, processing, results
 * - POSTs each file to `${API_BASE}/extract`
 * - Shows results with <ResultCard />
 */

import { useCallback, useMemo, useState } from "react";
import ResultCard from "@/components/ResultCard";
import HowItWorks from "@/components/HowItWorks";
import Dropzone from "@/components/Dropzone";

// ----------------------------------------------------------------------------
// Environment
// ----------------------------------------------------------------------------
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";
const DEFAULT_MAX = parseInt(process.env.NEXT_PUBLIC_MAX_FILES ?? "2", 10);

// ----------------------------------------------------------------------------
// Types (aligned with backend)
// ----------------------------------------------------------------------------
export type UploadResult = {
  meta: { source_file: string; extraction_mode: "text" | "ocr"; confidence: number };
  allergens: Record<string, { status: "contains" | "traces" | "absent" | "unknown"; evidence: string | null }>;
  nutrition: {
    energy: { kJ: number | null; kcal: number | null };
    fat_g: number | null;
    carbohydrate_g: number | null;
    sugar_g: number | null;
    protein_g: number | null;
    salt_g: number | null;
    sodium_g: number | null;
    notes?: string | null;
  };
  diagnostics?: { warnings?: string[]; raw_text_preview?: string };
};

export default function HomePage() {
  // ----------------------------------------------------------------------------
  // UI state
  // ----------------------------------------------------------------------------
  const [queue, setQueue] = useState<File[]>([]);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<UploadResult[]>([]);
  const baseActionBtn =
    "inline-flex h-11 items-center justify-center rounded-full px-5 text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600";
  const primaryActionBtn =
    baseActionBtn + " bg-emerald-600 text-white shadow-[0_10px_30px_-15px_rgba(16,185,129,0.8)] hover:bg-emerald-700 disabled:opacity-50 disabled:shadow-none";
  const secondaryActionBtn =
    baseActionBtn + " border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-40";

  // ----------------------------------------------------------------------------
  // Helpers
  // ----------------------------------------------------------------------------
  const MAX_FILES = useMemo(() => DEFAULT_MAX, []);
  const roomLeft = (add = 0) => Math.max(0, MAX_FILES - (queue.length + add));

  // ----------------------------------------------------------------------------
  // Queue ops
  // ----------------------------------------------------------------------------
  const addToQueue = useCallback(
    (incoming: File[]) => {
      setError(null);
      if (!incoming.length) return;

      const space = roomLeft();
      const accepted = incoming.slice(0, space);
      const rejected = incoming.length - accepted.length;

      if (accepted.length) {
        setQueue((prev) => [...prev, ...accepted]);
      }
      if (rejected > 0) setError(`Limit of ${MAX_FILES} file(s). Remove some to add more.`);
    },
    [MAX_FILES, queue.length]
  );

  const removeFromQueue = (idx: number) => {
    setQueue((prev) => prev.filter((_, i) => i !== idx));
    setError(null);
  };

  // ----------------------------------------------------------------------------
  // Processing
  // ----------------------------------------------------------------------------
  const processQueue = async () => {
    if (!queue.length || processing) return;

    setProcessing(true);
    setError(null);

    try {
      for (const file of queue) {
        const form = new FormData();
        form.append("file", file, file.name);

        const res = await fetch(`${API_BASE}/extract`, { method: "POST", body: form });
        if (!res.ok) throw new Error(`Failed to process "${file.name}".`);

        const json: UploadResult = await res.json();
        if (json?.meta && json?.allergens && json?.nutrition) {
          setResults((prev) => [json, ...prev]);
        }
      }

      setQueue([]);
    } catch (e: any) {
      setError(e?.message || "Processing error.");
    } finally {
      setProcessing(false);
    }
  };

  // ----------------------------------------------------------------------------
  // Render
  // ----------------------------------------------------------------------------
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="hero-surface absolute inset-0 blur-3xl opacity-70" aria-hidden="true" />
        <div className="relative mx-auto flex max-w-6xl flex-col items-center gap-6 px-4 py-16 text-center sm:gap-8">
          <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
            Extract Allergens &amp; Nutrition from Food PDFs
          </h1>
          <p className="mx-auto max-w-2xl text-base text-slate-600 sm:text-lg">
            Upload up to <span className="font-semibold text-emerald-700">{MAX_FILES} PDFs</span> and instantly surface the allergen list and key nutrition values for every product.
          </p>
        </div>
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent" />
      </section>

      {/* Uploader (uses Dropzone component) */}
      <section className="relative mx-auto -mt-10 max-w-6xl px-4 pb-20 sm:-mt-16">
        <div className="mx-auto max-w-4xl">
          <Dropzone onFilesSelected={addToQueue} maxFiles={MAX_FILES} />
          {error && <p className="mt-4 text-center text-sm font-medium text-rose-600">{error}</p>}
          <div className="mt-6 space-y-2 text-center text-sm text-slate-500">
            <p className="font-medium text-slate-700">
              Extracts 10 allergens · 6 nutrition facts · OCR fallback for scanned PDFs
            </p>
            <p>
              Works with unstructured tables or lists. Review results in an interactive table or copy the full JSON output.
            </p>
          </div>
        </div>

        {/* Guided steps */}
        <HowItWorks />

        {/* Queue */}
        <div className="mx-auto mb-12 mt-8 max-w-5xl space-y-5">
          {queue.length > 0 && (
            <div className="callout-glow rounded-2xl border border-emerald-100/60 p-5 shadow-[0_26px_48px_-32px_rgba(16,185,129,0.6)]">
              <div className="mb-4 flex items-center justify-between text-sm font-semibold text-slate-700">
                Queue ({queue.length}/{MAX_FILES})
                <span className="text-xs font-medium uppercase tracking-[0.25em] text-emerald-500">
                  Ready for extraction
                </span>
              </div>
              <ul className="flex flex-wrap gap-2">
                {queue.map((f, idx) => (
                  <li
                    key={idx}
                    className="flex items-center gap-2 rounded-full border border-slate-200 bg-white/80 px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm"
                  >
                    <span className="max-w-[46ch] truncate">{f.name}</span>
                    <button
                      onClick={() => removeFromQueue(idx)}
                      className="rounded-full border border-rose-200 bg-rose-50 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-[0.2em] text-rose-600 transition hover:bg-rose-100"
                      disabled={processing}
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="callout-glow flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200/80 px-5 py-4 shadow-[0_26px_48px_-32px_rgba(15,118,110,0.5)]">
            <button
              onClick={processQueue}
              disabled={processing || queue.length === 0}
              className={primaryActionBtn}
            >
              {processing ? "Processing…" : "Run Extraction"}
            </button>

            <button
              onClick={() => setQueue([])}
              disabled={processing || queue.length === 0}
              className={secondaryActionBtn}
            >
              Clear Files
            </button>

            <button
              onClick={() => setResults([])}
              disabled={processing || results.length === 0}
              className={secondaryActionBtn}
            >
              Clear Results
            </button>
          </div>
        </div>

        {/* Results */}
        {results.length > 0 && (
          <div className="mx-auto mb-20 max-w-5xl space-y-6">
            <div className="text-center">
              <h2 className="text-xl font-semibold text-slate-800">Review structured results</h2>
              <p className="mt-1 text-sm text-slate-500">
                Each card includes confidence scores, allergen flags, nutrition per 100 g, and a JSON copy option.
              </p>
            </div>
            {results
              .filter((r) => r?.meta && r?.allergens && r?.nutrition)
              .map((r, i) => <ResultCard key={i} data={r as any} />)}
          </div>
        )}
      </section>
    </div>
  );
}
