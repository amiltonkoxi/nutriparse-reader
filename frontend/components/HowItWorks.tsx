import React from "react";

// components/HowItWorks.tsx
export default function HowItWorks() {
  const steps = [
    {
      n: 1,
      t: "Upload",
      d: "Add up to 2 PDF files (drag & drop or select).",
    },
    {
      n: 2,
      t: "Extract",
      d: "Checks 10 allergens and nutrients per 100 g",
    },
    {
      n: 3,
      t: "Review",
      d: "View results in table or JSON and copy if needed.",
    },
  ];

  return (
    <div className="mx-auto mt-14 grid max-w-5xl grid-cols-1 gap-4 sm:grid-cols-3">
      {steps.map((s) => (
        <div
          key={s.n}
          className="callout-glow relative overflow-hidden rounded-2xl border border-emerald-500/30 p-5 shadow-[0_18px_40px_-28px_rgba(16,185,129,0.65)]"
        >
          <span className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-emerald-400/90 via-emerald-500/80 to-emerald-400/90" />
          <div className="mb-3 flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-500/20 text-xs font-semibold uppercase text-emerald-200 tracking-[0.15em]">
              {s.n}
            </span>
            <h3 className="text-base font-semibold text-slate-100">{s.t}</h3>
          </div>
          <p className="text-sm leading-relaxed text-slate-300">{s.d}</p>
        </div>
      ))}
    </div>
  );
}
