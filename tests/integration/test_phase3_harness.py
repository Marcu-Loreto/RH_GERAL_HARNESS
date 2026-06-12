"""Testes de integração do harness completo (SPEC Fase 3 §6).

Cobrem: observabilidade completa, model router via pipeline, cache hit/miss,
escalonamento humano, policy registry aplicado e relatório FinOps.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.models import Confidentiality, UserRole
from app.rag.pipeline import RagPipeline, allowed_confidentiality_for


@pytest.mark.integration
def test_full_flow_has_complete_observability(pipeline: RagPipeline) -> None:
    result = pipeline.run("quantos dias de férias eu tenho?")
    trace = result.trace
    assert trace.trace_id
    assert trace.session_id
    assert trace.model
    assert trace.model_tier is not None
    assert trace.agent == "agente_beneficios"
    assert trace.input_tokens > 0
    assert trace.output_tokens > 0
    assert trace.estimated_cost >= 0.0
    assert trace.latency_ms >= 0.0


@pytest.mark.integration
def test_model_router_low_risk_uses_economico(pipeline: RagPipeline) -> None:
    result = pipeline.run("quantos dias de férias eu tenho?")
    assert result.trace.model_tier == "economico"
    assert result.model == "minimax-m2.5"
    assert result.estimated_cost == 0.0


@pytest.mark.integration
def test_model_router_high_risk_uses_robusto(pipeline: RagPipeline) -> None:
    result = pipeline.run("quais são as regras para demissão por justa causa?")
    assert result.trace.model_tier == "robusto"


@pytest.mark.integration
def test_cache_miss_then_hit(cached_pipeline: RagPipeline) -> None:
    first = cached_pipeline.run("quantos dias de férias eu tenho?")
    assert first.cache_hit is False

    second = cached_pipeline.run("quantos dias de férias eu tenho?")
    assert second.cache_hit is True
    assert second.estimated_cost == 0.0
    assert second.model == "cache"
    assert second.answer.answer == first.answer.answer


@pytest.mark.integration
def test_sensitive_case_is_escalated(pipeline: RagPipeline) -> None:
    result = pipeline.run("como denunciar um caso de assédio e discriminação?")
    assert result.answer.requires_human_review is True
    assert result.trace.escalation_reason


@pytest.mark.integration
def test_policy_registry_applied_to_roles() -> None:
    colaborador = allowed_confidentiality_for(UserRole.COLABORADOR)
    rh = allowed_confidentiality_for(UserRole.RH)
    assert Confidentiality.CONFIDENCIAL not in colaborador
    assert Confidentiality.CONFIDENCIAL in rh


@pytest.mark.integration
def test_finops_summary_aggregates_costs(cached_pipeline: RagPipeline) -> None:
    cached_pipeline.run("quantos dias de férias?")
    cached_pipeline.run("qual o prazo do banco de horas?")
    summary = cached_pipeline.finops.summary()
    assert summary.answer_count == 2
    assert "agente_beneficios" in summary.cost_by_agent
    assert summary.total_tokens > 0


@pytest.mark.integration
def test_finops_endpoint_returns_summary(client: TestClient) -> None:
    response = client.get("/api/v1/finops/summary", headers={"X-User-Role": "admin"})
    assert response.status_code == 200
    body = response.json()
    assert "total_cost" in body
    assert "cost_by_agent" in body
