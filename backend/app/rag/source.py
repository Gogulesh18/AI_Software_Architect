"""Serves source snippets for the frontend's Monaco drill-down view.

The cloned/extracted repo is deleted after analysis (see
app.workers.pipeline) — there's no raw filesystem to read from afterwards.
Instead this reads back the text already captured in the per-job Chroma
collection during indexing (app.rag.indexer), which is fine for "show me
this function/class/file's source" but won't perfectly reconstruct a whole
file: only symbols (and, for shallow-parsed files, line windows) are
chunked, so gaps between chunks (e.g. bare module-level statements between
functions) aren't stored.
"""

from app.rag.store import get_by_file


def get_source_chunks(job_id: str, file_path: str) -> list[dict]:
    chunks = get_by_file(job_id, file_path)
    chunks.sort(key=lambda c: c["start_line"] or 0)
    return chunks
