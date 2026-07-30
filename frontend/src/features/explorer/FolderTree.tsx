import { useState } from "react";
import type { FolderTreeNode } from "@/api/types";
import { ChevronRightIcon, FileIcon, FolderIcon } from "@/components/icons";

function Node({ node, depth, onSelectFile }: { node: FolderTreeNode; depth: number; onSelectFile: (path: string) => void }) {
  const [open, setOpen] = useState(depth < 1);

  if (node.type === "file") {
    return (
      <button
        onClick={() => onSelectFile(node.path)}
        className="focus-ring flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
        style={{ paddingLeft: depth * 16 + 8 }}
      >
        <FileIcon className="h-3.5 w-3.5 shrink-0 text-slate-400" />
        <span className="truncate">{node.name}</span>
        {node.language && <span className="ml-auto shrink-0 text-xs text-slate-400">{node.language}</span>}
      </button>
    );
  }

  return (
    <div>
      <button
        onClick={() => setOpen((o) => !o)}
        className="focus-ring flex w-full items-center gap-1.5 rounded-lg px-2 py-1.5 text-left text-sm font-medium text-slate-800 transition-colors hover:bg-slate-100 dark:text-slate-100 dark:hover:bg-slate-800"
        style={{ paddingLeft: depth * 16 + 8 }}
      >
        <ChevronRightIcon className={`h-3.5 w-3.5 shrink-0 text-slate-400 transition-transform ${open ? "rotate-90" : ""}`} />
        <FolderIcon className="h-3.5 w-3.5 shrink-0 text-indigo-400" />
        <span className="truncate">{node.name || "/"}</span>
        <span className="ml-auto shrink-0 text-xs font-normal text-slate-400">{node.file_count} files</span>
      </button>
      {open && node.children?.map((child) => <Node key={child.path || child.name} node={child} depth={depth + 1} onSelectFile={onSelectFile} />)}
    </div>
  );
}

export default function FolderTree({ tree, onSelectFile }: { tree: FolderTreeNode; onSelectFile: (path: string) => void }) {
  return (
    <div className="max-h-[70vh] overflow-y-auto rounded-2xl border border-slate-200 bg-white p-2 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <Node node={tree} depth={0} onSelectFile={onSelectFile} />
    </div>
  );
}
