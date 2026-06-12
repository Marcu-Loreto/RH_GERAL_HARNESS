"""Compatibilidade legada do registro de agentes (SPEC Fase 2 §3).

Os agentes especialistas foram movidos para arquivos próprios (``benefits_agent``,
``labor_policy_agent``, ``compensation_agent``, ``learning_agent``,
``recruiting_agent``, ``compliance_agent``) e o registro central passou para
``agent_registry``. Este módulo é mantido apenas para compatibilidade: reexporta
os agentes e preserva a função ``build_agents`` delegando ao novo registro.
"""

from __future__ import annotations

from app.agents.agent_registry import AGENT_REGISTRY, build_registry
from app.agents.base_agent import SpecialistAgent
from app.agents.benefits_agent import BenefitsAgent
from app.agents.compensation_agent import CompensationAgent
from app.agents.compliance_agent import ComplianceAgent
from app.agents.labor_policy_agent import LaborPolicyAgent
from app.agents.learning_agent import LearningAgent
from app.agents.query_intelligence import Domain
from app.agents.recruiting_agent import RecruitingAgent
from app.retrieval.retriever import Retriever

__all__ = [
    "AGENT_REGISTRY",
    "BenefitsAgent",
    "CompensationAgent",
    "ComplianceAgent",
    "LaborPolicyAgent",
    "LearningAgent",
    "RecruitingAgent",
    "build_agents",
]


def build_agents(retriever: Retriever) -> dict[Domain, SpecialistAgent]:
    """Constrói o registro de agentes (legado; delega a ``build_registry``)."""
    return build_registry(retriever)
