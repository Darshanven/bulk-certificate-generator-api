from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app import worker

def sample_payload():
    return {"recipients": [
        {"name": "Asha Rao", "email": "asha@example.com", "course": "Python Basics"},
        {"name": "Ravi Kumar", "email": "ravi@example.com", "course": "Data Analytics"}
    ]}

def make_client(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(worker, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(worker, "OUTPUT_DIR", tmp_path / "certificates")
    return TestClient(app), engine

def test_create_job_progress_and_download(tmp_path, monkeypatch):
    client, engine = make_client(tmp_path, monkeypatch)
    try:
        response = client.post("/api/jobs/", json=sample_payload())
        assert response.status_code == 202
        created = response.json()
        assert created["total"] == 2
        job = client.get(f"/api/jobs/{created['id']}/").json()
        assert job["status"] == "COMPLETED"
        assert job["succeeded"] == 2
        assert job["progress_percent"] == 100.0
        recipient_id = job["recipients"][0]["recipient_id"]
        download = client.get(f"/api/jobs/{created['id']}/certificates/{recipient_id}/")
        assert download.status_code == 200
        assert download.content.startswith(b"%PDF")
    finally:
        client.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

def test_generate_certificate_allows_plain_filename(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    output_path = "plain.pdf"

    worker.generate_certificate(output_path, "Asha Rao", "Python Basics", "asha@example.com")

    assert tmp_path.joinpath(output_path).is_file()
    assert tmp_path.joinpath(output_path).read_bytes().startswith(b"%PDF")


def test_input_validation(tmp_path, monkeypatch):
    client, engine = make_client(tmp_path, monkeypatch)
    try:
        response = client.post("/api/jobs/", json={"recipients": [
            {"name": " ", "email": "bad", "course": "Python"}]})
        assert response.status_code == 422
    finally:
        client.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

def test_one_failure_does_not_stop_batch(tmp_path, monkeypatch):
    client, engine = make_client(tmp_path, monkeypatch)
    original = worker.generate_certificate
    def fail_one(path, name, course, email):
        if name == "Ravi Kumar":
            raise RuntimeError("simulated PDF failure")
        return original(path, name, course, email)
    monkeypatch.setattr(worker, "generate_certificate", fail_one)
    try:
        created = client.post("/api/jobs/", json=sample_payload()).json()
        job = client.get(f"/api/jobs/{created['id']}/").json()
        assert job["status"] == "PARTIALLY_COMPLETED"
        assert job["succeeded"] == 1 and job["failed"] == 1
        statuses = {r["name"]: r["status"] for r in job["recipients"]}
        assert statuses["Asha Rao"] == "SUCCEEDED"
        assert statuses["Ravi Kumar"] == "FAILED"
    finally:
        client.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

def test_missing_job_returns_404(tmp_path, monkeypatch):
    client, engine = make_client(tmp_path, monkeypatch)
    try:
        assert client.get("/api/jobs/missing/").status_code == 404
    finally:
        client.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
