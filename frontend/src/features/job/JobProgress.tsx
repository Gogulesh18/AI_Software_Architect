import clsx from "clsx";
import type { Job } from "@/api/types";
import Spinner from "@/components/Spinner";

const STAGES = [
  { key: "ingest", label: "Reading repository" },
  { key: "parse", label: "Parsing source files" },
  { key: "graph", label: "Building knowledge graph" },
  { key: "analyze", label: "Running architecture analysis" },
  { key: "diagram", label: "Generating diagrams" },
  { key: "report", label: "Writing executive report" },
  { key: "embed", label: "Indexing for search" },
] as const;

function stageIndex(stage: string): number {
  if (stage === "queued") return -1;
  if (stage === "done") return STAGES.length;
  return STAGES.findIndex((s) => s.key === stage);
}

export default function JobProgress({ job }: { job: Job | undefined }) {
  if (!job) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <Spinner className="h-6 w-6" />
      </div>
    );
  }

  if (job.status === "failed") {
    return (
      <div className="mx-auto mt-24 max-w-md">
        <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-center dark:border-red-900/50 dark:bg-red-900/10">
          <p className="text-sm font-semibold text-red-700 dark:text-red-400">Analysis failed</p>
          <p className="mt-1.5 text-sm text-red-600/80 dark:text-red-400/70">{job.error_message}</p>
        </div>
      </div>
    );
  }

  const current = stageIndex(job.status === "queued" ? "queued" : job.stage);

  return (
    <div className="mx-auto mt-20 max-w-md">
      <div className="text-center">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Analyzing repository…</h2>
        <p className="mt-1 text-sm text-slate-400">This runs through the full pipeline: ingest, parse, graph, analyze, diagram, report, embed.</p>
      </div>

      <div className="mt-6 h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
        <div
          className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-700 ease-out"
          style={{ width: `${job.progress}%` }}
        />
      </div>
      <p className="mt-1.5 text-right text-xs font-medium text-slate-400">{job.progress}%</p>

      <ol className="mt-6 space-y-1">
        {STAGES.map((s, i) => {
          const done = i < current;
          const active = i === current;
          return (
            <li
              key={s.key}
              className={clsx(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                active && "bg-indigo-50 dark:bg-indigo-500/10"
              )}
            >
              <span
                className={clsx(
                  "flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold",
                  done && "bg-emerald-500 text-white",
                  active && "bg-indigo-600 text-white",
                  !done && !active && "bg-slate-200 text-slate-400 dark:bg-slate-800 dark:text-slate-500"
                )}
              >
                {done ? "✓" : active ? <Spinner className="h-3 w-3 text-white" /> : i + 1}
              </span>
              <span
                className={clsx(
                  "font-medium",
                  done && "text-slate-400 dark:text-slate-500",
                  active && "text-indigo-700 dark:text-indigo-300",
                  !done && !active && "text-slate-400 dark:text-slate-600"
                )}
              >
                {s.label}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
