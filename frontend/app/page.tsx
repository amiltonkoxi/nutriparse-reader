"use client";
import { useState } from "react";
import { FileUploader } from "@/components/FileUploader";
import { ResultCard } from "@/components/ResultCard";
import { ApiResponse } from "@/lib/types";

export default function Page() {
  const [result, setResult] = useState<ApiResponse | null>(null);
  return (
    <main className="mx-auto max-w-4xl p-6 space-y-6">
      <header className="flex items-center gap-3">
        <img src="/logo.svg" alt="logo" className="h-6"/>
        <h1 className="text-2xl font-semibold">Food PDF Extractor</h1>
      </header>
      <FileUploader onResult={setResult} />
      {result && <ResultCard data={result} />}
    </main>
  );
}
