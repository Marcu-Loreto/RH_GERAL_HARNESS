"""Testes de integração da ingestão → embedding → indexação (RF1.1–RF1.3)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.core.models import Confidentiality, DocumentMetadata, DocumentStatus
from app.ingestion.service import IngestionError, IngestionService
from app.retrieval.vector_store import InMemoryVectorStore


def _doc(status: DocumentStatus = DocumentStatus.APPROVED) -> DocumentMetadata:
    return DocumentMetadata(
        source_id="doc-x",
        title="Política X",
        owner="rh@x.com",
        area_rh="beneficios",
        document_type="politica",
        version="1.0",
        status=status,
        valid_from=datetime(2025, 1, 1, tzinfo=UTC),
        confidentiality=Confidentiality.INTERNO,
        language="pt-BR",
        hash="h",
    )


@pytest.mark.integration
def test_ingest_indexes_chunks() -> None:
    store = InMemoryVectorStore()
    service = IngestionService(store=store, max_chars=100, overlap_chars=0)
    result = service.ingest(_doc(), "Parágrafo um.\n\nParágrafo dois bem mais longo.")
    assert result.chunks_indexed >= 1
    assert len(store) == result.chunks_indexed


@pytest.mark.integration
def test_ingest_rejects_non_approved() -> None:
    store = InMemoryVectorStore()
    service = IngestionService(store=store, max_chars=100, overlap_chars=0)
    with pytest.raises(IngestionError):
        service.ingest(_doc(status=DocumentStatus.DRAFT), "texto qualquer")
    assert len(store) == 0


@pytest.mark.integration
def test_ingest_rejects_empty_text() -> None:
    store = InMemoryVectorStore()
    service = IngestionService(store=store, max_chars=100, overlap_chars=0)
    with pytest.raises(IngestionError):
        service.ingest(_doc(), "   ")
