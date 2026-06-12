l"""Fixtures compartilhadas da suíte de testes."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app
from app.evaluation.golden import CorpusEntry, GoldenItem, load_corpus, load_golden
from app.ingestion.service import IngestionService
from app.rag.pipeline import RagPipeline
from app.retrieval.retriever import Retriever
from app.retrieval.vector_store import InMemoryVectorStore

CORPUS_PATH = Path("datasets/corpus_rh.json")
GOLDEN_PATH = Path("datasets/golden_rh.json")


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """Cliente de teste da API FastAPI."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def corpus() -> list[CorpusEntry]:
    """Corpus de documentos de RH para testes."""
    return load_corpus(CORPUS_PATH)


@pytest.fixture()
def golden_items() -> list[GoldenItem]:
    """Itens do golden dataset."""
    return load_golden(GOLDEN_PATH)


@pytest.fixture()
def populated_store(corpus: list[CorpusEntry]) -> InMemoryVectorStore:
    """Vector store com o corpus aprovado ingerido."""
    store = InMemoryVectorStore()
    service = IngestionService(store=store, max_chars=800, overlap_chars=100)
    for entry in corpus:
        if entry.document.is_indexable():
            service.ingest(entry.document, entry.raw_text)
    return store


@pytest.fixture()
def pipeline(populated_store: InMemoryVectorStore) -> RagPipeline:
    """Pipeline RAG pronto, com retriever sobre o store populado."""
    return RagPipeline(retriever=Retriever(store=populated_store))


@pytest.fixture()
def cached_pipeline(populated_store: InMemoryVectorStore) -> RagPipeline:
    """Pipeline RAG com cache semântico e tracker FinOps próprios (Fase 3)."""
    from app.cache.semantic_cache import SemanticCache
    from app.finops.cost import FinOpsTracker

    return RagPipeline(
        retriever=Retriever(store=populated_store),
        cache=SemanticCache(similarity_threshold=0.92),
        finops=FinOpsTracker(),
    )
