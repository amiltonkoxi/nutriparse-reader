"use client";

import { useState } from "react";
import axios from "axios";

type Mode = "table" | "json";

export default function HomePage() {
  const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [tab, setTab] = useState<Mode>("table");

  async function handleUpload() {
    if (!file) return;
    setLoading(true);
    setResult(null);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const { data } = await axios.post(`${API}/api/extract`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(data);
    } catch (e: any) {
      setResult({ error: e?.message || "Upload failed" });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-white to-slate-50">
      <div className="max-w-4xl mx-auto px-4 py-10">
        {/* Hero */}
        <header className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
            Food PDF Extractor
          </h1>
          <p className="text-slate-600 mt-2">
            Upload a food product PDF (text or scanned). We’ll extract allergens and nutrition.
          </p>
        </header>

        {/* Card */}
        <section className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              aria-label="Select PDF file"
              className="block w-full text-sm text-slate-700 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 focus:outline-none"
            />
            <button
              onClick={handleUpload}
              disabled={!file || loading}
              className="px-4 py-2 rounded-lg bg-blue-600 text-white font-medium disabled:opacity-50 hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2"
            >
              {loading ? "Uploading..." : "Upload"}
            </button>
          </div>

          <div className="mt-6">
            {!result && !loading && (
              <div className="text-sm text-slate-500">
                No results yet. Choose a PDF and click Upload.
              </div>
            )}

            {result && (
              <>
                {/* Tabs */}
                <div className="inline-flex rounded-lg border border-slate-200 p-1 mb-4 bg-slate-50">
                  <button
                    onClick={() => setTab("table")}
                    className={`px-3 py-1.5 text-sm rounded-md ${
                      tab === "table" ? "bg-white shadow" : "text-slate-600"
                    }`}
                  >
                    Table
                  </button>
                  <button
                    onClick={() => setTab("json")}
                    className={`px-3 py-1.5 text-sm rounded-md ${
                      tab === "json" ? "bg-white shadow" : "text-slate-600"
                    }`}
                  >
                    JSON
                  </button>
                </div>

                {tab === "table" ? (
                  <TableView data={result} />
                ) : (
                  <pre className="bg-slate-900 text-slate-100 text-sm rounded-lg p-4 overflow-auto">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                )}
              </>
            )}

            {"error" in (result || {}) && (
              <p className="text-rose-600 text-sm mt-2">{(result as any).error}</p>
            )}
          </div>
        </section>

        <footer className="mt-10 text-xs text-slate-500">
          © {new Date().getFullYear()} Amilton Koxi — Demo.
        </footer>
      </div>
    </main>
  );
}

function Chip({ label, tone }: { label: string; tone: "red" | "amber" | "green" | "gray" }) {
  const map: Record<string, string> = {
    red: "bg-rose-50 text-rose-700 border-rose-200",
    amber: "bg-amber-50 text-amber-700 border-amber-200",
    green: "bg-emerald-50 text-emerald-700 border-emerald-200",
    gray: "bg-slate-100 text-slate-700 border-slate-200",
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs border ${map[tone]}`}>
      {label}
    </span>
  );
}

function toneFromStatus(s?: string): "red" | "amber" | "green" | "gray" {
  if (s === "contains") return "red";
  if (s === "traces") return "amber";
  if (s === "absent") return "green";
  return "gray";
}

function Row({ label, value }: { label: string; value: any }) {
  return (
    <tr className="bg-white">
      <td className="px-4 py-2 text-sm text-slate-600 w-52">{label}</td>
      <td className="px-4 py-2 text-sm font-medium text-slate-900">{value ?? "—"}</td>
    </tr>
  );
}

function fmt(v: any) {
  return v ?? "—";
}

function TableView({ data }: { data: any }) {
  const a = data?.allergens || {};
  const n = data?.nutrition || {};
  const m = data?.meta || {};
  const chips: [string, any][] = [
    ["gluten", a.gluten?.status],
    ["egg", a.egg?.status],
    ["crustaceans", a.crustaceans?.status],
    ["fish", a.fish?.status],
    ["peanut", a.peanut?.status],
    ["soy", a.soy?.status],
    ["milk", a.milk?.status],
    ["tree_nuts", a.tree_nuts?.status],
    ["celery", a.celery?.status],
    ["mustard", a.mustard?.status],
  ];

  return (
    <div className="space-y-6">
      {/* Badges */}
      <div className="flex flex-wrap gap-2">
        <Chip label={`Mode: ${m.extraction_mode ?? "—"}`} tone="gray" />
        <Chip label={`Confidence: ${m.confidence ?? 0}`} tone="gray" />
      </div>

      {/* Allergens */}
      <div>
        <h3 className="font-semibold text-slate-900 mb-2">Allergens</h3>
        <div className="flex flex-wrap gap-2">
          {chips.map(([k, s]) => (
            <Chip key={k} label={`${k}: ${s ?? "unknown"}`} tone={toneFromStatus(s)} />
          ))}
        </div>
      </div>

      {/* Nutrition */}
      <div>
        <h3 className="font-semibold text-slate-900 mb-2">Nutrition (per 100g)</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full border border-slate-200 rounded-lg overflow-hidden">
            <tbody className="divide-y divide-slate-200">
              <Row label="Energy" value={`${n?.energy?.kJ ?? "—"} kJ / ${n?.energy?.kcal ?? "—"} kcal`} />
              <Row label="Fat (g)" value={fmt(n?.fat_g)} />
              <Row label="Carbohydrate (g)" value={fmt(n?.carbohydrate_g)} />
              <Row label="Sugar (g)" value={fmt(n?.sugar_g)} />
              <Row label="Protein (g)" value={fmt(n?.protein_g)} />
              <Row label="Salt (g)" value={fmt(n?.salt_g)} />
              <Row label="Sodium (g)" value={fmt(n?.sodium_g)} />
              <Row label="Notes" value={n?.notes ?? "—"} />
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
