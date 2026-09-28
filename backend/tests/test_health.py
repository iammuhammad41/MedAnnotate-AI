import os

os.environ.setdefault(
    "MEDANNOTATE_DATABASE_URL",
    "sqlite:///./test_medannotate.db",
)

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "MedAnnotate AI API"
