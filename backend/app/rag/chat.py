"""RAG chat: embed the question, retrieve relevant chunks, synthesize an
answer grounded in them. Falls back to returning the raw retrieved context
(no synthesis) when no LLM is configured, so the search feature still works
without an API key — just without prose."""

from app.embeddings import get_embedding_provider
from app.llm import get_llm_provider
from app.rag.store import query as query_store

TOP_K = 6

_SYSTEM_PROMPT = """You are an AI Software Architect answering questions about a specific \
codebase ({repo_name}) using only the retrieved code excerpts below. Cite the file (and line \
range, if given) for any claim you make. If the excerpts don't contain the answer, say so \
plainly instead of guessing."""


def answer_question(job_id: str, repo_name: str, message: str, history: list[dict[str, str]]) -> tuple[str, list[dict]]:
    embedder = get_embedding_provider()
    query_embedding = embedder.embed_one(message)
    hits = query_store(job_id, query_embedding, top_k=TOP_K)

    sources = [
        {
            "file": hit["metadata"].get("file"),
            "start_line": hit["metadata"].get("start_line"),
            "end_line": hit["metadata"].get("end_line"),
            "symbol": hit["metadata"].get("symbol"),
        }
        for hit in hits
    ]

    llm = get_llm_provider()
    if not llm.is_available:
        return _fallback_answer(hits), sources

    context = "\n\n".join(_format_context_block(hit) for hit in hits) or "(no relevant code found in this repository)"

    messages = list(history) + [{"role": "user", "content": f"Retrieved context:\n\n{context}\n\nQuestion: {message}"}]
    answer = llm.chat(_SYSTEM_PROMPT.format(repo_name=repo_name), messages, max_tokens=1200)
    return answer, sources


def _format_context_block(hit: dict) -> str:
    meta = hit["metadata"]
    symbol_suffix = f" ({meta.get('symbol')})" if meta.get("symbol") else ""
    header = f"### {meta.get('file')}{symbol_suffix} [lines {meta.get('start_line')}-{meta.get('end_line')}]"
    return f"{header}\n```\n{hit['text']}\n```"


def _fallback_answer(hits: list[dict]) -> str:
    if not hits:
        return "No LLM is configured (set ANTHROPIC_API_KEY) and no relevant code was found for this question."
    lines = ["No LLM is configured (set ANTHROPIC_API_KEY) — showing the most relevant code found instead:\n"]
    for hit in hits[:3]:
        meta = hit["metadata"]
        location = f"{meta.get('file')}:{meta.get('start_line')}-{meta.get('end_line')}"
        lines.append(f"**{location}**\n```\n{hit['text'][:500]}\n```")
    return "\n\n".join(lines)
