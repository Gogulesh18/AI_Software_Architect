import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { api, apiErrorMessage } from "@/api/client";
import type { ChatSource } from "@/api/types";
import Button from "@/components/Button";
import Spinner from "@/components/Spinner";
import { SearchIcon, SendIcon } from "@/components/icons";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
}

const SUGGESTIONS = [
  "How does authentication work?",
  "Where is the database connected?",
  "Explain the request lifecycle",
  "Where are the repositories/services?",
];

export default function SearchTab({ jobId }: { jobId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");

  const send = useMutation({
    mutationFn: (question: string) =>
      api.chat(
        jobId,
        question,
        messages.map((m) => ({ role: m.role, content: m.content }))
      ),
    onSuccess: (res, question) => {
      setMessages((prev) => [...prev, { role: "user", content: question }, { role: "assistant", content: res.answer, sources: res.sources }]);
    },
  });

  const ask = (question: string) => {
    if (!question.trim() || send.isPending) return;
    setInput("");
    send.mutate(question);
  };

  return (
    <div className="flex h-[75vh] flex-col rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex-1 space-y-4 overflow-y-auto p-5">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <span className="flex h-11 w-11 items-center justify-center rounded-full bg-indigo-50 dark:bg-indigo-500/15">
              <SearchIcon className="h-5 w-5 text-indigo-500" />
            </span>
            <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">Ask a question about this repository</p>
            <div className="mt-4 flex max-w-md flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => ask(s)}
                  className="focus-ring rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-600 dark:border-slate-700 dark:text-slate-300 dark:hover:border-indigo-500/40 dark:hover:bg-indigo-500/10 dark:hover:text-indigo-300"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block max-w-[85%] whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-left text-sm shadow-sm ${
                m.role === "user"
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100"
              }`}
            >
              {m.content}
            </div>
            {m.sources && m.sources.length > 0 && (
              <div className="mt-1.5 flex flex-wrap gap-1">
                {m.sources.map((s, si) => (
                  <span key={si} className="rounded bg-slate-50 px-1.5 py-0.5 font-mono text-[11px] text-slate-400 dark:bg-slate-800/50">
                    {s.file}
                    {s.start_line ? `:${s.start_line}` : ""}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}

        {send.isPending && (
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Spinner className="h-4 w-4" />
            Thinking…
          </div>
        )}
        {send.isError && <p className="text-sm text-red-500">{apiErrorMessage(send.error)}</p>}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(input);
        }}
        className="flex gap-2 border-t border-slate-200 p-3 dark:border-slate-800"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about this codebase…"
          className="focus-ring flex-1 rounded-lg border border-slate-300 px-3.5 py-2.5 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
        />
        <Button type="submit" variant="primary" disabled={send.isPending}>
          <SendIcon className="h-4 w-4" />
          Ask
        </Button>
      </form>
    </div>
  );
}
