import { useState } from "react";
import type { AnalysisResultBundle } from "@/api/types";
import CodeViewer from "./CodeViewer";
import FolderTree from "./FolderTree";

export default function ExplorerTab({ jobId, result }: { jobId: string; result: AnalysisResultBundle }) {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const { summary } = result;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Files" value={summary.total_files} />
        <StatCard label="Lines of code" value={summary.total_loc.toLocaleString()} accent />
        <StatCard label="Primary language" value={summary.primary_language ?? "—"} />
      </div>

      {summary.frameworks.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {summary.frameworks.map((f) => (
            <span
              key={f}
              className="rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-300"
            >
              {f}
            </span>
          ))}
        </div>
      )}

      <FolderTree tree={summary.folder_tree} onSelectFile={setSelectedFile} />

      {selectedFile && <CodeViewer jobId={jobId} filePath={selectedFile} onClose={() => setSelectedFile(null)} />}
    </div>
  );
}

function StatCard({ label, value, accent }: { label: string; value: string | number; accent?: boolean }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-1 text-xl font-semibold ${accent ? "text-indigo-600 dark:text-indigo-400" : "text-slate-900 dark:text-slate-100"}`}>
        {value}
      </p>
    </div>
  );
}
