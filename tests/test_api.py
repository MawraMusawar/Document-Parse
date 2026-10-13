"""API endpoint tests using FastAPI TestClient."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify that root endpoint returns HTTP 200 with service information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "/docs" in data["documentation"]
    assert "Make LLMs reliable" in data["tagline"]


def test_health_check_endpoint():
    """Verify health endpoint returns healthy status code."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_telemetry_failures_endpoint():
    """Verify telemetry endpoint responds with valid list structure."""
    response = client.get("/api/v1/telemetry/failures")
    assert response.status_code == 200
    data = response.json()
    assert "entries" in data


def test_parse_resume_missing_api_key():
    """Verify that attempting to parse without an API key returns 503 Service Unavailable."""
    # Since GEMINI_API_KEY is unset in testing environment, it should fail gracefully
    payload = {"resume_text": "Sample candidate text with enough length to pass min_length validation."}
    response = client.post("/api/v1/parse-resume", json=payload)
    # If unconfigured, expect 503 or 422
    assert response.status_code in [503, 422]
