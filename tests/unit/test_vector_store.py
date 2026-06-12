"""Testes unitários do vector store e filtros de metadados (RF1.5)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.core.models import ChunkMetadata, Confidentiality, DocumentStatus
from app.retrieval.embeddings import HashingEmbeddingProvider
from app.retrieval.vector_store import (
    InMemoryVectorStore,
    RetrievalFilters,
    StoredChunk,
)

_EMBEDDER = HashingEmbeddingProvider(dim=128)


def _chunk(chunk_id: str, text: str, **overrides: object) -> StoredChunk:
    data: dict[str, object] = {
        "chunk_id": chunk_id,
        "source_id": "doc",
        "title": "Doc",
        "text": text,
        "area_rh": "beneficios",
        "document_type": "politica",
        "version": "1.0",
        "confidentiality": Confidentiality.INTERNO,
        "status": DocumentStatus.APPROVED,
        "hash": "h",
        "valid_from": datetime(2025, 1, 1, tzinfo=UTC),
    }
    data.update(overrides)
    meta = ChunkMetadata(**data)  # type: ignore[arg-type]
    return StoredChunk(chunk=meta, vector=_EMBEDDER.embed(text))


@pytest.mark.unit
def test_search_filters_by_area() -> None:
    store = InMemoryVectorStore()
    store.add([_chunk("c1", "férias", area_rh="beneficios")])
    store.add([_chunk("c2", "férias", area_rh="politicas")])
    results = store.search(
        _EMBEDDER.embed("férias"), RetrievalFilters(area_rh="beneficios"), top_k=10
    )
    assert [r.chunk.chunk_id for r in results] == ["c1"]


@pytest.mark.unit
def test_search_excludes_non_approved() -> None:
    store = InMemoryVectorStore()
    store.add([_chunk("c1", "férias", status=DocumentStatus.DEPRECATED)])
    results = store.search(_EMBEDDER.embed("férias"), RetrievalFilters(), top_k=10)
    assert results == []


@pytest.mark.unit
def test_search_filters_by_confidentiality() -> None:
    store = InMemoryVectorStore()
    store.add([_chunk("c1", "férias", confidentiality=Confidentiality.CONFIDENCIAL)])
    filters = RetrievalFilters(allowed_confidentiality=[Confidentiality.INTERNO])
    assert store.search(_EMBEDDER.embed("férias"), filters, top_k=10) == []


@pytest.mark.unit
def test_search_filters_by_validity_window() -> None:
    store = InMemoryVectorStore()
    store.add(
        [
            _chunk(
                "c1",
                "férias",
                valid_from=datetime(2020, 1, 1, tzinfo=UTC),
                valid_until=datetime(2024, 12, 31, tzinfo=UTC),
            )
        ]
    )
    filters = RetrievalFilters(reference_date=datetime(2026, 1, 1, tzinfo=UTC))
    assert store.search(_EMBEDDER.embed("férias"), filters, top_k=10) == []
