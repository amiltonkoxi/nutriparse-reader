import axios from "axios";
import type { ApiResponse } from "./types";

// Build the backend base URL once, trimming stray slashes.
const RAW_API_BASE = (process.env.NEXT_PUBLIC_API_BASE || "").replace(/\/$/, "");
const API_BASE = RAW_API_BASE || "http://localhost:8000";

export async function extractPDF(file: File): Promise<ApiResponse> {
  // Always send a fresh FormData payload per request.
  const fd = new FormData();
  fd.append("file", file);

  // Append a timestamp to bypass CDN caches when Render updates.
  const endpoint = `${API_BASE}/extract?ts=${Date.now()}`;
  const { data } = await axios.post<ApiResponse>(endpoint, fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
