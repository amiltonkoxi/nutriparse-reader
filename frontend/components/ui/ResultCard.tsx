"use client";

import React from "react";

type AllergenKey =
  | "gluten" | "egg" | "crustaceans" | "fish" | "peanut"
  | "soy" | "milk" | "tree_nuts" | "celery" | "mustard";

type AllergenStatus = "contains" | "traces" | "absent" | "unknown";

type ExtractResponse = {
  meta?: {
    product_name?: string | null;
    source_file?: string;
    extraction_mode?: "text" | "ocr";
    serving_basis?: string | null;
    languages?: string[];
    confidence?: number | null;
  };
  allergens?: Record<AllergenKey, { status: AllergenStatus; evidence?: string | null }>;
  nutrition?: {
    energy?: { kJ?: number | null; kcal?: number | null };
    fat_g?: number | null;
    carbohydrate_g?: number | null;
    sugar_g?: number | null;
    protein_g?: number | null;
    salt_g?: number | null;
    sodium_g?: number | null;
    notes?: string | null;
  };
  extras?: Record<string, number | null>;
  diagnostics?: {
    warnings?: string[];
    pages_scanned?: number | null;
    raw_text_preview?: string;
  };
};

function pillClasses(status: AllergenStatus) {
  const base = "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold shadow-sm";
  switch (status) {
    case "contains":
      return `${base} bg-rose-100 text-rose-700 ring-1 ring-rose-200`;
    case "traces":
      return `${base} bg-amber-100 text-amber-800 ring-1 ring-amber-200`;
    case "absent":
      return `${base} bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200`;
    default:
      return `${base} bg-slate-100 text-slate-600 ring-1 ring-slate-200`;
  }
}

function box(label: string, value: React.ReactNode) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white/80 p-4 shadow-sm">
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div className="mt-1 text-lg font-semibold text-slate-900">{value ?? "—"}</div>
    </div>
  );
}

function fmtNum(n?: number | null, unit = "") {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  const s = (Math.round((n + Number.EPSILON) * 100) / 100).toString();
  return unit ? `${s} ${unit}` : s;
}

export default function ResultCard({ data, index = 0 }: { data: ExtractResponse; index?: number }) {
  const meta = data?.meta ?? {};
  const allergens = data?.allergens ?? {} as ExtractResponse["allergens"];
  const nut = data?.nutrition ?? {};

  const file = meta.source_file ?? `Result ${index + 1}`;
  const mode = meta.extraction_mode === "ocr" ? "OCR mode" : "Text mode";
  const conf = meta.confidence != null ? Math.round((meta.confidence || 0) * 100) : null;

  // allergens order
  const order: AllergenKey[] = [
    "gluten","egg","crustaceans","fish","peanut",
    "soy","milk","tree_nuts","celery","mustard"
  ];

  const kJ = nut.energy?.kJ ?? null;
  const kcal = nut.energy?.kcal ?? null;

  return (
    <section className="rounded-3xl border border-slate-200/80 bg-white/95 p-5 shadow-md ring-1 ring-black/5">
      <header className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate text-sm text-slate-500">File: {file}</div>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
              {mode}
            </span>
            {conf !== null && (
              <span className="inline-flex items-center rounded-lg bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                Confidence: {conf}%
              </span>
            )}
          </div>
        </div>

        <button
          onClick={() => navigator.clipboard.writeText(JSON.stringify(data, null, 2))}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-300/80 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50 active:scale-[0.99] focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50"
          aria-label="Copy JSON"
          type="button"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M8 7V5q0-.825.588-1.413T10 3h9q.825 0 1.413.587T21 5v9q0 .825-.587 1.413T19 16h-2v2q0 .825-.587 1.413T15 20H6q-.825 0-1.413-.587T4 18v-9q0-.825.587-1.413T6 7zm2 0h7v7h-2q-.825 0-1.413.588T13 16v2H6V9q0-.425.288-.712T7 8h2z"/></svg>
          Copy JSON
        </button>
      </header>

      {/* Allergens */}
      <div>
        <h3 className="mb-2 text-sm font-semibold text-slate-800">Allergens</h3>
        <div className="flex flex-wrap gap-2">
          {order.map((k) => {
            const st = (allergens?.[k]?.status ?? "unknown") as AllergenStatus;
            const ev = allergens?.[k]?.evidence ?? null;
            const label = k.replace("_", " ");
            return (
              <span key={k} className={pillClasses(st)} title={ev || undefined}>
                <span className="capitalize">{label}</span>
                <span className="ml-2 rounded-full bg-white/60 px-2 py-0.5 text-[10px] font-bold tracking-wide">
                  {st.toUpperCase()}
                </span>
              </span>
            );
          })}
        </div>
      </div>

      {/* Nutrition */}
      <div className="mt-5">
        <h3 className="mb-2 text-sm font-semibold text-slate-800">Nutrition (per 100g)</h3>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
          {box("Energy", kJ !== null ? `${fmtNum(kJ)} kJ` : "— kJ")}
          {box("Fat", fmtNum(nut.fat_g, "g"))}
          {box("Carbs", fmtNum(nut.carbohydrate_g, "g"))}
          {box("Sugar", fmtNum(nut.sugar_g, "g"))}
          {box("Protein", fmtNum(nut.protein_g, "g"))}
          {box("Salt", fmtNum(nut.salt_g ?? nut.sodium_g, nut.salt_g != null ? "" : "")) /* display raw number; kcal summary lives below */}
        </div>

        <div className="mt-4 rounded-xl border border-slate-200/80 bg-slate-50 p-3 text-sm text-slate-700">
          <div className="flex items-center justify-between">
            <span className="font-medium">Energy (kcal)</span>
            <span className="font-semibold">{kcal !== null ? `${fmtNum(kcal)} kcal` : "— kcal"}</span>
          </div>
        </div>

        {nut?.notes && (
          <p className="mt-2 text-xs text-slate-500">{nut.notes}</p>
        )}
      </div>
    </section>
  );
}
