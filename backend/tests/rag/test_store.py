import uuid

from app.rag.store import delete_job_collection, query, upsert_chunks


def test_upsert_and_query_roundtrip():
    job_id = f"test-{uuid.uuid4()}"
    try:
        upsert_chunks(
            job_id,
            ids=["1", "2"],
            embeddings=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            documents=["def find_user(): pass", "def send_email(): pass"],
            metadatas=[{"file": "a.py", "start_line": 1, "end_line": 1, "symbol": "find_user"}, {"file": "b.py", "start_line": 1, "end_line": 1, "symbol": None}],
        )

        hits = query(job_id, query_embedding=[1.0, 0.0, 0.0], top_k=1)

        assert len(hits) == 1
        assert hits[0]["metadata"]["file"] == "a.py"
        assert "symbol" not in hits[0]["metadata"] or hits[0]["metadata"].get("symbol") == "find_user"
    finally:
        delete_job_collection(job_id)


def test_query_on_empty_collection_returns_empty():
    job_id = f"test-empty-{uuid.uuid4()}"
    assert query(job_id, query_embedding=[1.0, 0.0, 0.0]) == []


def test_upsert_with_no_ids_is_a_noop():
    upsert_chunks("test-noop", ids=[], embeddings=[], documents=[], metadatas=[])
