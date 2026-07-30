# AI Software Architect — Architecture

Living source of truth for system design and technology decisions. Update this file whenever
the architecture changes; don't let it drift from the code.

## What this is

Given a GitHub repo URL, a ZIP file, or a local folder, the platform ingests the codebase,
parses it across 10 deeply-analyzed languages (plus 40+ more at a shallow, language-labeled
level), builds a knowledge graph, and produces a full architecture report: architecture style +
confidence, folder responsibilities, dependency graphs, database ER diagrams, API flow, design
pattern detection, SOLID analysis, code quality/security/performance findings, and nine
engineering scores — plus 12 interactive diagram types (React Flow) and a RAG chat interface
for asking questions about the repo.

This is an architecture *explainer*, not a code reviewer, linter, or compiler. Every detector
is a heuristic — see [What's heuristic vs. deterministic](#whats-heuristic-vs-deterministic).

## System shape

**Modular monolith backend (FastAPI)**, not microservices. Internal packages have hard
boundaries (see Folder Structure below) so the system *could* be decomposed into services
later, but a single deployable process is the right call now: the workload is CPU/IO-bound
repo analysis with no independent scaling needs per component, and a monolith is dramatically
simpler to run and debug locally.

## Request/analysis flow

```
User (React SPA)
   │  POST /api/repos/{url|zip|local} → creates AnalysisJob (status=queued), returns job id
   ▼
FastAPI API layer
   ▼
Job runner (asyncio background task locally / Celery worker in prod mode)
   │
   ├─ ingest/    → clone (GitPython) or unzip (zip-slip-safe) or read a local folder;
   │               enumerate files; apply ignore rules
   ├─ parser/    → language detection + Tree-sitter structural extraction per file
   │               (imports, classes, functions, decorators, base classes, complexity,
   │               nesting depth) for 10 languages; language-labeled LOC count for the rest
   ├─ graph/     → NetworkX knowledge graph (file/class/function/method nodes;
   │               imports/defines/inherits/calls edges) + repo summary + folder tree
   ├─ analyzer/  → architecture style + confidence, database/API detection, design patterns,
   │               SOLID, code quality, security, performance, then the 9 engineering scores
   │               — all rule-based (regex/AST heuristics), no LLM involved
   ├─ diagram/   → derive React Flow-ready {nodes, edges} JSON for 12 diagram types from the
   │               graph/analysis — pure data transforms, no LLM, no server-side layout
   ├─ llm/report → executive report Markdown: rule-based facts in, LLM prose out (falls back
   │               to a deterministic Markdown template with no LLM configured)
   └─ rag/       → chunk parsed symbols, embed (local, fastembed), upsert into a per-job
                    Chroma collection — powers both the Search/chat tab and the Monaco
                    source-snippet viewer (the cloned repo is deleted after the job finishes)
   │
   ▼
Results persisted (SQLAlchemy: AnalysisResult, one row per job) → AnalysisJob.status=done
   ▼
Frontend polls job status/stage/progress → fetches result/diagrams/report → renders;
Search tab hits /api/jobs/{id}/chat (RAG, LLM-synthesized or raw-context fallback)
```

**Rule-based detection, LLM for narrative.** Pattern/SOLID/security/complexity findings come
from deterministic AST + graph queries — cheap, reproducible, and explainable with exact
`file:line` references and a `reason`/`message` string. The LLM only handles narrative
synthesis (executive report prose) and RAG chat answers, never the detection itself. This
bounds cost/latency on large repos, keeps every finding auditable back to source, and means
**the whole analysis pipeline runs with zero API keys** — only the report's prose and chat's
synthesis degrade (to a template and to raw-context-only, respectively) without
`ANTHROPIC_API_KEY`.

**Analysis is always an async job**, even in low-ceremony local dev. Cloning/parsing/analyzing
a real repo takes seconds to minutes; the API returns a job id immediately and the frontend
polls status every second. This shaped the DB schema and API contracts from day one.

## Folder structure

```
ai-software-architect/
├── frontend/                        React + TypeScript + Vite + Tailwind
│   └── src/
│       ├── api/                     typed client + TS types (verified against live responses)
│       ├── components/              Sidebar, StatusBadge, ThemeToggle
│       ├── store/                   React Query client, dark-mode hook
│       └── features/
│           ├── explorer/            upload form, folder tree, Monaco code viewer
│           ├── diagrams/            React Flow viewer + dagre layout + per-type node renderers
│           ├── report/              Markdown report view + export buttons
│           ├── scores/              Recharts radar + reasoning cards
│           ├── database/            ER table/column/relationship list view
│           ├── api/                 endpoint table + auth summary
│           ├── findings/            patterns/SOLID/quality/security/performance browser
│           ├── search/              RAG chat panel
│           └── job/                 job status polling + tab routing shell
│
├── backend/
│   └── app/
│       ├── api/                     FastAPI routers (repos, jobs/result/diagrams/report/
│       │                            source/chat/export)
│       ├── ingest/                  clone/unzip/local-folder materialization, ignore rules
│       ├── parser/                  language detection, Tree-sitter extraction, ecosystem
│       │                            (framework) detection
│       ├── graph/                   NetworkX graph builder, JSON (de)serialization, repo
│       │                            summary + folder tree
│       ├── analyzer/
│       │   ├── architecture/        style classification + confidence score
│       │   ├── database.py          ORM/model detection → tables/columns/PK/FK
│       │   ├── api_surface.py       REST/GraphQL/gRPC/WebSocket + auth detection
│       │   ├── patterns/            design pattern detectors (Factory, Singleton, ...)
│       │   ├── solid/               SRP/OCP/LSP/ISP/DIP violation heuristics
│       │   ├── quality/             complexity, long/god/large classes, dead/duplicate code
│       │   ├── security/            secrets, injection, unsafe deserialization, weak hashing
│       │   ├── performance/         N+1, blocking calls, nested loops, missing cache
│       │   ├── scoring/             aggregates everything into the 9 engineering scores
│       │   └── pipeline.py          run_all_analyzers() — the one contract workers/ depends on
│       ├── diagram/                 12 graph → React Flow JSON transforms + pipeline.py
│       ├── llm/                     pluggable LLMProvider (Anthropic default) + report.py
│       ├── embeddings/              pluggable EmbeddingProvider (fastembed default)
│       ├── rag/                     chunking, Chroma store, chat synthesis, source lookup
│       ├── export/                  Markdown / JSON / PDF export
│       ├── database/                SQLAlchemy models (Repository, AnalysisJob,
│       │                            AnalysisResult), session
│       ├── workers/                 pipeline.py (the 8-stage orchestration), runner.py
│       │                            (asyncio/Celery dispatch), celery_app.py
│       └── core/                    config (pydantic-settings), logging, exceptions
│   └── tests/                       mirrors app/ — 151 tests, ~91% coverage
│
├── docker-compose.yml                prod-mode: postgres, redis, celery worker, backend, frontend
├── .env.example
└── README.md
```

> Deviation from the original brief: `parser/ graph/ analyzer/ diagram/ llm/ rag/ embeddings/
> database/ workers/` live inside `backend/app/` rather than at the repo root — idiomatic
> FastAPI layout, avoids ambiguous Python import roots. `database.py`/`api_surface.py`/`export/`
> weren't in the original folder list — added because the brief's Database/API Detection and
> Export features needed a home; `export/` is a new top-level package, the other two are flat
> modules under `analyzer/` (no subpackage needed, unlike the areas with multiple detector files).

## Technology decisions

| Area | Choice | Why |
|---|---|---|
| Backend framework | FastAPI + Pydantic v2 | async-native (job polling/streaming), auto OpenAPI drives the typed frontend client |
| DB (dev) | SQLite via SQLAlchemy | zero-setup locally; models are DB-agnostic, so Postgres is a connection-string swap |
| DB (prod) | PostgreSQL | concurrent writes, JSON columns for graph/report blobs |
| Background jobs (dev) | asyncio `create_task`, in-process | no Redis/Celery required to run locally; endpoints are `async def` specifically so the task schedules onto FastAPI's own event loop rather than a sync-dependency threadpool (see "Bugs found" below) |
| Background jobs (prod) | Celery + Redis | same `run_analysis_job` pipeline, dispatched via a worker process instead of asyncio — not exercised by the local test suite (no Redis in dev) |
| Repo parsing | Tree-sitter via `tree_sitter_language_pack` | one AST abstraction across many languages; the installed package turned out to be a newer, actively-maintained rewrite (v1.13, 306 languages, downloads-on-demand with the common ones bundled) rather than the older static-bundle package the name suggests — verified node-type-by-node-type against its actual grammars for all 10 deep-parsed languages rather than assumed |
| Graph | NetworkX (`MultiDiGraph`) | in-memory, sufficient at single-repo scale, serializes cleanly to JSON for React Flow |
| Vector store | Chroma, local persistent mode, one collection per job | no separate server process to run; a job's collection is independently droppable |
| Embeddings | Local (fastembed, ONNX, CPU, `BAAI/bge-small-en-v1.5`) | works with only an Anthropic key — no second paid API required; pluggable |
| LLM | Anthropic Claude, pluggable `llm/` interface | narrative synthesis + RAG answers only, not detection logic; `is_available` lets every caller degrade gracefully with no key |
| PDF export | fpdf2 | pure-Python, no system deps (no wkhtmltopdf/Chromium needed); latin-1-only core fonts, so LLM-generated Markdown is transliterated before rendering (see "Bugs found") |
| Frontend | React + TypeScript + Vite | fast local dev, strong typing across a large surface area |
| Styling | TailwindCSS + `@tailwindcss/typography` | typography plugin renders the Markdown report readably |
| Diagrams | React Flow + `dagre` | backend emits plain nodes/edges JSON with no positions; frontend runs dagre for auto-layout |
| Code viewer | Monaco Editor | reads from the RAG chunk store (see rag/source.py), not the filesystem — the cloned repo is deleted right after analysis |
| Charts | Recharts | single-series radar chart for the 8 category scores; status colors (score bands) kept out of the categorical/sequential palette question entirely |
| Server state (frontend) | TanStack React Query | job polling, result/diagram caching |
| Auth / multi-tenancy | Out of scope | self-hosted/local tool; revisit if this becomes a hosted multi-user SaaS |

## API surface (backend)

```
POST /api/repos/url            {url}              → Job
POST /api/repos/zip            multipart file      → Job
POST /api/repos/local           {path}              → Job
GET  /api/repos                                      → Repository[]
GET  /api/jobs/{id}                                   → Job (status/stage/progress/error)
GET  /api/jobs/{id}/result                            → summary/architecture/database/api/
                                                          patterns/solid/quality/security/
                                                          performance/scores
GET  /api/jobs/{id}/diagrams                          → available diagram type names
GET  /api/jobs/{id}/diagrams/{type}                   → {nodes, edges, truncated}
GET  /api/jobs/{id}/report                            → Markdown
GET  /api/jobs/{id}/source?file=...                   → chunks (from the RAG store)
POST /api/jobs/{id}/chat        {message, history}    → {answer, sources}
GET  /api/jobs/{id}/export/{markdown|json|pdf}         → file download
```

## Diagram types

`folder_tree`, `module_dependency`, `package_dependency`, `call_graph`, `class_diagram`,
`architecture_diagram`, `component_diagram`, `er_diagram`, `api_flow`, `deployment_diagram`,
`sequence_diagram`, `data_flow_diagram` — all pure graph/analysis-data transforms (no LLM), one
function each under `backend/app/diagram/`.

## What's heuristic vs. deterministic

**Deterministic:** language detection, Tree-sitter parsing (imports/classes/functions/
decorators/base-classes/complexity for the 10 deep-parsed languages), the knowledge graph, repo
summary/folder tree, framework/ecosystem detection (manifest-file-driven).

**Heuristic (documented in each module's docstring, not hidden):** architecture style
(weighted folder-name/file/ecosystem signals, not a classifier), design patterns (naming
convention + method-signature matching, the same thing a reviewer does at a glance), SOLID
violations (textbook smells: god classes for SRP, type-switches for OCP, stubbed overrides for
LSP, fat `I*` interfaces for ISP, direct construction for DIP), dead-code detection (zero
*resolved* callers in this repo's graph — under-reports real usage whenever a caller lives
across a reference the best-effort import/call resolver couldn't link), security/performance
findings (pattern-based, not taint-tracking — catches recognizable forms, not obfuscated ones),
and all 9 engineering scores (penalty-based aggregation of the above, not ML-derived).

Import/call/base-class graph edges are resolved conservatively: an ambiguous reference (a name
matching more than one candidate) is left unlinked rather than guessed, so the graph never
accumulates wrong edges — at the cost of under-connecting large repos with duplicate symbol
names across files.

## Bugs found and fixed during the build (kept here as institutional memory)

- **API surface double-counting**: the Express route regex (`app.get(...)`) also matched
  inside FastAPI's `@app.get(...)` decorator syntax, since the decorator text contains that
  substring. Fixed with a negative lookbehind excluding `@`-prefixed matches.
- **PDF export crash on Unicode**: fpdf2's core fonts (Helvetica/Courier) are latin-1 only;
  LLM-generated Markdown routinely contains smart quotes/em-dashes. Fixed by transliterating
  the common ones and replacing anything else rather than crashing.
- **PDF export crash on consecutive lines**: fpdf2's `multi_cell` defaults to
  `new_x=XPos.RIGHT`, leaving the draw cursor near the right margin after every call. Two
  non-blank report lines in a row (no blank line between them — e.g. a heading immediately
  followed by a bullet) left the next line almost no horizontal space, and fpdf2 raised
  `FPDFException("Not enough horizontal space...")`. Fixed by forcing `new_x="LMARGIN"` on
  every line.
- **Background job silently never ran**: `asyncio.create_task()` inside a *sync* `def` FastAPI
  endpoint raised `RuntimeError: no current event loop` — FastAPI runs sync path functions in a
  worker thread via `run_in_threadpool`, which has no asyncio event loop of its own. Fixed by
  making the repo-creation endpoints `async def` so they execute on the main event loop, where
  `asyncio.create_task()` can actually find a running loop.
- **SQLAlchemy `id` was `None` at use time**: `Repository(...)`'s `id` column has a Python-side
  default (`default=uuid4`), which SQLAlchemy applies at *flush*, not at object construction —
  code that read `repository.id` immediately after constructing the object (to build a
  dependent `AnalysisJob(repository_id=repository.id)`, or a ZIP upload's destination filename)
  got `None`. Fixed by flushing first (or generating the UUID explicitly upfront for the
  ZIP-upload case, where the id is needed before the object is even added to the session).
- **React hooks-order violation**: `JobPage` returned early (`if (!jobId) return <Navigate />`)
  *before* calling `useQuery()` — a real rules-of-hooks violation, not just a lint nitpick,
  since the hook-call sequence would differ between renders. Fixed by moving all hooks above
  any conditional return and gating them with `enabled: !!jobId` instead.
- **Vite couldn't resolve `@/...` imports**: the `@` path alias was only declared in
  `tsconfig.app.json`, which TypeScript's type-checker honors but Vite/Rollup's bundler does
  not — `npm run build` failed on every absolute import until the same alias was added to
  `vite.config.ts`'s `resolve.alias`.

## Roadmap (all phases complete)

1. System architecture, folder structure, technology decisions. ✅
2. Repository parser, language detection, knowledge graph. ✅
3. Architecture analyzer, pattern detection, SOLID analysis. ✅
4. Diagram generation. ✅
5. AI RAG, embeddings, LLM report synthesis, export. ✅
6. Frontend. ✅
7. Testing, optimization, documentation. ✅

Natural next steps if this continues: Alembic migrations for the Postgres/prod path (SQLite
dev mode auto-creates tables; Postgres prod mode doesn't have a migration yet), an OpenAI
`LLMProvider`/`EmbeddingProvider` implementation behind the existing interfaces, and
persisted multi-turn chat history (currently stateless — the frontend carries history per
request) if this becomes a hosted multi-user product.
