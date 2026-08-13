"""Tests for FastAPI endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from quotation.api.main import app
    return TestClient(app)


class TestAPIHealth:
    def test_health_endpoint(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_ai_health_endpoint(self, client):
        resp = client.get("/api/v1/ai/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "configured" in data

    def test_job_not_found(self, client):
        resp = client.get("/api/v1/jobs/nonexistent")
        assert resp.status_code == 404

    def test_upload_no_file(self, client):
        resp = client.post("/api/v1/quotes/upload")
        assert resp.status_code in (400, 422)  # FastAPI validation error
