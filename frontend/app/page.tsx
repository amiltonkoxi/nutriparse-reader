"use client";

/**
 * NutriParse Reader — Home Page
 *
 * - Uses <Dropzone /> for clean drag & drop / picker UI
 * - Manages queue, processing, results
 * - POSTs each file to `${API_BASE}/extract`
 * - Shows results with <ResultCard />
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
  nutrition_per_100g: {
    energy_kJ: number | string | null;
    energy_kcal: number | string | null;
    fat_g: number | string | null;
    saturated_fat_g?: number | string | null;
    carbohydrate_g: number | string | null;
    sugars_g: number | string | null;
    protein_g: number | string | null;
    salt_g: number | string | null;
    sodium_mg: number | string | null;
    collagen_g?: number | string | null;
    water_g?: number | string | null;
  };
  diagnostics?: { warnings?: string[]; raw_text_preview?: string; nutrition_evidence?: Record<string, string | null>; notes?: string[] | null };
};

type ToastTone = "success" | "warning";
type ToastMessage = { id: string; message: string; tone: ToastTone };

export default function HomePage() {
  // ----------------------------------------------------------------------------
  // UI state
  // ----------------------------------------------------------------------------
  const [queue, setQueue] = useState<File[]>([]);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<UploadResult[]>([]);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const toastTimers = useRef<Array<ReturnType<typeof setTimeout>>>([]);
  const [showInlineStatus, setShowInlineStatus] = useState(true);
  const [pendingScroll, setPendingScroll] = useState(false);
  const resultsRef = useRef<HTMLDivElement | null>(null);
  const runButtonRef = useRef<HTMLButtonElement | null>(null);
  const baseActionBtn =
    "inline-flex h-11 items-center justify-center rounded-full px-5 text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500";
  const primaryActionBtn =
    baseActionBtn +
    " bg-emerald-600 text-white shadow-[0_10px_30px_-15px_rgba(16,185,129,0.8)] hover:bg-emerald-500 disabled:opacity-50 disabled:shadow-none";
  const secondaryActionBtn =
    baseActionBtn +
    " border border-slate-700 bg-slate-900 text-slate-100 hover:bg-slate-800 disabled:opacity-40";

  const pushToast = useCallback(
    (message: string, tone: ToastTone) => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      setToasts((prev) => [...prev, { id, message, tone }]);

      const timer = setTimeout(() => {
        setToasts((prev) => prev.filter((toast) => toast.id !== id));
        toastTimers.current = toastTimers.current.filter((handle) => handle !== timer);
      }, 3200);

      toastTimers.current.push(timer);
    },
    []
  );

  useEffect(
    () => () => {
      toastTimers.current.forEach((handle) => clearTimeout(handle));
      toastTimers.current = [];
    },
    []
  );

  // ----------------------------------------------------------------------------
  // Helpers
  // ----------------------------------------------------------------------------
  const MAX_FILES = useMemo(() => DEFAULT_MAX, []);
  const inlineStatusMessage = useMemo(() => {
    if (!showInlineStatus) return null;

    if (queue.length === 0) {
      return `Drag PDFs here or click "Select PDFs" (max ${MAX_FILES} per run).`;
    }

    if (queue.length < MAX_FILES) {
      if (queue.length === 1 && MAX_FILES === 2) {
        return "1 file selected. You can add one more.";
      }
      const remaining = MAX_FILES - queue.length;
      const filesLabel = queue.length === 1 ? "1 file selected." : `${queue.length} files selected.`;
      const moreLabel = remaining === 1 ? "one more" : `${remaining} more`;
      return `${filesLabel} You can add ${moreLabel}.`;
    }

    const displayCount = Math.min(queue.length, MAX_FILES);
    return `${displayCount} files selected. Click "Run Extraction" to process and review results below.`;
  }, [MAX_FILES, queue.length, showInlineStatus]);

  const highlightRun = queue.length === MAX_FILES && !processing;
  const runButtonClass = highlightRun
    ? primaryActionBtn + " animate-pulse ring-2 ring-emerald-400 ring-offset-2 ring-offset-slate-900"
    : primaryActionBtn;

  useEffect(() => {
    if (highlightRun && runButtonRef.current) {
      runButtonRef.current.focus({ preventScroll: true });
    }
  }, [highlightRun]);

  useEffect(() => {
    if (pendingScroll && !processing && results.length > 0) {
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      setPendingScroll(false);
    }
  }, [pendingScroll, processing, results.length]);

  // ----------------------------------------------------------------------------
  // Queue ops
  // ----------------------------------------------------------------------------
  const addToQueue = useCallback(
    (incoming: File[]) => {
      setError(null);
      if (!incoming.length) return;

      const available = Math.max(0, MAX_FILES - queue.length);
      const accepted = available > 0 ? incoming.slice(0, available) : [];
      const rejected = incoming.length - accepted.length;

      if (accepted.length) {
        const nextCount = queue.length + accepted.length;
        setQueue((prev) => [...prev, ...accepted]);
        setShowInlineStatus(true);

        if (nextCount >= MAX_FILES) {
          pushToast("✔ Two files ready. Click \"Run Extraction\".", "success");
        } else if (nextCount === 1) {
          pushToast("✔ File added. You can select one more.", "success");
        } else {
          const remaining = MAX_FILES - nextCount;
          const moreLabel = remaining === 1 ? "one more." : `${remaining} more.`;
          pushToast(`✔ ${nextCount} files selected. You can add ${moreLabel}`, "success");
        }
      }
      if (rejected > 0) {
        setError(`Limit of ${MAX_FILES} file(s). Remove some to add more.`);
        pushToast(`⚠ Limit of ${MAX_FILES} PDFs per run.`, "warning");
      }
    },
    [MAX_FILES, queue.length, pushToast]
  );

  const removeFromQueue = (idx: number) => {
    setQueue((prev) => {
      const next = prev.filter((_, i) => i !== idx);
      if (next.length < MAX_FILES) {
        setShowInlineStatus(true);
      }
      return next;
    });
    setError(null);
  };

  const clearQueue = () => {
    setQueue([]);
    setError(null);
    setShowInlineStatus(true);
  };

  // ----------------------------------------------------------------------------
  // Processing
  // ----------------------------------------------------------------------------
  const processQueue = async () => {
    if (!queue.length || processing) return;

    setProcessing(true);
    setError(null);
    setShowInlineStatus(false);

    let producedResult = false;

    try {
      for (const file of queue) {
        const form = new FormData();
        form.append("file", file, file.name);

        const res = await fetch(`${API_BASE}/extract`, { method: "POST", body: form });
        if (!res.ok) throw new Error(`Failed to process "${file.name}".`);

        const json: UploadResult = await res.json();
        if (json?.meta && json?.allergens && json?.nutrition_per_100g) {
          setResults((prev) => [json, ...prev]);
          producedResult = true;
        }
      }

      setQueue([]);
    } catch (e: any) {
      setError(e?.message || "Processing error.");
    } finally {
      setProcessing(false);
      if (producedResult) {
        setPendingScroll(true);
      }
    }
  };

  // ----------------------------------------------------------------------------
  // Render
  // ----------------------------------------------------------------------------
  return (
    <div className="min-h-screen">
      <div className="pointer-events-none fixed bottom-6 right-6 z-50 flex w-full max-w-xs flex-col gap-3 sm:max-w-sm">
        {toasts.map((toast) => {
          const toneClasses =
            toast.tone === "success"
              ? "bg-emerald-600 text-white border border-emerald-500 shadow-[0_20px_45px_-20px_rgba(16,185,129,0.6)]"
              : "bg-amber-500 text-white border border-amber-400 shadow-[0_20px_45px_-20px_rgba(245,158,11,0.55)]";
          return (
            <div
              key={toast.id}
              className={`pointer-events-auto rounded-xl px-4 py-3 text-sm font-semibold ${toneClasses}`}
              role="status"
              aria-live="assertive"
            >
              {toast.message}
            </div>
          );
        })}
      </div>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="hero-surface pointer-events-none absolute inset-0 -z-10 blur-3xl opacity-60" aria-hidden="true" />
        <div className="relative z-10 mx-auto flex max-w-6xl flex-col items-center gap-6 px-4 py-16 text-center sm:gap-8">
          <h1 className="text-4xl font-extrabold tracking-tight text-slate-100 sm:text-5xl">
            Extract Allergens &amp; Nutrition from Food PDFs
          </h1>
          <p className="mx-auto max-w-2xl text-base text-slate-300 sm:text-lg">
            Upload up to <span className="font-semibold text-emerald-300">{MAX_FILES} PDFs</span> and instantly surface the allergen list and key nutrition values for every product.
          </p>
        </div>
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent" />
      </section>

      {/* Uploader (uses Dropzone component) */}
      <section className="relative mx-auto -mt-10 max-w-6xl px-4 pb-20 sm:-mt-16">
        <div className="mx-auto max-w-4xl">
          <Dropzone
            onFilesSelected={addToQueue}
            maxFiles={MAX_FILES}
            selectedCount={queue.length}
            statusMessage={inlineStatusMessage}
            instructionsVisible={showInlineStatus}
          />
          {error && <p className="mt-4 text-center text-sm font-medium text-rose-400">{error}</p>}
          <div className="mt-6 space-y-2 text-center text-sm text-slate-300">
            <p className="font-semibold text-slate-300">
              Extracts 10 allergens · 6 nutrition facts · OCR fallback for scanned PDFs
            </p>
            <p className="text-slate-400">
              Works with unstructured tables or lists. Review results in an interactive table or copy the full JSON output.
            </p>
          </div>
        </div>

        {/* Queue */}
        <div className="mx-auto mb-12 mt-8 max-w-5xl space-y-5">
          {queue.length > 0 && (
            <div className="callout-glow rounded-2xl border border-emerald-500/20 p-5 shadow-[0_26px_48px_-32px_rgba(16,185,129,0.6)]">
              <div className="mb-4 flex items-center justify-between text-sm font-semibold text-slate-200">
                Queue ({queue.length}/{MAX_FILES})
                <span className="text-xs font-medium uppercase tracking-[0.25em] text-emerald-300">
                  Ready for extraction
                </span>
              </div>
              <ul className="flex flex-wrap gap-2">
                {queue.map((f, idx) => (
                  <li
                    key={idx}
                    className="flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900/80 px-3 py-1.5 text-xs font-medium text-slate-200 shadow-sm"
                  >
                    <span className="max-w-[46ch] truncate">{f.name}</span>
                    <button
                      onClick={() => removeFromQueue(idx)}
                      className="rounded-full border border-rose-500/40 bg-rose-500/20 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-[0.2em] text-rose-200 transition hover:bg-rose-500/30"
                      disabled={processing}
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="callout-glow flex flex-wrap items-center gap-3 rounded-2xl border border-slate-700/60 px-5 py-4 shadow-[0_26px_48px_-32px_rgba(15,118,110,0.5)]">
            <button
              ref={runButtonRef}
              onClick={processQueue}
              disabled={processing || queue.length === 0}
              className={runButtonClass}
            >
              {processing ? "Processing…" : "Run Extraction"}
            </button>

            <button
              onClick={clearQueue}
              disabled={processing || queue.length === 0}
              className={`${secondaryActionBtn} disabled:bg-slate-800 disabled:text-slate-600`}
            >
              Clear Files
            </button>

            <button
              onClick={() => setResults([])}
              disabled={processing || results.length === 0}
              className={`${secondaryActionBtn} disabled:bg-slate-800 disabled:text-slate-600`}
            >
              Clear Results
            </button>
          </div>
        </div>

        {/* Guided steps */}
        <HowItWorks />

        {/* Results */}
        {results.length > 0 && (
          <div ref={resultsRef} className="mx-auto mb-20 max-w-5xl space-y-6">
            <div className="text-center">
              <h2 className="text-xl font-semibold text-slate-100">Review structured results</h2>
              <p className="mt-1 text-sm text-slate-300">
                Each card includes confidence scores, allergen flags, nutrition per 100 g, and a JSON copy option.
              </p>
            </div>
            {results
              .filter((r) => r?.meta && r?.allergens && r?.nutrition_per_100g)
              .map((r, i) => <ResultCard key={i} data={r as any} />)}
          </div>
        )}
      </section>
    </div>
  );
}
