"""Testes unitários do gerador de resposta extrativo (RF1.6)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.agents.answer_generator import ExtractiveAnswerGenerator
from app.core.models import ChunkMetadata, Confidentiality, DocumentStatus
from app.guardrails.policies import NO_EVIDENCE_RESPONSE
from app.retrieval.vector_store import ScoredChunk


def _scored(text: str, score: float) -> ScoredChunk:
    meta = ChunkMetadata(
        chunk_id="c1",
        source_id="d1",
        title="Política de Férias",
        text=text,
        area_rh="beneficios",
        document_type="politica",
        version="1.2",
        confidentiality=Confidentiality.INTERNO,
        status=DocumentStatus.APPROVED,
        hash="h",
        valid_from=datetime(2025, 1, 1, tzinfo=UTC),
    )
    return ScoredChunk(chunk=meta, score=score)


@pytest.mark.unit
def test_generates_answer_with_evidence() -> None:
    gen = ExtractiveAnswerGenerator()
    answer = gen.generate("férias", [_scored("Direito a 30 dias de férias.", 0.8)])
    assert answer.evidence
    assert answer.evidence[0].source_id == "d1"
    assert "30 dias" in answer.answer


@pytest.mark.unit
def test_no_chunks_returns_no_evidence_message() -> None:
    gen = ExtractiveAnswerGenerator()
    answer = gen.generate("qualquer", [])
    assert answer.answer == NO_EVIDENCE_RESPONSE
    assert answer.evidence == []


@pytest.mark.unit
def test_confidence_scales_with_score() -> None:
    gen = ExtractiveAnswerGenerator()
    high = gen.generate("q", [_scored("texto", 0.9)])
    low = gen.generate("q", [_scored("texto", 0.1)])
    assert str(high.confidence) == "alta"
    assert str(low.confidence) == "baixa"
