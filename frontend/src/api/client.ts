import axios from "axios";
import type {
  AnalysisResultBundle,
  ChatResponse,
  DiagramData,
  Job,
  Repository,
  SourceChunk,
} from "./types";

const http = axios.create({ baseURL: "/api" });

export const api = {
  createFromUrl: (url: string) => http.post<Job>("/repos/url", { url }).then((r) => r.data),

  createFromLocal: (path: string) => http.post<Job>("/repos/local", { path }).then((r) => r.data),

  createFromZip: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return http.post<Job>("/repos/zip", form, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
  },

  listRepos: () => http.get<Repository[]>("/repos").then((r) => r.data),

  getJob: (jobId: string) => http.get<Job>(`/jobs/${jobId}`).then((r) => r.data),

  getResult: (jobId: string) => http.get<AnalysisResultBundle>(`/jobs/${jobId}/result`).then((r) => r.data),

  listDiagramTypes: (jobId: string) => http.get<{ types: string[] }>(`/jobs/${jobId}/diagrams`).then((r) => r.data.types),

  getDiagram: (jobId: string, diagramType: string) =>
    http.get<DiagramData>(`/jobs/${jobId}/diagrams/${diagramType}`).then((r) => r.data),

  getReport: (jobId: string) => http.get<string>(`/jobs/${jobId}/report`, { responseType: "text" }).then((r) => r.data),

  getSource: (jobId: string, file: string) =>
    http.get<{ file: string; chunks: SourceChunk[] }>(`/jobs/${jobId}/source`, { params: { file } }).then((r) => r.data),

  chat: (jobId: string, message: string, history: { role: string; content: string }[]) =>
    http.post<ChatResponse>(`/jobs/${jobId}/chat`, { message, history }).then((r) => r.data),

  exportUrl: (jobId: string, fmt: "markdown" | "json" | "pdf") => `/api/jobs/${jobId}/export/${fmt}`,
};

export function apiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return (error.response?.data as { detail?: string } | undefined)?.detail ?? error.message;
  }
  return error instanceof Error ? error.message : "Unknown error";
}
