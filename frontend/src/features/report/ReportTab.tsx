import { useQuery } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api } from "@/api/client";
import type { ArchitectureResult } from "@/api/types";
import Spinner from "@/components/Spinner";
import ExportMenu from "./ExportMenu";

export default function ReportTab({ jobId, architecture }: { jobId: string; architecture: ArchitectureResult }) {
  const report = useQuery({ queryKey: ["report", jobId], queryFn: () => api.getReport(jobId) });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Executive Architecture Report</h2>
          <p className="mt-0.5 text-sm text-slate-500 dark:text-slate-400">
            Detected style:{" "}
            <span className="rounded-full bg-indigo-50 px-2 py-0.5 font-medium text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-300">
              {architecture.primary_style}
            </span>{" "}
            · {architecture.confidence}% confidence
          </p>
        </div>
        <ExportMenu jobId={jobId} />
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-8">
        {report.isLoading && (
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Spinner className="h-4 w-4" />
            Loading report…
          </div>
        )}
        {report.data && (
          <article className="prose prose-slate max-w-none dark:prose-invert prose-headings:font-semibold prose-headings:tracking-tight prose-a:text-indigo-600 dark:prose-a:text-indigo-400 prose-blockquote:border-indigo-300 prose-blockquote:text-slate-500 prose-strong:text-slate-800 dark:prose-strong:text-slate-200 prose-pre:bg-slate-100 dark:prose-pre:bg-slate-800/60 dark:prose-blockquote:border-indigo-500/40">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{report.data}</ReactMarkdown>
          </article>
        )}
      </div>
    </div>
  );
}
