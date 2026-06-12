"""Testes de integração de autenticação/RBAC nas rotas (Prioridade 1)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

_DOC = {
    "document": {
        "source_id": "auth-doc-001",
        "title": "Política de Férias",
        "owner": "rh@x.com",
        "area_rh": "beneficios",
        "document_type": "politica",
        "version": "1.0",
        "status": "approved",
        "valid_from": "2025-01-01T00:00:00Z",
        "confidentiality": "interno",
        "language": "pt-BR",
        "hash": "h-auth-001",
    },
    "raw_text": "Todo colaborador tem direito a 30 dias de férias por ano.",
}


@pytest.mark.integration
def test_ask_uses_context_role_not_payload(client: TestClient) -> None:
    # 'role' no corpo é ignorado (não é campo do schema); o perfil vem do header.
    response = client.post(
        "/api/v1/ask",
        json={"query": "quantos dias de férias?", "area_rh": "beneficios", "role": "admin"},
    )
    assert response.status_code == 200
    assert response.json()["trace_id"]


@pytest.mark.integration
def test_ask_works_for_anonymous_safe_minimal(client: TestClient) -> None:
    response = client.post("/api/v1/ask", json={"query": "quantos dias de férias?"})
    assert response.status_code == 200


@pytest.mark.integration
def test_ask_rejects_invalid_role_header(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ask",
        json={"query": "quantos dias de férias?"},
        headers={"X-User-Role": "superuser"},
    )
    assert response.status_code == 401


@pytest.mark.integration
def test_documents_requires_rh_or_admin(client: TestClient) -> None:
    assert client.post("/api/v1/documents", json=_DOC).status_code == 403
    assert (
        client.post("/api/v1/documents", json=_DOC, headers={"X-User-Role": "admin"}).status_code
        == 201
    )


@pytest.mark.integration
def test_finops_is_admin_only(client: TestClient) -> None:
    assert client.get("/api/v1/finops/summary").status_code == 403
    assert client.get("/api/v1/finops/summary", headers={"X-User-Role": "rh"}).status_code == 403
    assert client.get("/api/v1/finops/summary", headers={"X-User-Role": "admin"}).status_code == 200
