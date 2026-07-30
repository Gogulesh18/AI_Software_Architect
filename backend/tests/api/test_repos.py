def test_create_from_local_invalid_path_returns_400(client):
    r = client.post("/api/repos/local", json={"path": "C:/definitely/does/not/exist"})
    assert r.status_code == 400
    assert "does not exist" in r.json()["detail"]


def test_create_from_local_valid_path_creates_job(client, tmp_path):
    (tmp_path / "main.py").write_text("print('hi')\n")

    r = client.post("/api/repos/local", json={"path": str(tmp_path)})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("queued", "running", "done", "failed")
    assert body["stage"] is not None

    job_id = body["id"]
    r2 = client.get(f"/api/jobs/{job_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == job_id


def test_get_unknown_job_returns_404(client):
    r = client.get("/api/jobs/does-not-exist")
    assert r.status_code == 404


def test_list_repos_empty(client):
    r = client.get("/api/repos")
    assert r.status_code == 200
    assert r.json() == []


def test_result_before_job_done_returns_409(client):
    # Insert a job directly (status=queued) rather than going through
    # POST /api/repos/*, which enqueues the real (async, racy-to-observe)
    # pipeline — this test only cares about the "not done yet" response.
    from app.database.models import AnalysisJob, Repository, SourceType
    from app.database.session import SessionLocal

    db = SessionLocal()
    try:
        repo = Repository(name="fixture", source_type=SourceType.LOCAL, source_ref="/tmp/fixture")
        db.add(repo)
        db.flush()  # populate repo.id (Python-side default applies on flush, not construction)
        job = AnalysisJob(repository_id=repo.id)
        db.add(job)
        db.commit()
        job_id = job.id
    finally:
        db.close()

    r = client.get(f"/api/jobs/{job_id}/result")
    assert r.status_code == 409
