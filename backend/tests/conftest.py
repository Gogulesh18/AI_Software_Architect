"""Shared pytest fixtures for the backend test suite.

Sets isolated env vars (temp SQLite DB, temp workspace/chroma dirs) before
any `app.*` module is imported, since app.database.session builds its engine
at import time from app.core.config.get_settings() (which is lru_cache'd).
"""

import os
import tempfile
from pathlib import Path

_tmp_root = Path(tempfile.mkdtemp(prefix="ai-architect-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_tmp_root / 'test.db').as_posix()}"
os.environ["REPO_WORKSPACE_DIR"] = str(_tmp_root / "repos")
os.environ["CHROMA_PERSIST_DIR"] = str(_tmp_root / "chroma")
os.environ["JOB_RUNNER"] = "inprocess"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.database.models import Base
    from app.database.session import engine
    from app.main import app

    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    from app.database.models import Base
    from app.database.session import SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
