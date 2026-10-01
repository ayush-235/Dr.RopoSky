"""Tests for Health check endpoint."""

from fastapi.testclient import TestClient


def test_health_check_returns_200(client: TestClient):
    """GET /api/v1/health should return 200 with status ok."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "rokospy-backend"
    assert "version" in data


def test_openapi_docs_accessible(client: TestClient):
    """OpenAPI schema and docs should be accessible."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    openapi = response.json()
    assert openapi["info"]["title"] == "rokospy-backend"

    docs_response = client.get("/api/v1/docs")
    assert docs_response.status_code == 200


def test_404_not_found(client: TestClient):
    """Accessing non-existent endpoints returns structured 404."""
    response = client.get("/api/v1/non_existent_route")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_405_method_not_allowed(client: TestClient):
    """Invalid HTTP method returns structured 405."""
    response = client.delete("/api/v1/health")
    assert response.status_code == 405
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "METHOD_NOT_ALLOWED"
