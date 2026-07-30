import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import ReactFlow, { Background, Controls, MiniMap, type Edge, type Node } from "reactflow";
import "reactflow/dist/style.css";
import { api } from "@/api/client";
import Spinner from "@/components/Spinner";
import { DiagramIcon } from "@/components/icons";
import { layoutGraph } from "./layout";
import { nodeTypes } from "./nodeTypeRegistry";

function CenteredState({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-[70vh] flex-col items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white text-sm text-slate-400 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      {children}
    </div>
  );
}

export default function DiagramViewer({ jobId, diagramType }: { jobId: string; diagramType: string }) {
  const diagram = useQuery({
    queryKey: ["diagram", jobId, diagramType],
    queryFn: () => api.getDiagram(jobId, diagramType),
  });

  const { nodes, edges } = useMemo(() => {
    if (!diagram.data) return { nodes: [] as Node[], edges: [] as Edge[] };

    const rawNodes: Node[] = diagram.data.nodes.map((n) => ({
      id: n.id,
      type: n.type,
      data: n.data,
      position: { x: 0, y: 0 },
    }));
    const rawEdges: Edge[] = diagram.data.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.label,
      animated: e.type === "calls",
      style: { stroke: "#818cf8", strokeWidth: 1.5 },
      labelStyle: { fill: "#6366f1", fontSize: 11, fontWeight: 600 },
      labelBgStyle: { fill: "#eef2ff", fillOpacity: 0.9 },
      labelBgPadding: [4, 2] as [number, number],
      labelBgBorderRadius: 4,
    }));

    return { nodes: layoutGraph(rawNodes, rawEdges), edges: rawEdges };
  }, [diagram.data]);

  if (diagram.isLoading) {
    return (
      <CenteredState>
        <Spinner className="h-5 w-5" />
        Loading diagram…
      </CenteredState>
    );
  }
  if (diagram.isError) {
    return <CenteredState>Failed to load this diagram.</CenteredState>;
  }
  if (nodes.length === 0) {
    return (
      <CenteredState>
        <DiagramIcon className="h-8 w-8 text-slate-300 dark:text-slate-700" />
        Nothing detected for this diagram type.
      </CenteredState>
    );
  }

  return (
    <div className="h-[70vh] overflow-hidden rounded-2xl border border-slate-200 shadow-sm dark:border-slate-800">
      {diagram.data?.truncated && (
        <div className="border-b border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-700 dark:border-amber-900 dark:bg-amber-900/30 dark:text-amber-300">
          This diagram was truncated to keep it readable — showing the first {nodes.length} nodes.
        </div>
      )}
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView proOptions={{ hideAttribution: true }} className="!bg-slate-50 dark:!bg-slate-950">
        <Background gap={20} color="#cbd5e1" className="dark:opacity-20" />
        <Controls className="!shadow-md [&>button]:!border-slate-200 [&>button]:!bg-white dark:[&>button]:!border-slate-700 dark:[&>button]:!bg-slate-800 dark:[&>button]:!fill-slate-300" />
        <MiniMap pannable zoomable className="!bg-white !shadow-md dark:!bg-slate-900" />
      </ReactFlow>
    </div>
  );
}
