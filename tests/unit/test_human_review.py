"""Testes unitários da regra de human-in-the-loop (RF3.6)."""

from __future__ import annotations

import pytest

from app.agents.query_intelligence import RiskLevel
from app.core.models import Confidence
from app.escalation.human_review import evaluate_escalation


@pytest.mark.unit
def test_high_risk_is_escalated() -> None:
    decision = evaluate_escalation(
        risk=RiskLevel.ALTO,
        confidence=Confidence.ALTA,
        has_evidence=True,
        routing_confidence=0.9,
        min_routing_confidence=0.34,
    )
    assert decision.escalate is True
    assert "alto risco" in decision.reason


@pytest.mark.unit
def test_no_evidence_is_escalated() -> None:
    decision = evaluate_escalation(
        risk=RiskLevel.BAIXO,
        confidence=Confidence.MEDIA,
        has_evidence=False,
        routing_confidence=0.9,
        min_routing_confidence=0.34,
    )
    assert decision.escalate is True
    assert "evidência" in decision.reason


@pytest.mark.unit
def test_low_confidence_is_escalated() -> None:
    decision = evaluate_escalation(
        risk=RiskLevel.BAIXO,
        confidence=Confidence.BAIXA,
        has_evidence=True,
        routing_confidence=0.9,
        min_routing_confidence=0.34,
    )
    assert decision.escalate is True


@pytest.mark.unit
def test_safe_answer_is_not_escalated() -> None:
    decision = evaluate_escalation(
        risk=RiskLevel.BAIXO,
        confidence=Confidence.ALTA,
        has_evidence=True,
        routing_confidence=0.9,
        min_routing_confidence=0.34,
    )
    assert decision.escalate is False
    assert decision.reason == ""
