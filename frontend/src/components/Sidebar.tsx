import clsx from "clsx";
import { Link, useParams } from "react-router-dom";
import {
  ApiIcon,
  DatabaseIcon,
  DiagramIcon,
  ExplorerIcon,
  FindingsIcon,
  PlusIcon,
  ReportIcon,
  ScoresIcon,
  SearchIcon,
} from "./icons";
import ThemeToggle from "./ThemeToggle";

export const TABS = [
  { key: "report", label: "Architecture Report", icon: ReportIcon },
  { key: "explorer", label: "Repository Explorer", icon: ExplorerIcon },
  { key: "diagrams", label: "Diagrams", icon: DiagramIcon },
  { key: "database", label: "Database", icon: DatabaseIcon },
  { key: "api", label: "API Surface", icon: ApiIcon },
  { key: "findings", label: "Findings", icon: FindingsIcon },
  { key: "scores", label: "Scores", icon: ScoresIcon },
  { key: "search", label: "Search", icon: SearchIcon },
] as const;

export type TabKey = (typeof TABS)[number]["key"];

export default function Sidebar() {
  const { jobId, tab } = useParams<{ jobId: string; tab: string }>();

  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
      <div className="flex items-center gap-2.5 border-b border-slate-200 px-4 py-4 dark:border-slate-800">
        <Link to="/" className="flex items-center gap-2.5 focus-ring rounded-md">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-sm font-bold text-white shadow-sm shadow-indigo-600/30">
            AI
          </span>
          <span className="text-[15px] font-semibold leading-tight tracking-tight text-slate-900 dark:text-slate-100">
            Software
            <br />
            Architect
          </span>
        </Link>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto p-2.5">
        {jobId ? (
          TABS.map((t) => {
            const Icon = t.icon;
            const active = tab === t.key;
            return (
              <Link
                key={t.key}
                to={`/jobs/${jobId}/${t.key}`}
                className={clsx(
                  "focus-ring flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-300"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800/70"
                )}
              >
                <Icon className={clsx("h-[18px] w-[18px] shrink-0", active ? "text-indigo-600 dark:text-indigo-300" : "text-slate-400 dark:text-slate-500")} />
                {t.label}
              </Link>
            );
          })
        ) : (
          <p className="px-3 py-2 text-sm text-slate-400">Analyze a repository to see navigation.</p>
        )}

        <Link
          to="/"
          className="focus-ring mt-3 flex items-center gap-2.5 rounded-lg border border-dashed border-slate-300 px-3 py-2 text-sm font-medium text-slate-500 transition-colors hover:border-indigo-300 hover:bg-indigo-50/60 hover:text-indigo-600 dark:border-slate-700 dark:text-slate-400 dark:hover:border-indigo-500/40 dark:hover:bg-indigo-500/10 dark:hover:text-indigo-300"
        >
          <PlusIcon className="h-[18px] w-[18px]" />
          New analysis
        </Link>
      </nav>

      <div className="border-t border-slate-200 p-3 dark:border-slate-800">
        <ThemeToggle />
      </div>
    </aside>
  );
}
