"""Testes de integração da rota de ingestão (RF1.1)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

_APPROVED_DOC = {
    "document": {
        "source_id": "api-doc-001",
        "title": "Política de Teste",
        "owner": "rh@x.com",
        "area_rh": "beneficios",
        "document_type": "politica",
        "version": "1.0",
        "status": "approved",
        "valid_from": "2025-01-01T00:00:00Z",
        "confidentiality": "interno",
        "language": "pt-BR",
        "hash": "h-api-001",
    },
    "raw_text": "Esta política de teste concede 25 dias de licença especial.",
}


@pytest.mark.integration
def test_ingest_approved_document(client: TestClient) -> None:
    response = client.post("/api/v1/documents", json=_APPROVED_DOC, headers={"X-User-Role": "rh"})
    assert response.status_code == 201
    body = response.json()
    assert body["source_id"] == "api-doc-001"
    assert body["chunks_indexed"] >= 1
    assert body["trace_id"]


@pytest.mark.integration
def test_ingest_draft_document_is_rejected(client: TestClient) -> None:
    payload = {**_APPROVED_DOC, "document": {**_APPROVED_DOC["document"], "status": "draft"}}
    response = client.post("/api/v1/documents", json=payload, headers={"X-User-Role": "rh"})
    assert response.status_code == 422


@pytest.mark.integration
def test_ingest_requires_authorized_role(client: TestClient) -> None:
    # Colaborador (perfil padrão sem header) não pode ingerir documentos.
    response = client.post("/api/v1/documents", json=_APPROVED_DOC)
    assert response.status_code == 403
    # Perfil explícito sem permissão também é bloqueado.
    response = client.post(
        "/api/v1/documents", json=_APPROVED_DOC, headers={"X-User-Role": "colaborador"}
    )
    assert response.status_code == 403
