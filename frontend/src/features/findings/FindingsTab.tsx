import { useState } from "react";
import type { AnalysisResultBundle, Finding } from "@/api/types";
import { FindingsIcon } from "@/components/icons";

const SEVERITY_COLOR: Record<string, string> = {
  critical: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
  high: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300",
  medium: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  low: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
  info: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
};

const SUB_TABS = ["patterns", "solid", "quality", "security", "performance"] as const;
type SubTab = (typeof SUB_TABS)[number];

export default function FindingsTab({ result }: { result: AnalysisResultBundle }) {
  const [sub, setSub] = useState<SubTab>("security");

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-1.5 rounded-xl border border-slate-200 bg-white p-1.5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        {SUB_TABS.map((t) => {
          const count = countFor(result, t);
          return (
            <button
              key={t}
              onClick={() => setSub(t)}
              className={`focus-ring flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium capitalize transition-colors ${
                sub === t
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              }`}
            >
              {t}
              <span
                className={`rounded-full px-1.5 py-0.5 text-xs font-semibold ${
                  sub === t ? "bg-white/20 text-white" : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400"
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {sub === "patterns" && <PatternsList matches={result.patterns.matches} />}
      {sub === "solid" && <SolidList violations={result.solid.violations} />}
      {sub === "quality" && <FindingsList findings={result.quality.findings} />}
      {sub === "security" && <FindingsList findings={result.security.findings} />}
      {sub === "performance" && <FindingsList findings={result.performance.findings} />}
    </div>
  );
}

function countFor(result: AnalysisResultBundle, tab: SubTab): number {
  if (tab === "patterns") return result.patterns.matches.length;
  if (tab === "solid") return result.solid.violations.length;
  return result[tab].findings.length;
}

function FindingsList({ findings }: { findings: Finding[] }) {
  if (findings.length === 0) return <Empty />;
  return (
    <ul className="divide-y divide-slate-100 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-900">
      {findings.map((f, i) => (
        <li key={i} className="flex items-start gap-3 px-4 py-3.5 transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/40">
          <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold capitalize ${SEVERITY_COLOR[f.severity]}`}>{f.severity}</span>
          <div className="min-w-0">
            <p className="text-sm text-slate-700 dark:text-slate-200">{f.message}</p>
            <p className="mt-0.5 font-mono text-xs text-slate-400">
              {f.file}
              {f.line ? `:${f.line}` : ""} {f.symbol ? `· ${f.symbol}` : ""} · {f.category}
            </p>
          </div>
        </li>
      ))}
    </ul>
  );
}

function PatternsList({ matches }: { matches: AnalysisResultBundle["patterns"]["matches"] }) {
  if (matches.length === 0) return <Empty />;
  return (
    <ul className="divide-y divide-slate-100 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-900">
      {matches.map((m, i) => (
        <li key={i} className="px-4 py-3.5 transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/40">
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
            <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-300">{m.pattern}</span>{" "}
            {m.symbol && <span className="font-mono text-xs font-normal text-slate-400">{m.symbol}</span>}
          </p>
          <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">{m.reason}</p>
          <p className="mt-0.5 font-mono text-xs text-slate-400">
            {m.file}
            {m.line ? `:${m.line}` : ""}
          </p>
        </li>
      ))}
    </ul>
  );
}

function SolidList({ violations }: { violations: AnalysisResultBundle["solid"]["violations"] }) {
  if (violations.length === 0) return <Empty />;
  return (
    <ul className="divide-y divide-slate-100 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-900">
      {violations.map((v, i) => (
        <li key={i} className="px-4 py-3.5 transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/40">
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
            <span className="rounded-full bg-amber-50 px-2 py-0.5 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300">{v.principle}</span>
          </p>
          <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">{v.message}</p>
          <p className="mt-0.5 font-mono text-xs text-slate-400">
            {v.file}:{v.line} · {v.symbol}
          </p>
        </li>
      ))}
    </ul>
  );
}

function Empty() {
  return (
    <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-slate-200 bg-white/50 py-12 text-sm text-slate-400 dark:border-slate-800 dark:bg-slate-900/50">
      <FindingsIcon className="h-7 w-7 text-slate-300 dark:text-slate-700" />
      No findings in this category.
    </div>
  );
}
