import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api } from "@/api/client";
import Spinner from "@/components/Spinner";
import DiagramViewer from "./DiagramViewer";

const LABELS: Record<string, string> = {
  architecture_diagram: "Architecture",
  component_diagram: "Components",
  folder_tree: "Folder Tree",
  module_dependency: "Module Dependencies",
  package_dependency: "Package Dependencies",
  call_graph: "Call Graph",
  class_diagram: "Class Diagram",
  er_diagram: "Database (ER)",
  api_flow: "API Flow",
  deployment_diagram: "Deployment",
  sequence_diagram: "Sequence (best-effort)",
  data_flow_diagram: "Data Flow",
};

export default function DiagramsTab({ jobId }: { jobId: string }) {
  const types = useQuery({ queryKey: ["diagram-types", jobId], queryFn: () => api.listDiagramTypes(jobId) });
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    if (types.data && types.data.length > 0 && !selected) {
      setSelected(types.data.includes("architecture_diagram") ? "architecture_diagram" : types.data[0]);
    }
  }, [types.data, selected]);

  if (!types.data || !selected) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Spinner className="h-4 w-4" />
        Loading diagrams…
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-1.5 rounded-xl border border-slate-200 bg-white p-1.5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        {types.data.map((t) => (
          <button
            key={t}
            onClick={() => setSelected(t)}
            className={`focus-ring rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              selected === t
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
            }`}
          >
            {LABELS[t] ?? t}
          </button>
        ))}
      </div>
      <DiagramViewer jobId={jobId} diagramType={selected} />
    </div>
  );
}
