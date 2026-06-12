"""Testes unitários de cálculo e agregação de custo FinOps (RF3.1 / RF3.5)."""

from __future__ import annotations

import pytest

from app.core.model_router import ModelTier, get_model
from app.finops.cost import CostRecord, FinOpsTracker, estimate_cost


@pytest.mark.unit
def test_estimate_cost_economico_is_zero() -> None:
    model = get_model(ModelTier.ECONOMICO)
    assert estimate_cost(model, 1000, 1000) == 0.0


@pytest.mark.unit
def test_estimate_cost_robusto() -> None:
    model = get_model(ModelTier.ROBUSTO)
    # 2000 in (0.0025/1k) + 1000 out (0.01/1k) = 0.005 + 0.01 = 0.015
    assert estimate_cost(model, 2000, 1000) == pytest.approx(0.015)


@pytest.mark.unit
def test_estimate_cost_rejects_negative_tokens() -> None:
    model = get_model(ModelTier.ROBUSTO)
    with pytest.raises(ValueError):
        estimate_cost(model, -1, 10)


@pytest.mark.unit
def test_tracker_aggregates_by_dimension() -> None:
    tracker = FinOpsTracker()
    tracker.record(CostRecord("t1", "agente_beneficios", "gpt-4o", "api", 100, 50, 0.02))
    tracker.record(CostRecord("t2", "agente_beneficios", "gpt-4o-mini", "web", 80, 40, 0.001))
    tracker.record(CostRecord("t3", "agente_compliance", "gpt-4o", "api", 120, 60, 0.03))

    summary = tracker.summary()
    assert summary.answer_count == 3
    assert summary.total_cost == pytest.approx(0.051)
    assert summary.total_tokens == 450
    assert summary.cost_by_agent["agente_beneficios"] == pytest.approx(0.021)
    assert summary.cost_by_model["gpt-4o"] == pytest.approx(0.05)
    assert summary.cost_by_channel["api"] == pytest.approx(0.05)
    assert summary.avg_cost_per_answer == pytest.approx(0.017)


@pytest.mark.unit
def test_empty_tracker_summary() -> None:
    summary = FinOpsTracker().summary()
    assert summary.answer_count == 0
    assert summary.total_cost == 0.0
    assert summary.avg_cost_per_answer == 0.0
