"""Testes de integração do roteamento por domínio (SPEC Fase 2 §7)."""

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


@pytest.mark.integration
@pytest.mark.parametrize(
    ("question", "expected_agent", "expected_id"),
    [
        ("tenho direito a auxílio-creche para meu filho?", "agente_beneficios", "benefits_agent"),
        ("qual o prazo do banco de horas?", "agente_trabalhista", "labor_policy_agent"),
        (
            "como funciona a promoção por senioridade?",
            "agente_cargos_salarios",
            "compensation_agent",
        ),
        ("o curso de certificação é obrigatório?", "agente_treinamento", "learning_agent"),
        ("como me candidato a uma vaga interna?", "agente_recrutamento", "recruiting_agent"),
        ("como denunciar assédio no canal de ética?", "agente_compliance", "compliance_agent"),
    ],
)
def test_routes_question_to_expected_agent(
    orchestrator: Orchestrator, question: str, expected_agent: str, expected_id: str
) -> None:
    decision = orchestrator.route(question, _INTERNAL)
    assert decision.agent_used == expected_agent
    assert decision.agent_id == expected_id
    # Não chama todos os agentes: somente o necessário foi invocado.
    assert decision.agents_invoked == [expected_agent]


@pytest.mark.integration
def test_ambiguous_question_triggers_fallback(orchestrator: Orchestrator) -> None:
    decision = orchestrator.route("bom dia, tudo bem com você hoje?", _INTERNAL)
    assert decision.fallback_used is True
    assert "fallback" in decision.reason


@pytest.mark.integration
def test_orchestrator_does_not_call_all_agents(orchestrator: Orchestrator) -> None:
    decision = orchestrator.route("quantos dias de férias eu tenho?", _INTERNAL)
    assert len(decision.agents_invoked) == 1


@pytest.mark.integration
def test_decision_records_domain_agent_confidence_and_reason(
    orchestrator: Orchestrator,
) -> None:
    decision = orchestrator.route("qual o prazo do banco de horas?", _INTERNAL)
    assert decision.intel.domain.value == "trabalhista"
    assert decision.agent_used == "agente_trabalhista"
    assert decision.agent_id == "labor_policy_agent"
    assert decision.intel.confidence is not None
    assert decision.reason


@pytest.mark.integration
def test_compliance_routing_flags_human_review(orchestrator: Orchestrator) -> None:
    decision = orchestrator.route("como denunciar assédio e discriminação?", _INTERNAL)
    assert decision.agent_used == "agente_compliance"
    assert decision.screening is not None
    assert decision.screening.requires_human_review is True


@pytest.mark.integration
def test_domain_isolation_no_cross_leak(orchestrator: Orchestrator) -> None:
    decision = orchestrator.route("quantos dias de férias eu tenho?", _INTERNAL)
    areas = {c.chunk.area_rh for c in decision.chunks}
    assert areas == {"beneficios"}
