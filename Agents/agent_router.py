"""Roteador de agentes (RF2.3, RF2.4).

Seleciona o agente correto a partir da saída da Query Intelligence Layer. O
roteamento é determinístico e explicável: domínio classificado → agente do
domínio; baixa confiança → fallback de busca ampla.

Entrada equivalente a::

    {"domain": "beneficios", "canonical_query": "...",
     "risk_level": "medio", "confidence": 0.91}

Saída equivalente a::

    {"selected_agent": "benefits_agent",
     "reason": "Pergunta classificada como benefícios com alta confiança",
     "fallback_required": false}
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agents.benefits_agent import BenefitsAgent
from app.agents.compensation_agent import CompensationAgent
from app.agents.compliance_agent import ComplianceAgent
from app.agents.labor_policy_agent import LaborPolicyAgent
from app.agents.learning_agent import LearningAgent
from app.agents.query_intelligence import Domain, QueryIntelligence
from app.agents.recruiting_agent import RecruitingAgent

# Mapeia domínio para o identificador público do agente (file-based id).
DOMAIN_TO_AGENT_ID: dict[Domain, str] = {
    Domain.BENEFICIOS: BenefitsAgent.AGENT_ID,
    Domain.TRABALHISTA: LaborPolicyAgent.AGENT_ID,
    Domain.CARGOS_SALARIOS: CompensationAgent.AGENT_ID,
    Domain.TREINAMENTO: LearningAgent.AGENT_ID,
    Domain.RECRUTAMENTO: RecruitingAgent.AGENT_ID,
    Domain.COMPLIANCE: ComplianceAgent.AGENT_ID,
}


@dataclass
class RouterDecision:
    """Decisão de roteamento explicável."""

    selected_agent: str
    domain: Domain
    reason: str
    fallback_required: bool

    def to_dict(self) -> dict[str, object]:
        """Serializa a decisão no formato de contrato da SPEC."""
        return {
            "selected_agent": self.selected_agent,
            "reason": self.reason,
            "fallback_required": self.fallback_required,
        }


def agent_id_for(domain: Domain) -> str:
    """Retorna o identificador público do agente de um domínio."""
    return DOMAIN_TO_AGENT_ID[domain]


def route(intel: QueryIntelligence) -> RouterDecision:
    """Seleciona o agente para a pergunta classificada."""
    selected = DOMAIN_TO_AGENT_ID[intel.domain]
    if intel.fallback_required:
        reason = (
            f"confiança {intel.confidence} abaixo do limiar; " "fallback de busca ampla acionado"
        )
        return RouterDecision(
            selected_agent=selected,
            domain=intel.domain,
            reason=reason,
            fallback_required=True,
        )
    reason = f"domínio classificado como '{intel.domain.value}' " f"(confiança {intel.confidence})"
    return RouterDecision(
        selected_agent=selected,
        domain=intel.domain,
        reason=reason,
        fallback_required=False,
    )
