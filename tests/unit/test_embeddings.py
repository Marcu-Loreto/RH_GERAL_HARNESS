"""Testes unitários de embeddings e similaridade (RF1.3)."""

from __future__ import annotations

import math

import pytest

from app.retrieval.embeddings import (
    HashingEmbeddingProvider,
    cosine_similarity,
    tokenize,
)


@pytest.mark.unit
def test_tokenize_lowercases_and_splits() -> None:
    assert tokenize("Férias e Banco-de-Horas") == ["férias", "e", "banco", "de", "horas"]


@pytest.mark.unit
def test_embedding_is_deterministic() -> None:
    provider = HashingEmbeddingProvider(dim=64)
    assert provider.embed("política de férias") == provider.embed("política de férias")


@pytest.mark.unit
def test_embedding_is_l2_normalized() -> None:
    provider = HashingEmbeddingProvider(dim=64)
    vector = provider.embed("vale alimentação")
    assert math.isclose(math.sqrt(sum(v * v for v in vector)), 1.0, abs_tol=1e-9)


@pytest.mark.unit
def test_similar_texts_score_higher() -> None:
    provider = HashingEmbeddingProvider(dim=256)
    query = provider.embed("quantos dias de férias")
    similar = provider.embed("direito a dias de férias por ano")
    different = provider.embed("política de estacionamento e garagem")
    assert cosine_similarity(query, similar) > cosine_similarity(query, different)


@pytest.mark.unit
def test_cosine_dimension_mismatch_raises() -> None:
    with pytest.raises(ValueError):
        cosine_similarity([1.0, 0.0], [1.0])
