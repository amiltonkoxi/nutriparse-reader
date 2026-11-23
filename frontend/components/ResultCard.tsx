"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { ScrollArea } from "./ui/scroll-area";
import { ClipboardCopy, Check } from "lucide-react";

import type { AllergenEntry, AllergenStatus, ApiResponse, NutrientValue } from "@/lib/types";

type ApiLike = Partial<ApiResponse> & {
  allergens?: Record<string, AllergenEntry>;
};

const cx = (...c: Array<string | false | undefined>) => c.filter(Boolean).join(" ");

const STATUS_STYLES: Record<AllergenStatus, string> = {
  contains: "bg-rose-600 text-white",
  traces: "bg-amber-500 text-white",
  absent: "bg-emerald-600 text-white",
  unknown: "bg-slate-500 text-white",
};

const STATUS_LABEL: Record<AllergenStatus, string> = {
  contains: "CONTAINS",
  traces: "MAY CONTAIN",
  absent: "ABSENT",
  unknown: "NO EVIDENCE",
};

const BASIS_LABEL: Record<string, string> = {
  ingredients: "ingredient list",
  statement: "allergen statement",
  table_flags: "allergen table",
  checkbox: "tick box",
  grid: "+/- grid",
  layout_table: "table column",
  global_statement: "\"no allergens\" statement",
  implicit_declaration: "not in the declared list",
  not_food: "non-food document",
};

const TILE_COLORS: Record<string, string> = {
  Energy: "bg-emerald-600 text-white",
  Fat: "bg-rose-600 text-white",
  "Sat. Fat": "bg-rose-500 text-white",
  Carbs: "bg-orange-600 text-white",
  Sugar: "bg-pink-600 text-white",
  Protein: "bg-violet-600 text-white",
  Salt: "bg-cyan-600 text-white",
  Water: "bg-sky-600 text-white",
  Collagen: "bg-indigo-500 text-white",
};

/* ------------ Copy JSON helper; toast is anchored to the trigger button ------------ */
function CopyJsonButton({ json }: { json: any }) {
  const [copied, setCopied] = useState(false);
  const text = JSON.stringify(json, null, 2);
  const disabled = !text || text.trim().length === 0;

  async function onClick() {
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(text);
      } else if (typeof document !== "undefined") {
        const ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
      }
    } finally {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    }
  }

  return (
    <div className="relative inline-block">
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        className={cx(
          "inline-flex items-center gap-1.5 rounded-md border border-indigo-500 px-3 py-1.5 text-xs font-semibold",
          "bg-indigo-600 text-white shadow-sm hover:bg-indigo-500 active:bg-indigo-700",
          "focus:outline-none focus:ring-2 focus:ring-indigo-400/60 focus:ring-offset-2",
          "disabled:opacity-60 disabled:cursor-not-allowed"
        )}
        aria-label="Copy JSON"
        title="Copy JSON"
      >
        <ClipboardCopy className="h-4 w-4" />
        Copy JSON
      </button>

      {copied && (
        <div className="absolute -bottom-9 right-0 rounded-md bg-emerald-600 text-white px-2 py-1 text-xs shadow-md">
          <span className="inline-flex items-center gap-1">
            <Check className="h-4 w-4" />
            Copied
          </span>
        </div>
      )}
    </div>
  );
}

/* ---------------- Main Card ---------------- */
export default function ResultCard({ data }: { data?: ApiLike | null }) {
  const [activeTab, setActiveTab] = useState<"table" | "json" | "preview">("table");

  const meta = data?.meta;
  const allergens = data?.allergens;
  const nutrition = data?.nutrition_per_100g;
  const notes = (data?.diagnostics?.notes ?? []).filter((n): n is string => Boolean(n && n.trim().length));

  if (!data || !meta || !allergens || !nutrition) {
    return (
      <div className="rounded border border-slate-700 bg-slate-900 p-4 text-sm text-slate-200">
        No data yet. Upload a PDF and click <b>Process</b>.
      </div>
    );
  }

  const energyParts: string[] = [];
  const kjDisplay = fmtUnit(nutrition.energy_kJ, "kJ");
  if (kjDisplay) energyParts.push(kjDisplay);
  const kcalDisplay = fmtUnit(nutrition.energy_kcal, "kcal");
  if (kcalDisplay) energyParts.push(kcalDisplay);
  const energyDisplay = energyParts.length ? energyParts.join(" · ") : "—";

  const saltValue = fmtUnit(nutrition.salt_g, "g");
  let saltDisplay = saltValue ?? "—";
  if (!saltValue && nutrition.sodium_mg != null) {
    if (typeof nutrition.sodium_mg === "number") {
      saltDisplay = `${(nutrition.sodium_mg * 2.54 / 1000).toFixed(2)} g`;
    } else if (typeof nutrition.sodium_mg === "string" && nutrition.sodium_mg.trim().length > 0) {
      saltDisplay = `${nutrition.sodium_mg} mg Na`;
    }
  }

  const tiles = [
    { label: "Energy", value: energyDisplay },
    { label: "Fat", value: fmtG(nutrition.fat_g) },
    { label: "Carbs", value: fmtG(nutrition.carbohydrate_g) },
    { label: "Sugar", value: fmtG(nutrition.sugars_g) },
    { label: "Protein", value: fmtG(nutrition.protein_g) },
    { label: "Salt", value: saltDisplay },
  ];
  if (nutrition.saturated_fat_g != null && !(typeof nutrition.saturated_fat_g === "string" && !nutrition.saturated_fat_g.trim())) {
    tiles.splice(2, 0, { label: "Sat. Fat", value: fmtG(nutrition.saturated_fat_g) });
  }
  if (nutrition.water_g != null && !(typeof nutrition.water_g === "string" && !nutrition.water_g.trim())) {
    tiles.push({ label: "Water", value: fmtG(nutrition.water_g) });
  }
  if (nutrition.collagen_g != null && !(typeof nutrition.collagen_g === "string" && !nutrition.collagen_g.trim())) {
    tiles.push({ label: "Collagen", value: fmtG(nutrition.collagen_g) });
  }

  const coverage = meta.allergen_coverage ?? 0;
  const coveragePct = Math.round(coverage * 100);
  const evidenced = Math.round(coverage * 14);
  const modeLabel =
    meta.extraction_mode === "ocr" ? "Scanned (OCR)" : meta.extraction_mode === "mixed" ? "Mixed (text + OCR)" : "Digital text";
  const warnings = data.diagnostics?.warnings ?? [];

  return (
    <Card className="rounded-2xl border border-slate-700 bg-slate-900/80 shadow-sm transition hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <CardTitle className="text-lg sm:text-xl text-slate-100">
              Extraction Results
            </CardTitle>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-300">
              <span className="mr-2 truncate">
                File: {meta.source_file ?? "—"}
              </span>
              <span className="inline-block rounded border border-slate-600 bg-slate-800 px-2 py-0.5 text-slate-200">
                {modeLabel}
              </span>
              <span className="inline-block rounded border border-violet-500 bg-violet-700 px-2 py-0.5 text-white"
                title="Allergens whose status is backed by text in the document">
                Evidence: {evidenced}/14 allergens
              </span>
              {meta.pages ? (
                <span className="inline-block rounded border border-slate-600 bg-slate-800 px-2 py-0.5 text-slate-200">
                  {meta.pages} {meta.pages === 1 ? "page" : "pages"}
                </span>
              ) : null}
              {meta.needs_review && (
                <span className="inline-block rounded border border-amber-400 bg-amber-500 px-2 py-0.5 font-semibold text-slate-900">
                  Needs review
                </span>
              )}
            </div>
          </div>

          <div className="shrink-0">
            <CopyJsonButton json={data} />
          </div>
        </div>

        {/* progress */}
        <div className="mt-3 h-2 w-full rounded bg-slate-700">
          <div
            className={cx(
              "h-2 rounded bg-emerald-500 transition-all",
              coveragePct >= 99 && "bg-emerald-600",
              coveragePct < 50 && "bg-amber-500"
            )}
            style={{ width: `${Math.max(0, Math.min(100, coveragePct))}%` }}
          />
        </div>
      </CardHeader>

      <CardContent>
        {/* --- TABS: always visible + high contrast --- */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="w-full">
          <TabsList className="inline-flex gap-1 rounded-lg border border-slate-700 bg-slate-900/80 p-1 text-slate-200 shadow-sm">
            <TabsTrigger
              value="table"
              className="
                rounded-md px-3 py-1 text-sm font-medium outline-none transition
                hover:text-white focus-visible:ring-2 focus-visible:ring-white/40
                data-[state=active]:bg-slate-800 data-[state=active]:text-white
              "
            >
              Summary
            </TabsTrigger>

            <TabsTrigger
              value="json"
              className="
                rounded-md px-3 py-1 text-sm font-medium outline-none transition
                hover:text-white focus-visible:ring-2 focus-visible:ring-white/40
                data-[state=active]:bg-slate-800 data-[state=active]:text-white
              "
            >
              JSON
            </TabsTrigger>

            <TabsTrigger
              value="preview"
              disabled={!data?.diagnostics?.raw_text_preview}
              className="
                rounded-md px-3 py-1 text-sm font-medium outline-none transition
                hover:text-white focus-visible:ring-2 focus-visible:ring-white/40
                data-[state=active]:bg-slate-800 data-[state=active]:text-white
                disabled:opacity-50 disabled:cursor-not-allowed
              "
            >
              PREVIEW
            </TabsTrigger>
          </TabsList>

          {/* SUMMARY */}
          <TabsContent value="table" className="space-y-8 pt-4">
            <section>
              <h3 className="mb-3 text-sm font-semibold text-slate-100">
                Allergens
              </h3>
              {Object.keys(allergens).length ? (
                <div className="overflow-hidden rounded-xl border border-slate-700">
                  <table className="w-full text-left text-xs text-slate-200">
                    <thead className="bg-slate-800 text-[11px] uppercase tracking-wide text-slate-400">
                      <tr>
                        <th className="px-3 py-2">Allergen</th>
                        <th className="px-3 py-2">Status</th>
                        <th className="hidden px-3 py-2 sm:table-cell">Evidence from the document</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(allergens).map(([k, v]) => {
                        const st = (v?.status ?? "unknown") as AllergenStatus;
                        return (
                          <tr key={k} className="border-t border-slate-800 align-top">
                            <td className="px-3 py-2 font-medium capitalize">{k.replace(/_/g, " ")}</td>
                            <td className="px-3 py-2">
                              <span className={cx("inline-block rounded-full px-2.5 py-0.5 text-[10px] font-bold", STATUS_STYLES[st])}>
                                {STATUS_LABEL[st]}
                              </span>
                              {v?.conflict && (
                                <span className="ml-1 inline-block rounded-full bg-amber-400 px-2 py-0.5 text-[10px] font-bold text-slate-900"
                                  title="The document contradicts itself; the safer status was kept">
                                  CONFLICT
                                </span>
                              )}
                            </td>
                            <td className="hidden px-3 py-2 text-slate-300 sm:table-cell">
                              {v?.evidence ? (
                                <>
                                  <span className="italic">&ldquo;{v.evidence}&rdquo;</span>
                                  <span className="ml-1 text-slate-500">
                                    ({BASIS_LABEL[v.basis ?? ""] ?? v.basis}{v.page ? `, p. ${v.page}` : ""})
                                  </span>
                                </>
                              ) : (
                                <span className="text-slate-500">Not mentioned. Check manually.</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-xs text-slate-200">
                  No allergen entries found in this document.
                </div>
              )}
              {warnings.length > 0 && (
                <ul className="mt-3 space-y-1 rounded-xl border border-amber-500/40 bg-amber-500/10 p-3 text-xs text-amber-100">
                  {warnings.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              )}
          </section>

          <section className="space-y-4">
              <h3 className="text-sm font-semibold text-slate-100">
                Nutrition (per 100g)
              </h3>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
                {tiles.map((n) => (
                  <div
                    key={n.label}
                    className={cx(
                      "rounded-xl border-2 py-4 px-3 text-center shadow-md",
                      TILE_COLORS[n.label] ?? "bg-slate-800 text-slate-100"
                    )}
                  >
                    <p className="text-[11px] font-medium">{n.label}</p>
                    <p className="mt-1 text-2xl font-extrabold">{n.value}</p>
                  </div>
                ))}
              </div>

              {notes.length > 0 && (
                <div className="rounded-xl border border-slate-700 bg-slate-800/70 p-3 text-xs text-slate-200">
                  {notes.map((note, idx) => (
                    <p key={idx} className="leading-relaxed">{note}</p>
                  ))}
                </div>
              )}

            </section>
          </TabsContent>

          {/* JSON */}
          <TabsContent value="json" className="pt-4">
            <ScrollArea className="h-60 sm:h-80 rounded border border-slate-700 bg-[#0d1117] p-3 text-[#c9d1d9]">
              <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed select-text">
                {JSON.stringify(data, null, 2)}
              </pre>
            </ScrollArea>
          </TabsContent>

          {/* PREVIEW */}
          <TabsContent value="preview" className="pt-4">
            {data?.diagnostics?.raw_text_preview ? (
              <ScrollArea className="h-60 sm:h-80 rounded border border-slate-700 bg-[#0d1117] p-3 text-[#c9d1d9]">
                <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed select-text">
                  {data.diagnostics.raw_text_preview}
                </pre>
              </ScrollArea>
            ) : (
              <p className="text-sm text-slate-400">No preview available.</p>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

/* utils */
function fmtG(v: NutrientValue | undefined) {
  return fmtUnit(v, "g") ?? "—";
}

function fmtUnit(value: NutrientValue | undefined, unit: string): string | null {
  if (typeof value === "number") {
    const formatted = Number.isInteger(value) ? value.toString() : value.toFixed(2).replace(/\.00$/, "");
    return `${formatted} ${unit}`;
  }
  if (typeof value === "string" && value.trim().length > 0) {
    return `${value} ${unit}`;
  }
  return null;
}
