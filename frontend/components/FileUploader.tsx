"use client";
import { useState, useCallback } from "react";
import { extractPDF } from "@/lib/api";
import { ApiResponse } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { Loader } from "./Loader";

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
      const data: ApiResponse = await extractPDF(file);
      onResult(data);
    } catch (e: any) {
      console.error(e);
      setError(e?.response?.data?.detail || "Failed to process PDF.");
      onResult(null);
    } finally {
      setLoading(false);
    }
  }, [file, onResult]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload PDF</CardTitle>
      </CardHeader>
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
