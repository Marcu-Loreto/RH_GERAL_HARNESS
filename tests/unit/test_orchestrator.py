"""Testes unitários do orquestrador multiagente (RF2.3, RF2.4, RF2.6)."""

from __future__ import annotations

import pytest

from app.agents.orchestrator import Orchestrator
from app.core.models import Confidentiality
from app.retrieval.retriever import Retriever
from app.retrieval.vector_store import InMemoryVectorStore

_INTERNAL = [Confidentiality.PUBLICO, Confidentiality.INTERNO]


@pytest.fixture()
def orchestrator(populated_store: InMemoryVectorStore) -> Orchestrator:
    return Orchestrator(Retriever(store=populated_store))


@pytest.mark.unit
def test_registers_six_agents(orchestrator: Orchestrator) -> None:
    assert len(orchestrator.known_agents()) == 6


@pytest.mark.unit
def test_routes_benefits_to_benefits_agent(orchestrator: Orchestrator) -> None:
    decision = orchestrator.route("quantos dias de férias?", _INTERNAL)
    assert decision.agent_used == "agente_beneficios"
    assert decision.fallback_used is False
    assert decision.chunks
    # Não chama todos os agentes: apenas o necessário foi invocado.
    assert decision.agents_invoked == ["agente_beneficios"]


@pytest.mark.unit
def test_routes_compliance_to_compliance_agent(orchestrator: Orchestrator) -> None:
    decision = orchestrator.route("denúncia de assédio no canal de ética", _INTERNAL)
    assert decision.agent_used == "agente_compliance"
    assert decision.chunks


@pytest.mark.unit
def test_low_confidence_triggers_fallback(orchestrator: Orchestrator) -> None:
    decision = orchestrator.route("bom dia, tudo bem?", _INTERNAL)
    assert decision.fallback_used is True
    assert "fallback" in decision.reason


@pytest.mark.unit
def test_domain_isolation_no_cross_leak(orchestrator: Orchestrator) -> None:
    # Pergunta de benefícios não deve trazer documentos de outras áreas.
    decision = orchestrator.route("quantos dias de férias?", _INTERNAL)
    areas = {c.chunk.area_rh for c in decision.chunks}
    assert areas == {"beneficios"}
