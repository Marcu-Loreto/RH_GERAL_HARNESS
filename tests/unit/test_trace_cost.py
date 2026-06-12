"""Testes unitários de criação de trace com custo e campos Fase 3 (RF3.1)."""

from __future__ import annotations

import pytest

from app.core.models import Answer, Confidence, Evidence
from app.observability.trace import build_answer_trace


def _answer() -> Answer:
    return Answer(
        answer="Resposta com evidência.",
        evidence=[Evidence(source_id="s1", title="Doc", version="1", chunk_id="c1")],
        confidence=Confidence.ALTA,
    )


@pytest.mark.unit
def test_trace_records_cost_and_phase3_fields() -> None:
    trace = build_answer_trace(
        trace_id="t1",
        session_id="s1",
        user_id="u1",
        channel="api",
        original_query="quantos dias de férias",
        canonical_query="dias férias",
        domain="beneficios",
        agent="agente_beneficios",
        model="gpt-4o",
        answer=_answer(),
        retrieved_chunk_ids=["c1"],
        guardrails_triggered=[],
        latency_ms=12.5,
        estimated_cost=0.0123,
        model_tier="robusto",
        cache_hit=False,
        prompt_version="1",
    )
    assert trace.estimated_cost == 0.0123
    assert trace.model_tier == "robusto"
    assert trace.cache_hit is False
    assert trace.prompt_version == "1"
    assert trace.channel == "api"
    assert trace.input_tokens > 0


@pytest.mark.unit
def test_trace_cache_hit_flag() -> None:
    trace = build_answer_trace(
        trace_id="t2",
        session_id="s2",
        user_id=None,
        original_query="q",
        canonical_query="q",
        domain="beneficios",
        agent="agente_beneficios",
        model="cache",
        answer=_answer(),
        retrieved_chunk_ids=["c1"],
        guardrails_triggered=[],
        latency_ms=1.0,
        cache_hit=True,
    )
    assert trace.cache_hit is True
    assert trace.estimated_cost == 0.0
