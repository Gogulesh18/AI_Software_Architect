import type { DatabaseSchema } from "@/api/types";
import { DatabaseIcon } from "@/components/icons";

export default function DatabaseTab({ database }: { database: DatabaseSchema }) {
  if (database.tables.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-slate-200 bg-white/50 py-16 text-sm text-slate-400 dark:border-slate-800 dark:bg-slate-900/50">
        <DatabaseIcon className="h-8 w-8 text-slate-300 dark:text-slate-700" />
        No ORM models or database schema detected in this repository.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {database.orms_detected.map((orm) => (
          <span
            key={orm}
            className="rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-300"
          >
            {orm}
          </span>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {database.tables.map((table) => (
          <div
            key={`${table.file}:${table.name}`}
            className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-shadow hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="border-b border-slate-200 bg-slate-50 px-4 py-2.5 dark:border-slate-800 dark:bg-slate-800/50">
              <p className="font-semibold text-slate-800 dark:text-slate-100">{table.name}</p>
              <p className="text-xs text-slate-400">
                {table.orm} · {table.file}
              </p>
            </div>
            <table className="w-full text-sm">
              <tbody>
                {table.columns.map((c) => (
                  <tr key={c.name} className="border-b border-slate-100 last:border-0 dark:border-slate-800">
                    <td className="px-4 py-2 font-mono">
                      {c.primary_key && (
                        <span className="mr-1 rounded bg-amber-100 px-1 text-[10px] font-semibold text-amber-700 dark:bg-amber-900/40 dark:text-amber-300">
                          PK
                        </span>
                      )}
                      {c.foreign_key && (
                        <span className="mr-1 rounded bg-blue-100 px-1 text-[10px] font-semibold text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
                          FK
                        </span>
                      )}
                      {c.name}
                    </td>
                    <td className="px-4 py-2 text-slate-400">{c.type}</td>
                  </tr>
                ))}
                {table.columns.length === 0 && (
                  <tr>
                    <td className="px-4 py-2 italic text-slate-400">no columns detected</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        ))}
      </div>

      {database.relationships.length > 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h3 className="mb-2 text-sm font-semibold text-slate-700 dark:text-slate-200">Relationships</h3>
          <ul className="space-y-1.5 text-sm text-slate-500 dark:text-slate-400">
            {database.relationships.map((r, i) => (
              <li key={i} className="font-mono">
                {r.from} <span className="text-indigo-400">→</span> {r.to} <span className="text-slate-400">({r.via})</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
