import axios from "axios";
import type { ApiResponse } from "./types";

const API = process.env.NEXT_PUBLIC_API_BASE || process.env.NEXT_PUBLIC_API_URL;

export async function extractPDF(file: File): Promise<ApiResponse> {
  const fd = new FormData();
  fd.append("file", file);
  const { data } = await axios.post<ApiResponse>(`${API}/api/extract`, fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
