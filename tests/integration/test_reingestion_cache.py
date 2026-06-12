"""Testes de invalidação de cache na reingestão/atualização de documento (RF3.4).

Garante que toda reingestão ou atualização de versão de um documento invalide o
cache semântico relacionado, de modo que respostas baseadas na versão antiga não
sejam reutilizadas (PRIORIDADE 5).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.cache.semantic_cache import SemanticCache
from app.core.models import (
    Answer,
    Confidence,
    Confidentiality,
    DocumentMetadata,
    DocumentStatus,
    Evidence,
)
from app.ingestion.service import IngestionService
from app.observability.sinks import TraceSink
from app.retrieval.embeddings import get_embedding_provider
from app.retrieval.vector_store import InMemoryVectorStore


class _RecordingSink:
    """Sink de teste que captura eventos emitidos."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []

    def event(self, name: str, **fields: object) -> None:
        self.events.append((name, dict(fields)))

    def record(self, trace: object) -> None:  # pragma: no cover - não usado aqui
        return None


def _doc(version: str, valid_until: datetime | None = None) -> DocumentMetadata:
    return DocumentMetadata(
        source_id="ben-ferias-001",
        title="Política de Férias",
        owner="rh@x.com",
        area_rh="beneficios",
        document_type="politica",
        version=version,
        status=DocumentStatus.APPROVED,
        valid_from=datetime(2025, 1, 1, tzinfo=UTC),
        valid_until=valid_until,
        confidentiality=Confidentiality.INTERNO,
        language="pt-BR",
        hash="h",
    )


def _cached_answer() -> Answer:
    return Answer(
        answer="Você tem direito a 30 dias de férias.",
        evidence=[
            Evidence(
                source_id="ben-ferias-001", title="Política de Férias", version="1", chunk_id="c1"
            )
        ],
        confidence=Confidence.ALTA,
    )


def _service(store: InMemoryVectorStore, cache: SemanticCache, sink: TraceSink) -> IngestionService:
    return IngestionService(store=store, max_chars=200, overlap_chars=0, cache=cache, sink=sink)


@pytest.mark.integration
def test_initial_ingestion_does_not_invalidate() -> None:
    store = InMemoryVectorStore()
    cache = SemanticCache(similarity_threshold=0.9)
    sink = _RecordingSink()
    service = _service(store, cache, sink)

    result = service.ingest(_doc("1"), "Férias de 30 dias por ano.")

    assert result.reindexed is False
    assert result.cache_entries_invalidated == 0
    assert not any(name == "cache_invalidated_on_reingestion" for name, _ in sink.events)


@pytest.mark.integration
def test_update_triggers_invalidate_by_document() -> None:
    store = InMemoryVectorStore()
    cache = SemanticCache(similarity_threshold=0.9)
    sink = _RecordingSink()
    service = _service(store, cache, sink)

    service.ingest(_doc("1"), "Férias de 30 dias por ano.")

    # Resposta em cache baseada na versão 1 do documento.
    embedder = get_embedding_provider()
    q = "quantos dias de férias eu tenho"
    cache.store(
        q,
        embedder.embed(q),
        _cached_answer(),
        domain="beneficios",
        required_confidentiality=frozenset({"interno"}),
        document_versions={"ben-ferias-001": "1"},
    )
    assert len(cache) == 1

    result = service.ingest(_doc("2"), "Férias de 30 dias, podendo ser fracionadas.")

    assert result.reindexed is True
    assert result.previous_version == "1"
    assert result.cache_entries_invalidated == 1
    assert len(cache) == 0


@pytest.mark.integration
def test_old_cache_not_used_after_reingestion() -> None:
    store = InMemoryVectorStore()
    cache = SemanticCache(similarity_threshold=0.9)
    sink = _RecordingSink()
    service = _service(store, cache, sink)

    service.ingest(_doc("1"), "Férias de 30 dias por ano.")
    embedder = get_embedding_provider()
    q = "quantos dias de férias eu tenho"
    cache.store(
        q,
        embedder.embed(q),
        _cached_answer(),
        domain="beneficios",
        required_confidentiality=frozenset({"interno"}),
        document_versions={"ben-ferias-001": "1"},
    )

    service.ingest(_doc("2"), "Férias de 30 dias, podendo ser fracionadas.")

    lookup = cache.lookup(
        embedder.embed(q),
        domain="beneficios",
        allowed_confidentiality=[Confidentiality.INTERNO],
        current_versions={"ben-ferias-001": "2"},
    )
    assert lookup.hit is False


@pytest.mark.integration
def test_reingestion_logs_invalidation_event() -> None:
    store = InMemoryVectorStore()
    cache = SemanticCache(similarity_threshold=0.9)
    sink = _RecordingSink()
    service = _service(store, cache, sink)

    service.ingest(_doc("1"), "Férias de 30 dias por ano.")
    embedder = get_embedding_provider()
    q = "quantos dias de férias eu tenho"
    cache.store(
        q,
        embedder.embed(q),
        _cached_answer(),
        domain="beneficios",
        required_confidentiality=frozenset({"interno"}),
        document_versions={"ben-ferias-001": "1"},
    )

    service.ingest(_doc("2"), "Texto novo da política de férias.")

    events = [name for name, _ in sink.events]
    assert "cache_invalidated_on_reingestion" in events
    payload = next(f for n, f in sink.events if n == "cache_invalidated_on_reingestion")
    assert payload["new_version"] == "2"
    assert payload["previous_version"] == "1"


@pytest.mark.integration
def test_reindex_replaces_old_chunks_in_store() -> None:
    store = InMemoryVectorStore()
    cache = SemanticCache(similarity_threshold=0.9)
    sink = _RecordingSink()
    service = _service(store, cache, sink)

    service.ingest(_doc("1"), "Conteúdo antigo da política.")
    assert store.version_of("ben-ferias-001") == "1"

    service.ingest(_doc("2"), "Conteúdo novo da política.")

    # Apenas a versão nova permanece indexada (sem chunks órfãos da versão 1).
    assert store.version_of("ben-ferias-001") == "2"
    assert all(item.chunk.version == "2" for item in store._items)
