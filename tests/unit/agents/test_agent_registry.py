"""Testes unitários do registro e instanciação dos agentes (SPEC Fase 2 §3)."""

from __future__ import annotations

import pytest

from app.agents.agent_registry import AGENT_REGISTRY, build_registry, registered_domains
from app.agents.base_agent import SpecialistAgent
from app.agents.benefits_agent import BenefitsAgent
from app.agents.compensation_agent import CompensationAgent
from app.agents.compliance_agent import ComplianceAgent
from app.agents.labor_policy_agent import LaborPolicyAgent
from app.agents.learning_agent import LearningAgent
from app.agents.query_intelligence import DOMAIN_TO_AREA, Domain
from app.agents.recruiting_agent import RecruitingAgent
from app.retrieval.retriever import Retriever
from app.retrieval.vector_store import InMemoryVectorStore

_EXPECTED_DOMAINS = {
    Domain.BENEFICIOS,
    Domain.TRABALHISTA,
    Domain.CARGOS_SALARIOS,
    Domain.TREINAMENTO,
    Domain.RECRUTAMENTO,
    Domain.COMPLIANCE,
}

_EXPECTED_CLASSES = {
    Domain.BENEFICIOS: BenefitsAgent,
    Domain.TRABALHISTA: LaborPolicyAgent,
    Domain.CARGOS_SALARIOS: CompensationAgent,
    Domain.TREINAMENTO: LearningAgent,
    Domain.RECRUTAMENTO: RecruitingAgent,
    Domain.COMPLIANCE: ComplianceAgent,
}


@pytest.fixture()
def retriever() -> Retriever:
    return Retriever(store=InMemoryVectorStore())


@pytest.mark.unit
def test_registry_has_exactly_six_agents() -> None:
    assert len(AGENT_REGISTRY) == 6


@pytest.mark.unit
def test_registry_contains_all_expected_domains() -> None:
    assert set(registered_domains()) == _EXPECTED_DOMAINS


@pytest.mark.unit
def test_registry_maps_each_domain_to_correct_class() -> None:
    assert AGENT_REGISTRY == _EXPECTED_CLASSES


@pytest.mark.unit
def test_each_agent_instantiates(retriever: Retriever) -> None:
    agents = build_registry(retriever)
    assert len(agents) == 6
    assert all(isinstance(agent, SpecialistAgent) for agent in agents.values())


@pytest.mark.unit
def test_each_agent_declares_required_attributes(retriever: Retriever) -> None:
    for domain, agent in build_registry(retriever).items():
        assert agent.name == f"agente_{domain.value}"
        assert agent.agent_id
        assert agent.domain == domain
        assert agent.area_rh == DOMAIN_TO_AREA[domain]
        assert agent.scope
        assert agent._retriever is retriever


@pytest.mark.unit
def test_agent_domain_matches_area(retriever: Retriever) -> None:
    for domain, agent in build_registry(retriever).items():
        assert agent.area_rh == DOMAIN_TO_AREA[domain]
