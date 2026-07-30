# AI Software Architect

Analyzes an entire repository — GitHub URL, ZIP, or local folder — and explains how the
software is built from an architectural perspective: architecture style, folder
responsibilities, dependency/database/API graphs, design patterns, SOLID analysis, code
quality/security/performance findings, engineering scores, interactive diagrams, and a RAG
chat interface for asking questions about the codebase.

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full system design, technology decisions, and
the heuristic limits of each analyzer (this is a static-analysis tool, not a compiler — it's
upfront about what's deterministic vs. best-effort).

**Status: feature-complete** (Phases 1–7). 151 backend tests / 91% coverage, frontend
typecheck+lint+build clean, verified end-to-end against a live backend over HTTP.

## Repository layout

```
frontend/   React + TypeScript + Vite + Tailwind SPA
backend/    FastAPI app: ingest, parse, graph, analyze, diagram, RAG, export
```

## Running locally (dev mode — no Docker required)

Dev mode uses SQLite and in-process background tasks: only Python 3.11+ and Node 20+ are
required.

```bash
# Backend
cd backend
python -m venv .venv
./.venv/Scripts/activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -e ".[dev]"
cp ../.env.example ../.env      # then fill in ANTHROPIC_API_KEY (optional — see below)
uvicorn app.main:app --reload   # http://localhost:8000, docs at /docs

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                     # http://localhost:5173, proxies /api to http://localhost:8000
```

Open http://localhost:5173, paste a GitHub URL (or upload a ZIP, or point at a local folder),
and watch it analyze.

### Running without an Anthropic API key

`ANTHROPIC_API_KEY` is optional, not required. Without it:
- The executive report is generated from a deterministic Markdown template (facts only, no
  LLM prose) instead of `llm.complete()`.
- The Search/chat tab returns the raw retrieved code chunks instead of an LLM-synthesized
  answer.

Everything else (parsing, graph, architecture/pattern/SOLID/quality/security/performance
analysis, diagrams, database/API detection, scoring, export) runs entirely offline with no
API key at all — only the embedding model (local, via fastembed) is downloaded once on first
use.

## Running in VS Code

Open the repo root (`ai-software-architect/`, the folder containing this README) as a single
VS Code workspace — not `backend/` or `frontend/` individually, so the committed `.vscode/`
config (interpreter path, tasks, debug configs) applies.

1. **Install the recommended extensions** — VS Code will prompt automatically on open
   ("Show Recommendations"); or install manually: Python, Pylance, Ruff, ESLint, Tailwind CSS
   IntelliSense.
2. **First-time setup** — Terminal → Run Task →
   - `Backend: Install deps` (creates nothing itself; run `python -m venv .venv` inside
     `backend/` first if `.venv` doesn't exist yet, then this task)
   - `Frontend: Install deps`
3. **Copy the env file**: `cp .env.example .env` at the repo root, fill in `ANTHROPIC_API_KEY`
   (optional — see below).
4. **Run both dev servers** — Terminal → Run Task → `Run Full Stack (backend + frontend)`
   (runs `Backend: Run dev server` and `Frontend: Run dev server` in parallel dedicated
   terminal panels), or run either one individually the same way.
5. **Debugging the backend** — Run and Debug panel (`Ctrl+Shift+D`) →
   `Backend: FastAPI (uvicorn --reload)` to hit breakpoints in any route/analyzer/parser code,
   or `Backend: Pytest (current file)` with a test file open to debug a specific test.
6. **Running tests from the Testing panel** — the Python extension auto-discovers
   `backend/tests/` via the committed `python.testing.*` settings; click any test to run/debug
   it directly.

The Python interpreter is pre-wired to `backend/.venv/Scripts/python.exe` and ESLint is scoped
to `frontend/` — both via `.vscode/settings.json`, already committed, nothing to configure.

## Running in production mode (Docker Compose)

Brings up Postgres, Redis, a Celery worker, the backend, and the frontend together:

```bash
cp .env.example .env   # fill in ANTHROPIC_API_KEY at minimum
docker compose up --build
```

## Configuration

All configuration is environment-driven — see [.env.example](./.env.example) for the full list
(LLM provider/model, embedding provider, database URL, job runner, vector store location).

## Testing

```bash
# Backend — 151 tests, ~91% coverage, no network required except one live model
# download the first time fastembed runs (cached after that)
cd backend
./.venv/Scripts/python.exe -m pytest tests/ -q
./.venv/Scripts/python.exe -m pytest tests/ -q --cov=app --cov-report=term-missing

# Frontend
cd frontend
npx tsc -b --noEmit   # typecheck
npm run lint
npm run build          # production build
```

`tests/api/test_full_pipeline.py` is the key integration test: it POSTs a real local repo
through the HTTP API, polls the background job to completion, and checks every read endpoint
the frontend calls (result, diagrams, report, chat, export×3) — the full
ingest → parse → graph → analyze → diagram → report → embed pipeline, exercised together.

## What's heuristic vs. deterministic

Parsing (Tree-sitter), the knowledge graph, and repository/folder statistics are exact for the
10 deeply-parsed languages (Python, JS, TS, Java, Go, Rust, PHP, C#, C++, C) and best-effort
(language-labeled, not AST-parsed) for everything else. Architecture style, design patterns,
SOLID violations, and the 9 engineering scores are rule-based heuristics — the same signals an
experienced reviewer would look for (naming conventions, method-name overlap, folder layout,
annotation markers) — not formal verification. Every finding carries a file:line reference and
a `reason`/`message` explaining exactly what triggered it, so results are auditable even when
the underlying rule is approximate. See ARCHITECTURE.md for specifics per analyzer.

## Development phases

Built in reviewed phases (see ARCHITECTURE.md's Roadmap section): architecture/scaffold →
parser/knowledge graph → architecture analyzer → diagrams → RAG/export → frontend →
testing/docs. Each phase landed working, tested code before the next began.
