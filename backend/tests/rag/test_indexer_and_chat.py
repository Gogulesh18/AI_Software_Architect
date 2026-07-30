import uuid

from app.parser.extractor import parse_source
from app.rag.chat import answer_question
from app.rag.indexer import index_repository
from app.rag.store import delete_job_collection


def test_index_and_retrieve_relevant_chunk():
    job_id = f"test-index-{uuid.uuid4()}"
    files = [
        parse_source(
            "auth.py",
            "python",
            "def authenticate_user(username, password):\n    return check_credentials(username, password)\n",
        ),
        parse_source(
            "email.py",
            "python",
            "def send_welcome_email(user):\n    return mailer.send(user.email, 'welcome')\n",
        ),
    ]
    try:
        count = index_repository(job_id, files)
        assert count == 2

        # No LLM configured in this test environment -> chat falls back to
        # returning retrieved context directly (verifies retrieval works
        # end-to-end without needing a real Anthropic API key).
        answer, sources = answer_question(job_id, "demo-repo", "How does authentication work?", [])

        assert "No LLM is configured" in answer
        assert any(s["file"] == "auth.py" for s in sources)
    finally:
        delete_job_collection(job_id)


def test_index_empty_repo_returns_zero():
    job_id = f"test-empty-{uuid.uuid4()}"
    assert index_repository(job_id, []) == 0


def test_chat_on_unindexed_job_returns_no_context_message():
    job_id = f"test-unindexed-{uuid.uuid4()}"
    answer, sources = answer_question(job_id, "demo-repo", "anything?", [])
    assert sources == []
    assert "No LLM is configured" in answer
