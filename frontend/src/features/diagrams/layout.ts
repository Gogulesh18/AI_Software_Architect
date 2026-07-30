import dagre from "dagre";
import type { Edge, Node } from "reactflow";

const NODE_WIDTH = 200;
const NODE_HEIGHT = 60;

/** Backend emits plain {nodes, edges} with no positions (see ARCHITECTURE.md:
 * the backend owns graph data, the frontend owns layout). dagre gives every
 * diagram type a readable top-to-bottom/left-to-right layout for free. */
export function layoutGraph(nodes: Node[], edges: Edge[], direction: "TB" | "LR" = "TB"): Node[] {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: direction, nodesep: 40, ranksep: 70 });

  for (const node of nodes) {
    const height = estimateHeight(node);
    g.setNode(node.id, { width: NODE_WIDTH, height });
  }
  for (const edge of edges) {
    if (g.hasNode(edge.source) && g.hasNode(edge.target)) {
      g.setEdge(edge.source, edge.target);
    }
  }

  dagre.layout(g);

  return nodes.map((node) => {
    const pos = g.node(node.id);
    if (!pos) return node;
    return {
      ...node,
      position: { x: pos.x - NODE_WIDTH / 2, y: pos.y - estimateHeight(node) / 2 },
    };
  });
}

function estimateHeight(node: Node): number {
  const methods = (node.data?.methods as unknown[] | undefined)?.length ?? 0;
  const columns = (node.data?.columns as unknown[] | undefined)?.length ?? 0;
  const extraRows = Math.max(methods, columns);
  return NODE_HEIGHT + Math.min(extraRows, 8) * 16;
}
