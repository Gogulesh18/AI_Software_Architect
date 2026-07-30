import { useQuery } from "@tanstack/react-query";
import { Suspense, lazy } from "react";
import { Navigate, useParams } from "react-router-dom";
import { api } from "@/api/client";
import Sidebar, { TABS, type TabKey } from "@/components/Sidebar";
import ApiTab from "@/features/api/ApiTab";
import DatabaseTab from "@/features/database/DatabaseTab";
import FindingsTab from "@/features/findings/FindingsTab";
import ReportTab from "@/features/report/ReportTab";
import SearchTab from "@/features/search/SearchTab";
import JobProgress from "./JobProgress";

// Code-split the heaviest dependencies (react flow, recharts, monaco) out
// of the main bundle — they're only needed once a user opens that tab.
const DiagramsTab = lazy(() => import("@/features/diagrams/DiagramsTab"));
const ScoresTab = lazy(() => import("@/features/scores/ScoresTab"));
const ExplorerTab = lazy(() => import("@/features/explorer/ExplorerTab"));

export default function JobPage() {
  const { jobId, tab } = useParams<{ jobId: string; tab: string }>();

  // Hooks must run unconditionally on every render (rules-of-hooks) — so
  // the missing-jobId case is handled via `enabled`/fallbacks here and only
  // turned into a redirect in the JSX below, after all hooks are called.
  const job = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => api.getJob(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => (query.state.data?.status === "done" || query.state.data?.status === "failed" ? false : 1000),
  });

  const result = useQuery({
    queryKey: ["result", jobId],
    queryFn: () => api.getResult(jobId!),
    enabled: !!jobId && job.data?.status === "done",
  });

  const activeTab = (TABS.find((t) => t.key === tab)?.key ?? "report") as TabKey;

  if (!jobId) return <Navigate to="/" replace />;

  return (
    <div className="flex">
      <Sidebar />
      <main className="min-h-screen flex-1 overflow-y-auto bg-slate-50 p-6 dark:bg-slate-950">
        {!job.data || job.data.status !== "done" ? (
          <JobProgress job={job.data} />
        ) : !result.data ? (
          <p className="text-sm text-slate-400">Loading analysis…</p>
        ) : (
          <Suspense fallback={<p className="text-sm text-slate-400">Loading…</p>}>
            {activeTab === "report" && <ReportTab jobId={jobId} architecture={result.data.architecture} />}
            {activeTab === "explorer" && <ExplorerTab jobId={jobId} result={result.data} />}
            {activeTab === "diagrams" && <DiagramsTab jobId={jobId} />}
            {activeTab === "database" && <DatabaseTab database={result.data.database_schema} />}
            {activeTab === "api" && <ApiTab api={result.data.api_surface} />}
            {activeTab === "findings" && <FindingsTab result={result.data} />}
            {activeTab === "scores" && <ScoresTab scores={result.data.scores} />}
            {activeTab === "search" && <SearchTab jobId={jobId} />}
          </Suspense>
        )}
      </main>
    </div>
  );
}
