"""Exercises the LLM-available branch of app.rag.chat with a fake provider —
no real ANTHROPIC_API_KEY is available in this test environment, so this is
the only way to cover the synthesis path (context building, prompt
assembly) rather than just the no-LLM fallback."""

import uuid
from unittest.mock import patch

from app.parser.extractor import parse_source
from app.rag.chat import answer_question
from app.rag.indexer import index_repository
from app.rag.store import delete_job_collection


class FakeLLM:
    is_available = True

    def __init__(self):
        self.last_system = None
        self.last_messages = None

    def chat(self, system, messages, max_tokens=1000):
        self.last_system = system
        self.last_messages = messages
        return "Authentication happens in auth.py via authenticate_user()."


def test_chat_uses_llm_when_available():
    job_id = f"test-llm-{uuid.uuid4()}"
    files = [parse_source("auth.py", "python", "def authenticate_user(u, p):\n    return True\n")]
    fake = FakeLLM()

    try:
        index_repository(job_id, files)
        with patch("app.rag.chat.get_llm_provider", return_value=fake):
            answer, sources = answer_question(job_id, "demo-repo", "How does auth work?", [])

        assert answer == "Authentication happens in auth.py via authenticate_user()."
        assert any(s["file"] == "auth.py" for s in sources)
        assert "demo-repo" in fake.last_system
        assert fake.last_messages[-1]["role"] == "user"
        assert "auth.py" in fake.last_messages[-1]["content"]
    finally:
        delete_job_collection(job_id)


def test_chat_passes_conversation_history_to_llm():
    job_id = f"test-llm-history-{uuid.uuid4()}"
    files = [parse_source("a.py", "python", "def f():\n    pass\n")]
    fake = FakeLLM()
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]

    try:
        index_repository(job_id, files)
        with patch("app.rag.chat.get_llm_provider", return_value=fake):
            answer_question(job_id, "demo-repo", "follow up question", history)

        assert fake.last_messages[0] == history[0]
        assert fake.last_messages[1] == history[1]
    finally:
        delete_job_collection(job_id)
