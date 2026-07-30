"""Chunk -> embed -> store, run once per analysis job."""

import logging

from app.embeddings import get_embedding_provider
from app.parser.models import ParsedFile
from app.rag.chunking import chunk_repository
from app.rag.store import upsert_chunks

logger = logging.getLogger(__name__)

MAX_CHUNKS = 4000


def index_repository(job_id: str, parsed_files: list[ParsedFile]) -> int:
    chunks = chunk_repository(parsed_files)[:MAX_CHUNKS]
    if not chunks:
        return 0

    provider = get_embedding_provider()
    embeddings = provider.embed([c.text for c in chunks])

    ids = [f"{job_id}::{i}" for i in range(len(chunks))]
    documents = [c.text for c in chunks]
    metadatas = [
        {"file": c.file, "start_line": c.start_line, "end_line": c.end_line, "symbol": c.symbol} for c in chunks
    ]

    upsert_chunks(job_id, ids, embeddings, documents, metadatas)
    logger.info("Indexed %d chunks for job %s", len(chunks), job_id)
    return len(chunks)
