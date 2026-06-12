"""Testes de integração das rotas de health check (RF0.5)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.middleware import SESSION_HEADER, TRACE_HEADER


@pytest.mark.integration
def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["trace_id"]


@pytest.mark.integration
def test_health_sets_trace_headers(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert TRACE_HEADER in response.headers
    assert SESSION_HEADER in response.headers


@pytest.mark.integration
def test_incoming_trace_id_is_preserved(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={TRACE_HEADER: "trace-fixo"})
    assert response.headers[TRACE_HEADER] == "trace-fixo"
    assert response.json()["trace_id"] == "trace-fixo"


@pytest.mark.integration
def test_ready_reports_database(client: TestClient) -> None:
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["database"] in {"up", "down"}
