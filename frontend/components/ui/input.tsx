import * as React from "react"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "border border-slate-600 bg-slate-900 text-slate-200 placeholder:text-slate-500 selection:bg-emerald-600 selection:text-white h-9 w-full min-w-0 rounded-md px-3 py-1 text-base shadow-xs transition-[color,box-shadow] outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        "focus-visible:ring-emerald-400/40 focus-visible:ring-[3px]",
        "aria-invalid:border-rose-500",
        className
      )}
      {...props}
    />
  )
}

export { Input }
