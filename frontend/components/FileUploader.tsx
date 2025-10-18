"use client";
import { useState, useCallback } from "react";
import { extractPDF } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { Loader } from "./Loader";

type AxiosLikeError = { response?: { data?: { detail?: string } } };

function isAxiosLikeError(x: unknown): x is AxiosLikeError {
  return typeof x === "object" && x !== null && "response" in x;
}

export function FileUploader({ onResult }: { onResult: (r: ApiResponse | null) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    setFile(f ?? null);
  }, []);

  const onSubmit = useCallback(async () => {
    if (!file) return;
    setError(null);
    setLoading(true);
    try {
      const data = await extractPDF(file);
      onResult(data);
    } catch (e: unknown) {
      let msg = "Failed to process the PDF.";
      if (isAxiosLikeError(e)) msg = e.response?.data?.detail ?? msg;
      else if (e instanceof Error) msg = e.message || msg;

      console.error(e);
      setError(msg);
      onResult(null);
    } finally {
      setLoading(false);
    }
  }, [file, onResult]);

  return (
    <Card>
      <CardHeader><CardTitle>Upload PDF</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <Input type="file" accept="application/pdf" onChange={onChange} />
          <Button onClick={onSubmit} disabled={!file || loading}>
            {loading ? "Processing..." : "Upload"}
          </Button>
        </div>
        {loading && <Loader />}
        {error && (
          <Alert variant="destructive">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
