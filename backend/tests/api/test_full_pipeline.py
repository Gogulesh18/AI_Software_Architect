"""End-to-end: POST a local repo through the real HTTP API, wait for the
background job to finish, and check every read endpoint the frontend will
call. This is the first test that exercises ingest -> parse -> graph ->
analyze -> diagram -> report -> embed all wired together through workers/pipeline.py.
"""

import time


def _wait_for_job(client, job_id: str, timeout_s: float = 30.0) -> dict:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        body = client.get(f"/api/jobs/{job_id}").json()
        if body["status"] in ("done", "failed"):
            return body
        time.sleep(0.2)
    raise AssertionError(f"job {job_id} did not finish within {timeout_s}s")


def _make_sample_repo(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "controllers").mkdir()
    (tmp_path / "app" / "repositories").mkdir()

    (tmp_path / "README.md").write_text("# Sample App\n\nA small FastAPI + SQLAlchemy demo.\n")
    (tmp_path / "app" / "controllers" / "user_controller.py").write_text(
        '@app.get("/users")\ndef list_users():\n    return UserRepository().find_all()\n'
    )
    (tmp_path / "app" / "repositories" / "user_repository.py").write_text(
        'class UserRepository(Base):\n    __tablename__ = "users"\n    id = Column(Integer, primary_key=True)\n\n'
        "    def find_all(self):\n        return []\n"
    )
    return tmp_path


def test_full_pipeline_via_http_api(client, tmp_path):
    repo_path = _make_sample_repo(tmp_path)

    create_resp = client.post("/api/repos/local", json={"path": str(repo_path)})
    assert create_resp.status_code == 200
    job_id = create_resp.json()["id"]

    job = _wait_for_job(client, job_id)
    assert job["status"] == "done", job.get("error_message")
    assert job["progress"] == 100

    result = client.get(f"/api/jobs/{job_id}/result").json()
    assert result["summary"]["total_files"] >= 3
    assert result["architecture"]["primary_style"]
    assert "users" in {t["name"] for t in result["database_schema"]["tables"]}
    assert result["api_surface"]["endpoint_count"] == 1
    assert set(result["scores"].keys()) >= {"overall", "security", "performance"}

    diagram_types = client.get(f"/api/jobs/{job_id}/diagrams").json()["types"]
    assert "er_diagram" in diagram_types
    er_diagram = client.get(f"/api/jobs/{job_id}/diagrams/er_diagram").json()
    assert any(n["id"] == "users" for n in er_diagram["nodes"])

    missing = client.get(f"/api/jobs/{job_id}/diagrams/not_a_real_type")
    assert missing.status_code == 409

    report = client.get(f"/api/jobs/{job_id}/report")
    assert report.status_code == 200
    assert "Architecture" in report.text

    source_resp = client.get(f"/api/jobs/{job_id}/source", params={"file": "app/repositories/user_repository.py"})
    assert source_resp.status_code == 200
    source_chunks = source_resp.json()["chunks"]
    assert any("find_all" in c["text"] for c in source_chunks)

    chat_resp = client.post(f"/api/jobs/{job_id}/chat", json={"message": "How is the user data accessed?"})
    assert chat_resp.status_code == 200
    assert chat_resp.json()["answer"]

    for fmt in ("markdown", "json", "pdf"):
        export_resp = client.get(f"/api/jobs/{job_id}/export/{fmt}")
        assert export_resp.status_code == 200, f"{fmt} export failed: {export_resp.text}"
        assert len(export_resp.content) > 0
