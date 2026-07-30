import { api } from "@/api/client";
import { DownloadIcon } from "@/components/icons";

export default function ExportMenu({ jobId }: { jobId: string }) {
  return (
    <div className="flex gap-2">
      {(["markdown", "json", "pdf"] as const).map((fmt) => (
        <a
          key={fmt}
          href={api.exportUrl(jobId, fmt)}
          download
          className="focus-ring flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-600 shadow-sm transition-colors hover:border-indigo-300 hover:text-indigo-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-indigo-500/50 dark:hover:text-indigo-300"
        >
          <DownloadIcon className="h-3.5 w-3.5" />
          {fmt.toUpperCase()}
        </a>
      ))}
    </div>
  );
}
