"""Chroma persistent vector store — one collection per analysis job so
results from different repos/runs never mix and a job's collection can be
dropped independently."""

from functools import lru_cache

import chromadb

from app.core.config import get_settings


@lru_cache
def _client() -> chromadb.ClientAPI:
    settings = get_settings()
    return chromadb.PersistentClient(path=str(settings.chroma_path))


def _collection_name(job_id: str) -> str:
    return f"job_{job_id}"


def upsert_chunks(job_id: str, ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict]) -> None:
    if not ids:
        return
    collection = _client().get_or_create_collection(_collection_name(job_id))
    # Chroma's add() rejects None metadata values; upstream callers may pass
    # `symbol: None` for window-chunked (non-symbol) content.
    clean_metadatas = [{k: v for k, v in m.items() if v is not None} for m in metadatas]
    # Chroma's stubs want ndarray/Sequence[float] and a stricter metadata
    # value union than plain list[list[float]]/list[dict] — both work fine
    # at runtime (proven by tests/rag/test_store.py's real roundtrip).
    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=clean_metadatas)  # type: ignore[arg-type]


def query(job_id: str, query_embedding: list[float], top_k: int = 6) -> list[dict]:
    collection = _client().get_or_create_collection(_collection_name(job_id))
    if collection.count() == 0:
        return []
    result = collection.query(query_embeddings=[query_embedding], n_results=min(top_k, collection.count()))  # type: ignore[arg-type]
    hits = []
    # documents/metadatas/distances are typed Optional in Chroma's stubs but
    # are always present unless `include=` explicitly excludes them, which
    # we never do here.
    docs = result["documents"][0]  # type: ignore[index]
    metas = result["metadatas"][0]  # type: ignore[index]
    distances = result["distances"][0]  # type: ignore[index]
    for doc, meta, distance in zip(docs, metas, distances):
        hits.append({"text": doc, "metadata": meta, "distance": distance})
    return hits


def get_by_file(job_id: str, file_path: str) -> list[dict]:
    collection = _client().get_or_create_collection(_collection_name(job_id))
    result = collection.get(where={"file": file_path})
    documents = result["documents"] or []  # type: ignore[index]
    metadatas = result["metadatas"] or []  # type: ignore[index]
    return [
        {"text": doc, "start_line": meta.get("start_line"), "end_line": meta.get("end_line"), "symbol": meta.get("symbol")}
        for doc, meta in zip(documents, metadatas)
    ]


def delete_job_collection(job_id: str) -> None:
    try:
        _client().delete_collection(_collection_name(job_id))
    except Exception:  # noqa: BLE001, S110 - collection may not exist; deletion is best-effort cleanup
        pass
