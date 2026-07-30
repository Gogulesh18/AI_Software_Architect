import type { ApiSurface } from "@/api/types";
import { ApiIcon } from "@/components/icons";

const METHOD_COLOR: Record<string, string> = {
  GET: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  POST: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
  PUT: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  PATCH: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  DELETE: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
  WEBSOCKET: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300",
  ANY: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
};

export default function ApiTab({ api }: { api: ApiSurface }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Stat label="Protocols" value={api.protocols.join(", ") || "none detected"} />
        <Stat label="Endpoints" value={api.endpoint_count} accent />
        <Stat label="Auth" value={api.auth.detected ? api.auth.mechanisms.join(", ") : "not detected"} />
      </div>

      {api.endpoints.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-slate-200 bg-white/50 py-16 text-sm text-slate-400 dark:border-slate-800 dark:bg-slate-900/50">
          <ApiIcon className="h-8 w-8 text-slate-300 dark:text-slate-700" />
          No API endpoints detected.
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-200 shadow-sm dark:border-slate-800">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-400 dark:bg-slate-800/50">
              <tr>
                <th className="px-4 py-2.5">Method</th>
                <th className="px-4 py-2.5">Path</th>
                <th className="px-4 py-2.5">Framework</th>
                <th className="px-4 py-2.5">Location</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-slate-900">
              {api.endpoints.map((e, i) => (
                <tr key={i} className="border-t border-slate-100 transition-colors hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/40">
                  <td className="px-4 py-2.5">
                    <span className={`rounded px-1.5 py-0.5 text-xs font-semibold ${METHOD_COLOR[e.method] ?? METHOD_COLOR.ANY}`}>{e.method}</span>
                  </td>
                  <td className="px-4 py-2.5 font-mono text-slate-700 dark:text-slate-200">{e.path}</td>
                  <td className="px-4 py-2.5 text-slate-400">{e.framework}</td>
                  <td className="px-4 py-2.5 font-mono text-xs text-slate-400">
                    {e.file}:{e.line}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: string | number; accent?: boolean }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-1 truncate text-lg font-semibold ${accent ? "text-indigo-600 dark:text-indigo-400" : "text-slate-900 dark:text-slate-100"}`}>
        {value}
      </p>
    </div>
  );
}
