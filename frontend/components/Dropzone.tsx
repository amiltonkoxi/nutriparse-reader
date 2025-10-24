"use client";
import React, { useState, DragEvent, ChangeEvent, MouseEvent } from "react";

interface DropzoneProps {
  onFilesSelected: (files: File[]) => void;
  maxFiles?: number;
  selectedCount?: number;
  statusMessage?: string | null;
  instructionsVisible?: boolean;
}

export default function Dropzone({
  onFilesSelected,
  maxFiles = 2,
  selectedCount = 0,
  statusMessage,
  instructionsVisible = true,
}: DropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const limitReached = selectedCount >= maxFiles;

  const resolvedMessage = (() => {
    if (!instructionsVisible) return null;
    if (typeof statusMessage === "string") return statusMessage;

    if (selectedCount === 0) {
      return `Drag PDFs here or click "Select PDFs" (max ${maxFiles} per run).`;
    }

    if (selectedCount < maxFiles) {
      if (selectedCount === 1 && maxFiles === 2) {
        return "1 file selected. You can add one more.";
      }
      const remaining = Math.max(0, maxFiles - selectedCount);
      const moreLabel = remaining === 1 ? "one more" : `${remaining} more`;
      const filesLabel = selectedCount === 1 ? "1 file selected." : `${selectedCount} files selected.`;
      return `${filesLabel} You can add ${moreLabel}.`;
    }

    const displayCount = Math.min(selectedCount, maxFiles);
    return `${displayCount} files selected. Click "Run Extraction" to process and review results below.`;
  })();

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files).filter(f => f.type === "application/pdf");
    if (files.length) {
      onFilesSelected(files);
    }
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []).filter(f => f.type === "application/pdf");
    if (files.length) {
      onFilesSelected(files);
    }
  };

  const handleSelectClick = (event: MouseEvent<HTMLLabelElement>) => {
    if (limitReached) {
      event.preventDefault();
    }
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={e => e.preventDefault()}
      onDragEnter={() => setIsDragging(true)}
      onDragLeave={() => setIsDragging(false)}
      className={`group relative mx-auto flex w-full max-w-2xl flex-col items-center justify-center space-y-5 overflow-hidden rounded-3xl border border-slate-700/70 bg-gradient-to-br from-slate-900/80 via-slate-900 to-emerald-500/10 p-8 text-center shadow-[0_24px_56px_-34px_rgba(16,185,129,0.6)] transition-all duration-300 sm:p-10 ${
        isDragging
          ? "scale-[1.01] border-emerald-500 bg-gradient-to-br from-emerald-500/30 via-slate-900 to-emerald-500/20 shadow-[0_36px_76px_-42px_rgba(16,185,129,0.7)]"
          : "hover:border-emerald-400/80"
      }`}
    >
      <div
        className={`relative flex h-16 w-16 items-center justify-center rounded-2xl border-2 border-emerald-500/50 bg-slate-900 text-emerald-200 shadow-md transition-all ${
          isDragging
            ? "scale-110 border-emerald-300 text-emerald-200 shadow-lg"
            : "group-hover:border-emerald-400"
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
        <p className="text-lg font-semibold text-slate-100">
          Upload <span className="text-emerald-300">food label PDFs</span>
        </p>
        <p className="text-sm text-slate-300">
          Drag files into this panel or choose them below to upload up to {maxFiles} PDFs per run.
        </p>
      </div>
      <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
        PDF ONLY • MAX {maxFiles} FILES
      </p>
      <label
        onClick={handleSelectClick}
        htmlFor="pdf-upload"
        aria-disabled={limitReached}
        className={`mt-2 inline-flex items-center justify-center rounded-full border border-emerald-500 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400 ${
          limitReached
            ? "cursor-not-allowed bg-emerald-500/70 opacity-80"
            : "bg-emerald-500 hover:bg-emerald-400 active:scale-[0.98]"
        }`}
      >
        <span>Select PDFs</span>
        {limitReached && (
          <span className="ml-2 rounded-full bg-slate-900/40 px-2 py-0.5 text-[11px] font-semibold tracking-wide text-white">
            {Math.min(selectedCount, maxFiles)}/{maxFiles}
          </span>
        )}
      </label>
      <input
        id="pdf-upload"
        type="file"
        accept="application/pdf"
        multiple
        onChange={handleChange}
        disabled={limitReached}
        className="hidden"
      />
      {resolvedMessage && (
        <p className="mt-4 text-sm text-slate-300" role="status" aria-live="polite">
          {resolvedMessage}
        </p>
      )}
    </div>
  );
}
