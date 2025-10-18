export function Loader() {
  return (
    <div className="flex flex-col items-center justify-center py-10 space-y-3">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-emerald-500" />
      <p className="text-sm font-medium text-slate-600">
        Loading <span className="text-emerald-500 font-semibold">NutriParse Reader</span>...
      </p>
    </div>
  );
}
