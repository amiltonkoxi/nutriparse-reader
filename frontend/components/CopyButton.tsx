"use client";
import { useState } from "react";
import { Button } from "./ui/button";
export default function CopyButton({ text }: { text: string }) {
  const [ok, setOk] = useState(false);
  return (
    <Button variant="outline" size="sm" onClick={async () => {
      await navigator.clipboard.writeText(text);
      setOk(true);
      setTimeout(() => setOk(false), 1200);
    }}>
      {ok ? "Copied" : "Copy JSON"}
    </Button>
  );
}
