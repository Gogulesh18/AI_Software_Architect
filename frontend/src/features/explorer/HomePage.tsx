import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, apiErrorMessage } from "@/api/client";
import Button from "@/components/Button";
import Spinner from "@/components/Spinner";
import ThemeToggle from "@/components/ThemeToggle";
import {
  ApiIcon,
  DatabaseIcon,
  DiagramIcon,
  FindingsIcon,
  FolderIcon,
  GithubIcon,
  UploadIcon,
} from "@/components/icons";

type SourceMode = "url" | "zip" | "local";

const MODES: { key: SourceMode; label: string; icon: typeof GithubIcon }[] = [
  { key: "url", label: "GitHub URL", icon: GithubIcon },
  { key: "zip", label: "Upload ZIP", icon: UploadIcon },
  { key: "local", label: "Local folder", icon: FolderIcon },
];

const FEATURES = [
  { icon: DiagramIcon, label: "12 interactive diagrams" },
  { icon: DatabaseIcon, label: "Database & API detection" },
  { icon: FindingsIcon, label: "SOLID, security & performance" },
  { icon: ApiIcon, label: "RAG chat over your code" },
];

export default function HomePage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<SourceMode>("url");
  const [url, setUrl] = useState("");
  const [localPath, setLocalPath] = useState("");
  const [zipFile, setZipFile] = useState<File | null>(null);

  const repos = useQuery({ queryKey: ["repos"], queryFn: api.listRepos });

  const submit = useMutation({
    mutationFn: async () => {
      if (mode === "url") return api.createFromUrl(url);
      if (mode === "local") return api.createFromLocal(localPath);
      if (!zipFile) throw new Error("Choose a .zip file first");
      return api.createFromZip(zipFile);
    },
    onSuccess: (job) => navigate(`/jobs/${job.id}/report`),
  });

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Decorative background: soft radial glow, purely cosmetic */}
      <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute left-1/2 top-[-12rem] h-[36rem] w-[64rem] -translate-x-1/2 rounded-full bg-gradient-to-br from-indigo-200/60 via-violet-100/40 to-transparent blur-3xl dark:from-indigo-500/15 dark:via-violet-500/10 dark:to-transparent" />
      </div>

      <div className="absolute right-6 top-6">
        <ThemeToggle />
      </div>

      <div className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center px-6 py-16">
        <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-lg font-bold text-white shadow-lg shadow-indigo-600/30">
          AI
        </span>

        <h1 className="mt-6 text-center text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-4xl">
          AI Software Architect
        </h1>
        <p className="mt-3 max-w-lg text-center text-slate-500 dark:text-slate-400">
          Point it at any repository and get architecture style, design patterns, SOLID analysis, database & API
          detection, engineering scores, and an executive report — in seconds.
        </p>

        <div className="mt-6 flex flex-wrap justify-center gap-2">
          {FEATURES.map((f) => (
            <span
              key={f.label}
              className="flex items-center gap-1.5 rounded-full border border-slate-200 bg-white/60 px-3 py-1 text-xs font-medium text-slate-500 backdrop-blur dark:border-slate-800 dark:bg-slate-900/60 dark:text-slate-400"
            >
              <f.icon className="h-3.5 w-3.5 text-indigo-500" />
              {f.label}
            </span>
          ))}
        </div>

        <div className="mt-8 w-full rounded-2xl border border-slate-200 bg-white/90 p-6 shadow-xl shadow-slate-200/50 backdrop-blur dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-black/20">
          <div className="grid grid-cols-3 gap-1.5 rounded-xl bg-slate-100 p-1 dark:bg-slate-800">
            {MODES.map((m) => (
              <button
                key={m.key}
                onClick={() => setMode(m.key)}
                className={`focus-ring flex items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
                  mode === m.key
                    ? "bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white"
                    : "text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                }`}
              >
                <m.icon className="h-4 w-4" />
                <span className="hidden sm:inline">{m.label}</span>
              </button>
            ))}
          </div>

          <form
            className="mt-5 flex flex-col gap-3"
            onSubmit={(e) => {
              e.preventDefault();
              submit.mutate();
            }}
          >
            {mode === "url" && (
              <input
                type="text"
                placeholder="https://github.com/owner/repo"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="focus-ring rounded-lg border border-slate-300 px-3.5 py-2.5 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              />
            )}
            {mode === "local" && (
              <input
                type="text"
                placeholder="C:\path\to\repo"
                value={localPath}
                onChange={(e) => setLocalPath(e.target.value)}
                className="focus-ring rounded-lg border border-slate-300 px-3.5 py-2.5 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              />
            )}
            {mode === "zip" && (
              <label className="focus-ring flex cursor-pointer items-center justify-center gap-2 rounded-lg border-2 border-dashed border-slate-300 px-3.5 py-4 text-sm text-slate-500 transition-colors hover:border-indigo-400 hover:text-indigo-600 dark:border-slate-700 dark:text-slate-400 dark:hover:border-indigo-500">
                <UploadIcon className="h-4 w-4" />
                {zipFile ? zipFile.name : "Choose a .zip file"}
                <input type="file" accept=".zip" onChange={(e) => setZipFile(e.target.files?.[0] ?? null)} className="hidden" />
              </label>
            )}

            <Button type="submit" variant="primary" disabled={submit.isPending} className="w-full">
              {submit.isPending ? (
                <>
                  <Spinner className="h-4 w-4 text-white/80" />
                  Starting analysis…
                </>
              ) : (
                "Analyze"
              )}
            </Button>

            {submit.isError && <p className="text-sm text-red-600 dark:text-red-400">{apiErrorMessage(submit.error)}</p>}
          </form>
        </div>

        {repos.data && repos.data.length > 0 && (
          <div className="mt-8 w-full">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">Recent repositories</h2>
            <ul className="mt-2 divide-y divide-slate-200 overflow-hidden rounded-xl border border-slate-200 bg-white dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-900">
              {repos.data.map((r) => (
                <li key={r.id} className="flex items-center gap-2 px-4 py-2.5 text-sm text-slate-700 dark:text-slate-300">
                  <FolderIcon className="h-4 w-4 shrink-0 text-slate-400" />
                  {r.name} <span className="text-slate-400">({r.source_type})</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
