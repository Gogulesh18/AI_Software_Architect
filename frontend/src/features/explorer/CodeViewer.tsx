import Editor from "@monaco-editor/react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import Spinner from "@/components/Spinner";
import { useTheme } from "@/store/theme";

const EXTENSION_LANG: Record<string, string> = {
  py: "python", js: "javascript", jsx: "javascript", ts: "typescript", tsx: "typescript",
  java: "java", go: "go", rs: "rust", php: "php", cs: "csharp", cpp: "cpp", c: "c",
  json: "json", yaml: "yaml", yml: "yaml", md: "markdown", html: "html", css: "css",
};

function languageFor(path: string): string {
  const ext = path.split(".").pop() ?? "";
  return EXTENSION_LANG[ext] ?? "plaintext";
}

export default function CodeViewer({ jobId, filePath, onClose }: { jobId: string; filePath: string; onClose: () => void }) {
  const { theme } = useTheme();
  const source = useQuery({
    queryKey: ["source", jobId, filePath],
    queryFn: () => api.getSource(jobId, filePath),
  });

  const text =
    source.data?.chunks
      .map((c) => `// lines ${c.start_line}-${c.end_line}${c.symbol ? ` (${c.symbol})` : ""}\n${c.text}`)
      .join("\n\n") ?? "";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-6 backdrop-blur-sm">
      <div className="flex h-full w-full max-w-4xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-black/5 dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-4 py-2.5 dark:border-slate-800 dark:bg-slate-800/50">
          <span className="truncate font-mono text-sm text-slate-700 dark:text-slate-200">{filePath}</span>
          <button
            onClick={onClose}
            className="focus-ring rounded-lg px-2.5 py-1 text-sm font-medium text-slate-500 transition-colors hover:bg-slate-200/60 dark:hover:bg-slate-700"
          >
            Close
          </button>
        </div>
        {!source.data ? (
          <div className="flex flex-1 items-center justify-center gap-2 text-sm text-slate-400">
            <Spinner className="h-4 w-4" />
            Loading source…
          </div>
        ) : source.data.chunks.length === 0 ? (
          <p className="flex flex-1 items-center justify-center p-4 text-sm text-slate-400">No indexed source available for this file.</p>
        ) : (
          <Editor
            height="100%"
            language={languageFor(filePath)}
            value={text}
            theme={theme === "dark" ? "vs-dark" : "light"}
            options={{ readOnly: true, minimap: { enabled: false }, fontSize: 13 }}
          />
        )}
      </div>
    </div>
  );
}
