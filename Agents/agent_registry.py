"""Registro central dos agentes especialistas (SPEC Fase 2 §3).

Centraliza o mapeamento ``Domain → classe de agente``. Adicionar um novo agente
significa criar o arquivo do agente e registrá-lo aqui — nenhum outro ponto do
sistema precisa ser alterado (o orquestrador consome este registro).
"""

from __future__ import annotations

from collections.abc import Callable

from app.agents.base_agent import SpecialistAgent
from app.agents.benefits_agent import BenefitsAgent
from app.agents.compensation_agent import CompensationAgent
from app.agents.compliance_agent import ComplianceAgent
from app.agents.labor_policy_agent import LaborPolicyAgent
from app.agents.learning_agent import LearningAgent
from app.agents.query_intelligence import Domain
from app.agents.recruiting_agent import RecruitingAgent
from app.retrieval.retriever import Retriever

# Mapeamento único de domínio para a fábrica do agente responsável. Cada valor é
# a classe do agente, que é construída apenas com o ``retriever``.
AgentFactory = Callable[[Retriever], SpecialistAgent]

AGENT_REGISTRY: dict[Domain, AgentFactory] = {
    Domain.BENEFICIOS: BenefitsAgent,
    Domain.TRABALHISTA: LaborPolicyAgent,
    Domain.CARGOS_SALARIOS: CompensationAgent,
    Domain.TREINAMENTO: LearningAgent,
    Domain.RECRUTAMENTO: RecruitingAgent,
    Domain.COMPLIANCE: ComplianceAgent,
}


def build_registry(retriever: Retriever) -> dict[Domain, SpecialistAgent]:
    """Instancia todos os agentes registrados, indexados por domínio."""
    return {domain: factory(retriever) for domain, factory in AGENT_REGISTRY.items()}


def registered_domains() -> list[Domain]:
    """Lista os domínios cobertos por um agente especialista."""
    return list(AGENT_REGISTRY)
