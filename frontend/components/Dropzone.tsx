"use client";
import React, { useState, DragEvent, ChangeEvent } from "react";

interface DropzoneProps {
  onFilesSelected: (files: File[]) => void;
  maxFiles?: number;
}

export default function Dropzone({ onFilesSelected, maxFiles = 2 }: DropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files).filter(f => f.type === "application/pdf");
    onFilesSelected(files.slice(0, maxFiles));
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []).filter(f => f.type === "application/pdf");
    onFilesSelected(files.slice(0, maxFiles));
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={e => e.preventDefault()}
      onDragEnter={() => setIsDragging(true)}
      onDragLeave={() => setIsDragging(false)}
      className={`group relative mx-auto flex w-full max-w-2xl flex-col items-center justify-center space-y-5 overflow-hidden rounded-3xl border border-slate-200/80 bg-gradient-to-br from-white/90 via-white to-emerald-50/50 p-8 text-center shadow-[0_24px_56px_-34px_rgba(16,185,129,0.6)] transition-all duration-300 sm:p-10 ${
        isDragging
          ? "scale-[1.01] border-emerald-400 bg-gradient-to-br from-emerald-50/80 via-white to-emerald-50/60 shadow-[0_36px_76px_-42px_rgba(16,185,129,0.7)]"
          : "hover:border-emerald-300/80 hover:shadow-[0_30px_74px_-46px_rgba(16,185,129,0.6)]"
      }`}
    >
      <div
        className={`relative flex h-16 w-16 items-center justify-center rounded-2xl border-2 border-emerald-200/80 bg-white/95 text-emerald-500 shadow-md transition-all ${
          isDragging ? "scale-110 border-emerald-400 text-emerald-600 shadow-lg" : "group-hover:border-emerald-300"
        }`}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 48 48"
          className="h-10 w-10"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M30 4H18a4 4 0 0 0-4 4v32a4 4 0 0 0 4 4h16a4 4 0 0 0 4-4V14L30 4z" fill="currentColor" opacity=".12" />
          <path d="M30 4v10h10" />
          <path d="M18 26h4a3 3 0 0 0 0-6h-4v16m10-16v16m0-16h5a6 6 0 0 1 0 12h-5m11-12h6" />
        </svg>
        <span className="pointer-events-none absolute -bottom-2 rounded-full bg-emerald-500 px-2 py-0.5 text-[10px] font-semibold tracking-[0.25em] text-white shadow-sm">
          PDF
        </span>
      </div>
      <div className="space-y-2">
        <p className="text-lg font-semibold text-slate-800">
          Upload <span className="text-emerald-600">food label PDFs</span>
        </p>
        <p className="text-sm text-slate-500">
          Drag files into this panel or choose them below to upload up to {maxFiles} PDFs per run.
        </p>
      </div>
      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
        PDF ONLY • MAX {maxFiles} FILES
      </p>
      <label
        htmlFor="pdf-upload"
        className="mt-2 inline-flex items-center justify-center rounded-full border border-emerald-600 bg-emerald-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 hover:bg-emerald-700 active:scale-[0.98]"
      >
        Select PDFs
      </label>
      <input
        id="pdf-upload"
        type="file"
        accept="application/pdf"
        multiple
        onChange={handleChange}
        className="hidden"
      />
    </div>
  );
}
