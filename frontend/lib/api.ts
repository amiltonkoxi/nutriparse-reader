import axios from "axios";
const api = axios.create({ baseURL: process.env.NEXT_PUBLIC_API_URL });
export async function extractPDF(file: File) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/api/extract", form, { headers: { "Content-Type": "multipart/form-data" } });
  return data;
}
export default api;
