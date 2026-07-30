import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip } from "recharts";
import type { Scores } from "@/api/types";

const LABELS: Record<string, string> = {
  architecture: "Architecture",
  security: "Security",
  performance: "Performance",
  maintainability: "Maintainability",
  readability: "Readability",
  scalability: "Scalability",
  testability: "Testability",
  documentation: "Documentation",
  overall: "Overall",
};

function scoreColor(score: number): string {
  if (score >= 80) return "text-emerald-600 dark:text-emerald-400";
  if (score >= 60) return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
}

function scoreBarColor(score: number): string {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 60) return "bg-amber-500";
  return "bg-red-500";
}

function ScoreBar({ score }: { score: number }) {
  return (
    <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
      <div className={`h-full rounded-full ${scoreBarColor(score)} transition-all duration-500`} style={{ width: `${score}%` }} />
    </div>
  );
}

export default function ScoresTab({ scores }: { scores: Scores }) {
  const categories = Object.entries(scores).filter(([key]) => key !== "overall");
  const chartData = categories.map(([key, entry]) => ({ subject: LABELS[key] ?? key, score: entry.score }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Overall Engineering Score</h2>
            <span className={`text-4xl font-bold tabular-nums ${scoreColor(scores.overall.score)}`}>{scores.overall.score}</span>
          </div>
          <ScoreBar score={scores.overall.score} />
          <ul className="mt-4 space-y-1.5 text-sm text-slate-500 dark:text-slate-400">
            {scores.overall.reasoning.map((r, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-indigo-400">•</span>
                {r}
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h3 className="mb-1 text-sm font-semibold text-slate-600 dark:text-slate-300">Score breakdown</h3>
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={chartData}>
              <PolarGrid stroke="currentColor" className="text-slate-200 dark:text-slate-700" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11, fill: "currentColor" }} className="text-slate-600 dark:text-slate-300" />
              <PolarRadiusAxis domain={[0, 100]} angle={90} tick={{ fontSize: 9, fill: "currentColor" }} className="text-slate-400" />
              <Radar dataKey="score" stroke="#4f46e5" fill="#4f46e5" fillOpacity={0.35} />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid rgb(226 232 240)" }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {categories.map(([key, entry]) => (
          <div
            key={key}
            className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-slate-800 dark:text-slate-100">{LABELS[key] ?? key}</h3>
              <span className={`text-xl font-semibold tabular-nums ${scoreColor(entry.score)}`}>{entry.score}</span>
            </div>
            <ScoreBar score={entry.score} />
            <ul className="mt-3 space-y-1 text-xs text-slate-500 dark:text-slate-400">
              {entry.reasoning.map((r, i) => (
                <li key={i} className="flex gap-1.5">
                  <span className="text-indigo-400">•</span>
                  {r}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
