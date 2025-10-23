// MultiUploader component for handling multiple PDF uploads
"use client";

import React, { useCallback, useMemo, useState } from "react";

type ExtractResult = {
  meta: any;
  allergens: any;
  nutrition: any;
  diagnostics: { warnings?: string[] };
};

type Props = {
  isLoggedIn?: boolean;                 // false = guest access
  backendUrl?: string;                  // e.g. "http://localhost:8000"
  onEachResult?: (res: ExtractResult) => void; // optional callback to surface parsed results
};

export default function MultiUploader({
  isLoggedIn = false,
  backendUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  onEachResult,
}: Props) {
  const MAX_FILES = useMemo(() => (isLoggedIn ? 5 : 2), [isLoggedIn]);

  const [queue, setQueue] = useState<File[]>([]);
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState("Drop PDFs here or click to select.");
  const [error, setError] = useState<string | null>(null);

  const onFilesPicked = useCallback(
    (files: FileList | null) => {
      setError(null);
      if (!files) return;

      const incoming = Array.from(files).filter(f => f.type === "application/pdf");
      if (incoming.length === 0) {
        setError("Only PDF files are accepted.");
        return;
      }

      const room = MAX_FILES - queue.length;
      const accepted = incoming.slice(0, Math.max(0, room));
      const rejected = incoming.length - accepted.length;

      if (accepted.length) {
        setQueue(prev => [...prev, ...accepted]);
        const left = MAX_FILES - (queue.length + accepted.length);
        setMessage(
          left > 0
            ? `Added file(s). You can upload ${left} more or start processing.`
            : `Queue full (${MAX_FILES}). Click Process to continue.`
        );
      }

      if (rejected > 0) {
        setError(`Limit of ${MAX_FILES} file(s). Remove some before adding more.`);
      }
    },
    [MAX_FILES, queue.length]
  );

  const removeFromQueue = (idx: number) => {
    setQueue(prev => prev.filter((_, i) => i !== idx));
    setMessage("Removed file. You can add another or process the rest.");
    setError(null);
  };

  const processQueue = async () => {
    if (queue.length === 0 || processing) return;
    setProcessing(true);
    setError(null);

    try {
      for (const file of queue) {
        const form = new FormData();
        form.append("file", file, file.name);

        const res = await fetch(`${backendUrl}/extract`, { method: "POST", body: form });
        if (!res.ok) {
          const txt = await res.text();
          throw new Error(`Failed to process "${file.name}": ${res.status} ${txt}`);
        }
        const json = (await res.json()) as ExtractResult;
        onEachResult?.(json);
      }

      setMessage("Done! Add new PDFs or review the results below.");
      setQueue([]);
    } catch (e: any) {
      setError(e?.message ?? "Processing error.");
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Drop/select area */}
      <label
        className={`block cursor-pointer rounded-xl border-2 border-dashed p-8 text-center ${
          processing ? "opacity-60" : ""
        }`}
      >
        <input
          type="file"
          accept="application/pdf"
          multiple
          className="hidden"
          onChange={(e) => onFilesPicked(e.target.files)}
          disabled={processing || queue.length >= MAX_FILES}
        />
        <div className="text-lg font-semibold">Select PDF files</div>
        <div className="text-sm opacity-70 mt-1">
          Limit: {MAX_FILES} file(s) {isLoggedIn ? "(signed in)" : "(guest)"}
        </div>
        <div className="text-sm mt-2">{message}</div>
      </label>

      {/* Queue */}
      {queue.length > 0 && (
        <div className="rounded-xl border p-4">
          <div className="font-medium mb-2">In queue ({queue.length}/{MAX_FILES})</div>
          <ul className="space-y-2">
            {queue.map((f, i) => (
              <li key={i} className="flex items-center justify-between text-sm">
                <span className="truncate">{f.name}</span>
                <button
                  className="text-red-600 hover:underline disabled:opacity-50"
                  onClick={() => removeFromQueue(i)}
                  disabled={processing}
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-3">
        <button
          className="rounded-lg bg-emerald-600 px-4 py-2 text-white disabled:opacity-50"
          onClick={processQueue}
          disabled={processing || queue.length === 0}
        >
          {processing ? "Processing..." : "Process"}
        </button>
        {!isLoggedIn && (
          <span className="text-xs opacity-70">
            Need to upload more than {MAX_FILES}? Sign in or create an account.
          </span>
        )}
      </div>

      {/* Messages */}
      {!!error && <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>}
    </div>
  );
}
