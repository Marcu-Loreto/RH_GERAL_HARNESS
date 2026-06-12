"""Testes unitários de comportamento de risco e isolamento dos agentes."""

from __future__ import annotations

import pytest

from app.agents.agent_registry import build_registry
from app.agents.compensation_agent import CompensationAgent
from app.agents.compliance_agent import ComplianceAgent
from app.agents.labor_policy_agent import LaborPolicyAgent
from app.agents.query_intelligence import DOMAIN_TO_AREA, Domain, classify
from app.core.models import Confidentiality
from app.retrieval.retriever import Retriever
from app.retrieval.vector_store import InMemoryVectorStore

_INTERNAL = [Confidentiality.PUBLICO, Confidentiality.INTERNO]


@pytest.fixture()
def retriever() -> Retriever:
    return Retriever(store=InMemoryVectorStore())


@pytest.mark.unit
def test_compensation_blocks_individual_salary(retriever: Retriever) -> None:
    agent = CompensationAgent(retriever)
    intel = classify("qual é o salário individual de outro funcionário?")
    screening = agent.screen(intel)
    assert screening.blocked is True
    assert screening.reason


@pytest.mark.unit
def test_compensation_allows_general_salary_policy(retriever: Retriever) -> None:
    agent = CompensationAgent(retriever)
    intel = classify("como funciona a faixa salarial e a promoção do cargo?")
    assert agent.screen(intel).blocked is False


@pytest.mark.unit
def test_compliance_flags_human_review_on_sensitive(retriever: Retriever) -> None:
    agent = ComplianceAgent(retriever)
    intel = classify("como denunciar um caso de assédio e discriminação?")
    screening = agent.screen(intel)
    assert screening.requires_human_review is True
    assert screening.reason


@pytest.mark.unit
def test_compliance_no_review_on_simple_channel_question(retriever: Retriever) -> None:
    agent = ComplianceAgent(retriever)
    intel = classify("qual o horário de funcionamento do canal de ética?")
    assert agent.screen(intel).requires_human_review is False


@pytest.mark.unit
def test_labor_policy_flags_higher_risk_on_sensitive(retriever: Retriever) -> None:
    agent = LaborPolicyAgent(retriever)
    intel = classify("como funciona o afastamento por atestado médico?")
    screening = agent.screen(intel)
    assert screening.requires_human_review is True
    assert screening.reason


@pytest.mark.unit
def test_labor_policy_no_review_on_routine_question(retriever: Retriever) -> None:
    agent = LaborPolicyAgent(retriever)
    intel = classify("quantos dias de trabalho remoto por semana são permitidos?")
    assert agent.screen(intel).requires_human_review is False


@pytest.mark.unit
def test_agents_use_filters_compatible_with_their_area(
    populated_store: InMemoryVectorStore,
) -> None:
    retriever = Retriever(store=populated_store)
    agents = build_registry(retriever)
    for domain, agent in agents.items():
        if domain in (Domain.BENEFICIOS, Domain.TRABALHISTA):
            intel = classify("política da empresa")
            result = agent.retrieve(intel, _INTERNAL)
            areas = {c.chunk.area_rh for c in result.results}
            assert areas <= {DOMAIN_TO_AREA[domain]}


@pytest.mark.unit
def test_no_agent_accesses_outside_its_domain(populated_store: InMemoryVectorStore) -> None:
    retriever = Retriever(store=populated_store)
    agent = build_registry(retriever)[Domain.BENEFICIOS]
    intel = classify("quantos dias de férias eu tenho?")
    result = agent.retrieve(intel, _INTERNAL)
    areas = {c.chunk.area_rh for c in result.results}
    assert areas <= {DOMAIN_TO_AREA[Domain.BENEFICIOS]}
