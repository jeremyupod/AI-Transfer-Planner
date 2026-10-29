from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "AI Transfer Planner API is running"}


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_cors_allows_local_frontend() -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_unknown_origin() -> None:
    response = client.get("/health", headers={"Origin": "https://example.com"})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
