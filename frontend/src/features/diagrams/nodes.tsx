import { Handle, Position, type NodeProps } from "reactflow";

const CARD =
  "rounded-xl border shadow-sm text-xs bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 min-w-[170px] transition-shadow hover:shadow-md";

function Handles() {
  return (
    <>
      <Handle type="target" position={Position.Top} className="!h-2 !w-2 !border-2 !border-white !bg-indigo-400 dark:!border-slate-900" />
      <Handle type="source" position={Position.Bottom} className="!h-2 !w-2 !border-2 !border-white !bg-indigo-400 dark:!border-slate-900" />
    </>
  );
}

function GenericNode({ data }: NodeProps) {
  return (
    <div className={CARD}>
      <Handles />
      <div className="px-3 py-2.5">
        <p className="truncate font-semibold text-slate-800 dark:text-slate-100">{String(data.label)}</p>
        {typeof data.file_count === "number" && <p className="mt-0.5 text-slate-400">{data.file_count} files</p>}
        {typeof data.language === "string" && <p className="mt-0.5 text-slate-400">{data.language}</p>}
        {typeof data.image === "string" && <p className="mt-0.5 truncate text-slate-400">{data.image}</p>}
      </div>
    </div>
  );
}

function FunctionNode({ data }: NodeProps) {
  const complexity = data.complexity as number | undefined;
  return (
    <div className={CARD}>
      <Handles />
      <div className="px-3 py-2.5">
        <p className="truncate font-mono font-semibold text-slate-800 dark:text-slate-100">{String(data.label)}()</p>
        {data.parent_class ? <p className="mt-0.5 truncate text-slate-400">{String(data.parent_class)}</p> : null}
        {typeof complexity === "number" && (
          <p className={`mt-0.5 font-medium ${complexity > 10 ? "text-red-500" : "text-slate-400"}`}>complexity {complexity}</p>
        )}
      </div>
    </div>
  );
}

function ClassNode({ data }: NodeProps) {
  const methods = (data.methods as string[]) ?? [];
  return (
    <div className={CARD}>
      <Handles />
      <div className="rounded-t-xl border-b border-slate-200 bg-slate-50 px-3 py-1.5 font-semibold text-slate-800 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-100">
        {String(data.label)}
      </div>
      <ul className="max-h-32 overflow-y-auto px-3 py-1.5 font-mono text-slate-500 dark:text-slate-400">
        {methods.length === 0 && <li className="italic">no methods</li>}
        {methods.slice(0, 10).map((m) => (
          <li key={m} className="truncate py-0.5">
            {m}()
          </li>
        ))}
        {methods.length > 10 && <li className="py-0.5 text-slate-400">+{methods.length - 10} more</li>}
      </ul>
    </div>
  );
}

function TableNode({ data }: NodeProps) {
  const columns = (data.columns as { name: string; type: string; primary_key: boolean; foreign_key: string | null }[]) ?? [];
  return (
    <div className={CARD}>
      <Handles />
      <div className="rounded-t-xl border-b border-slate-200 bg-indigo-50/70 px-3 py-1.5 font-semibold text-slate-800 dark:border-slate-700 dark:bg-indigo-500/10 dark:text-slate-100">
        {String(data.label)}
        {typeof data.orm === "string" && <span className="ml-1 font-normal text-slate-400">({data.orm})</span>}
      </div>
      <table className="w-full">
        <tbody>
          {columns.map((c) => (
            <tr key={c.name} className="border-b border-slate-100 last:border-0 dark:border-slate-800">
              <td className="px-2 py-1 font-mono">
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
              <td className="px-2 py-1 text-slate-400">{c.type}</td>
            </tr>
          ))}
          {columns.length === 0 && (
            <tr>
              <td className="px-2 py-1 italic text-slate-400">no columns detected</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export { ClassNode, FunctionNode, GenericNode, TableNode };
