"""Testes unitários do roteador de agentes (RF2.3, RF2.4)."""

from __future__ import annotations

import pytest

from app.agents.agent_router import DOMAIN_TO_AGENT_ID, RouterDecision, route
from app.agents.query_intelligence import Domain, classify


@pytest.mark.unit
def test_router_selects_benefits_agent() -> None:
    intel = classify("quantos dias de férias eu tenho?")
    decision = route(intel)
    assert decision.selected_agent == "benefits_agent"
    assert decision.fallback_required is False
    assert "beneficios" in decision.reason


@pytest.mark.unit
def test_router_selects_compliance_agent() -> None:
    intel = classify("como denunciar assédio no canal de ética?")
    decision = route(intel)
    assert decision.selected_agent == "compliance_agent"


@pytest.mark.unit
def test_router_flags_fallback_for_ambiguous_query() -> None:
    intel = classify("bom dia, tudo bem com você?")
    decision = route(intel)
    assert decision.fallback_required is True
    assert "fallback" in decision.reason


@pytest.mark.unit
def test_router_decision_serializes_to_contract() -> None:
    intel = classify("qual o prazo do banco de horas?")
    payload = route(intel).to_dict()
    assert set(payload) == {"selected_agent", "reason", "fallback_required"}
    assert payload["selected_agent"] == "labor_policy_agent"


@pytest.mark.unit
def test_all_domains_have_agent_id() -> None:
    assert set(DOMAIN_TO_AGENT_ID) == set(Domain)
    assert all(isinstance(v, str) and v for v in DOMAIN_TO_AGENT_ID.values())


@pytest.mark.unit
def test_router_decision_dataclass_fields() -> None:
    decision = RouterDecision(
        selected_agent="benefits_agent",
        domain=Domain.BENEFICIOS,
        reason="x",
        fallback_required=False,
    )
    assert decision.domain == Domain.BENEFICIOS
