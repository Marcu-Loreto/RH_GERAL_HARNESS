"""Testes unitários do model router (RF3.3 / SPEC Fase 3 §4)."""

from __future__ import annotations

import pytest

from app.agents.query_intelligence import RiskLevel
from app.core.model_router import (
    BudgetStatus,
    ModelSpec,
    ModelTier,
    select_model,
)


@pytest.mark.unit
def test_low_risk_uses_economico() -> None:
    decision = select_model(RiskLevel.BAIXO, confidence=0.9)
    assert decision.model.tier == ModelTier.ECONOMICO
    assert decision.requires_human_review is False
    assert decision.fallback_used is False


@pytest.mark.unit
def test_medium_risk_uses_intermediario() -> None:
    decision = select_model(RiskLevel.MEDIO, confidence=0.9)
    assert decision.model.tier == ModelTier.INTERMEDIARIO


@pytest.mark.unit
def test_high_risk_uses_robusto() -> None:
    decision = select_model(RiskLevel.ALTO, confidence=0.9)
    assert decision.model.tier == ModelTier.ROBUSTO
    assert decision.requires_human_review is False


@pytest.mark.unit
def test_low_confidence_forces_robusto_and_human_review() -> None:
    decision = select_model(RiskLevel.BAIXO, confidence=0.1, min_confidence=0.34)
    assert decision.model.tier == ModelTier.ROBUSTO
    assert decision.requires_human_review is True


@pytest.mark.unit
def test_fixed_strategy_overrides_rules() -> None:
    decision = select_model(RiskLevel.ALTO, confidence=0.9, strategy="economico")
    assert decision.model.tier == ModelTier.ECONOMICO


@pytest.mark.unit
def test_fallback_when_preferred_unavailable() -> None:
    catalog = {
        ModelTier.ECONOMICO: ModelSpec("eco", ModelTier.ECONOMICO, 0.0, 0.0, available=True),
        ModelTier.INTERMEDIARIO: ModelSpec(
            "mid", ModelTier.INTERMEDIARIO, 0.001, 0.002, available=True
        ),
        ModelTier.ROBUSTO: ModelSpec("big", ModelTier.ROBUSTO, 0.01, 0.02, available=False),
    }
    decision = select_model(RiskLevel.ALTO, confidence=0.9, catalog=catalog)
    assert decision.fallback_used is True
    assert decision.model.available is True
    assert decision.requested_tier == ModelTier.ROBUSTO


@pytest.mark.unit
def test_budget_exceeded_forces_economico() -> None:
    decision = select_model(RiskLevel.MEDIO, confidence=0.9, budget_status=BudgetStatus.EXCEEDED)
    assert decision.model.tier == ModelTier.ECONOMICO
    assert decision.budget_status == BudgetStatus.EXCEEDED
    assert "orçamento excedido" in decision.reason


@pytest.mark.unit
def test_budget_exceeded_high_risk_requires_human_review() -> None:
    decision = select_model(RiskLevel.ALTO, confidence=0.9, budget_status=BudgetStatus.EXCEEDED)
    assert decision.model.tier == ModelTier.ECONOMICO
    assert decision.requires_human_review is True


@pytest.mark.unit
def test_budget_near_limit_downgrades_tier() -> None:
    decision = select_model(RiskLevel.ALTO, confidence=0.9, budget_status=BudgetStatus.NEAR_LIMIT)
    # Alto risco pediria robusto; orçamento próximo rebaixa para intermediário.
    assert decision.model.tier == ModelTier.INTERMEDIARIO
    assert "rebaixado" in decision.reason


@pytest.mark.unit
def test_decision_includes_cost_and_latency() -> None:
    decision = select_model(
        RiskLevel.ALTO,
        confidence=0.9,
        estimated_input_tokens=1000,
        estimated_output_tokens=1000,
    )
    assert decision.model.tier == ModelTier.ROBUSTO
    # gpt-4o: 0.0025 (input) + 0.01 (output) por 1k tokens.
    assert decision.estimated_cost == pytest.approx(0.0125)
    assert decision.expected_latency_ms > 0


@pytest.mark.unit
def test_cost_latency_grow_with_tier() -> None:
    eco = select_model(
        RiskLevel.BAIXO, confidence=0.9, estimated_input_tokens=1000, estimated_output_tokens=1000
    )
    robust = select_model(
        RiskLevel.ALTO, confidence=0.9, estimated_input_tokens=1000, estimated_output_tokens=1000
    )
    assert eco.estimated_cost < robust.estimated_cost
    assert eco.expected_latency_ms < robust.expected_latency_ms


@pytest.mark.unit
def test_decision_reason_always_present() -> None:
    decision = select_model(RiskLevel.BAIXO, confidence=0.9)
    assert decision.reason
