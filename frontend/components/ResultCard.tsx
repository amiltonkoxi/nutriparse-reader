"use client";
import { ApiResponse, AllergenStatus } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Badge } from "./ui/badge";
import CopyButton from "./CopyButton";
import { ScrollArea } from "./ui/scroll-area";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./ui/tooltip";
const STATUS_STYLES: Record<AllergenStatus, string> = {
  contains: "bg-red-600 text-white",
  traces: "bg-amber-500 text-white",
  absent: "bg-emerald-600 text-white",
  unknown: "bg-slate-400 text-white",
};
function pct(x: number) { return `${Math.round((x ?? 0) * 100)}%`; }
export function ResultCard({ data }: { data: ApiResponse }) {
  const { meta, allergens, nutrition, extras, diagnostics } = data;
  const allergenEntries = Object.entries(allergens) as [string, {status: AllergenStatus, evidence: string | null}][];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-4">
          <div>
            <CardTitle className="text-xl">Extraction Results</CardTitle>
            <div className="mt-1 text-xs text-slate-500">
              <span className="mr-2">Arquivo: {meta.source_file}</span>
              <div className="flex gap-2 mt-1">
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs">
                  {meta.extraction_mode === "ocr" ? "OCR mode" : "Text mode"}
                  </span>
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs">
                    conf {(meta.confidence * 100).toFixed(0)}%
                    </span>
              </div>
            </div>
          </div>
          <CopyButton text={JSON.stringify(data, null, 2)} />
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="table" className="w-full">
          <TabsList>
            <TabsTrigger value="table">Table</TabsTrigger>
            <TabsTrigger value="json">JSON</TabsTrigger>
            <TabsTrigger value="preview" disabled={!diagnostics?.raw_text_preview}>Preview</TabsTrigger>
          </TabsList>
          <TabsContent value="table" className="pt-4 space-y-6">
            <section>
              <h3 className="font-medium mb-2">Allergens</h3>
              <TooltipProvider>
                <div className="flex flex-wrap gap-2">
                  {allergenEntries.map(([key, v]) => (
                    <Tooltip key={key}>
                      <TooltipTrigger asChild>
                        <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${STATUS_STYLES[v.status]}`}>
                          {key.replace(/_/g, " ")}
                        </span>
                      </TooltipTrigger>
                      <TooltipContent className="max-w-sm"><p className="text-xs whitespace-pre-wrap">{v.evidence || "(sem evidência)"}</p></TooltipContent>
                    </Tooltip>
                  ))}
                </div>
              </TooltipProvider>
            </section>
            <section>
              <h3 className="font-medium mb-2">Nutrition (per 100g quando disponível)</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm border">
                  <tbody>
                    <tr className="border-b"><td className="p-2 font-medium">Energy</td><td className="p-2">{nutrition.energy?.kJ ?? "—"} kJ / {nutrition.energy?.kcal ?? "—"} kcal</td></tr>
                    <tr className="border-b"><td className="p-2 font-medium">Fat</td><td className="p-2">{nutrition.fat_g != null ? nutrition.fat_g.toFixed(1) : "—"} g</td></tr>
                    <tr className="border-b"><td className="p-2 font-medium">Carbohydrate</td><td className="p-2">{nutrition.carbohydrate_g ?? "—"} g</td></tr>
                    <tr className="border-b"><td className="p-2 font-medium">Sugar</td><td className="p-2">{nutrition.sugar_g ?? "—"} g</td></tr>
                    <tr className="border-b"><td className="p-2 font-medium">Protein</td><td className="p-2">{nutrition.protein_g ?? "—"} g</td></tr>
                    <tr className="border-b"><td className="p-2 font-medium">Salt</td><td className="p-2">{nutrition.salt_g ?? (nutrition.sodium_g ? `${(nutrition.sodium_g * 2.54).toFixed(3)} g (calc from sodium)` : "—")}</td></tr>
                  </tbody>
                </table>
              </div>
              {nutrition.notes && <p className="mt-2 text-xs text-slate-500">{nutrition.notes}</p>}
            </section>
            {diagnostics?.warnings?.length ? (
              <section>
                <h3 className="font-medium mb-2">Diagnostics</h3>
                <ul className="list-disc ml-5 text-xs text-amber-700">{diagnostics.warnings.map((w,i)=><li key={i}>{w}</li>)}</ul>
              </section>
            ):null}
          </TabsContent>
          <TabsContent value="json" className="pt-4">
            <ScrollArea className="h-80 rounded border p-3 bg-slate-50"><pre className="text-xs whitespace-pre-wrap">{JSON.stringify(data, null, 2)}</pre></ScrollArea>
          </TabsContent>
          <TabsContent value="preview" className="pt-4">
            {diagnostics?.raw_text_preview ?
              <ScrollArea className="h-80 rounded border p-3 bg-slate-50"><pre className="text-xs whitespace-pre-wrap">{diagnostics.raw_text_preview}</pre></ScrollArea> :
              <p className="text-sm text-slate-500">Sem preview disponível.</p>}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
