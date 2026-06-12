"""Agente de Compliance e Conduta (SPEC Fase 2 §3.6).

Domínio: Compliance e Conduta. Escopo: ética, denúncias, assédio, discriminação,
conflito de interesses, código de conduta e canal de denúncia.

Restrição: casos sensíveis devem recomendar/permitir escalonamento humano.
"""

from __future__ import annotations

from app.agents.base_agent import AgentScreening, SpecialistAgent
from app.agents.query_intelligence import (
    DOMAIN_TO_AREA,
    Domain,
    QueryIntelligence,
    RiskLevel,
    agent_name_for,
)
from app.retrieval.retriever import Retriever

# Temas sensíveis de conduta que exigem escalonamento humano.
_SENSITIVE_CONDUCT_TERMS: tuple[str, ...] = (
    "assédio",
    "assedio",
    "discriminação",
    "discriminacao",
    "fraude",
    "retaliação",
    "retaliacao",
    "conflito de interesse",
)


class ComplianceAgent(SpecialistAgent):
    """Agente especialista do domínio Compliance e Conduta."""

    AGENT_ID = "compliance_agent"
    DOMAIN = Domain.COMPLIANCE
    AREA_RH = DOMAIN_TO_AREA[Domain.COMPLIANCE]
    SCOPE = (
        "Compliance e Conduta: ética, denúncias, assédio, discriminação, "
        "conflito de interesses, código de conduta e canal de denúncia."
    )
    RISK_RULES = _SENSITIVE_CONDUCT_TERMS

    def __init__(self, retriever: Retriever) -> None:
        super().__init__(
            name=agent_name_for(self.DOMAIN),
            domain=self.DOMAIN,
            area_rh=self.AREA_RH,
            scope=self.SCOPE,
            retriever=retriever,
            agent_id=self.AGENT_ID,
            risk_rules=self.RISK_RULES,
        )

    def screen(self, intel: QueryIntelligence) -> AgentScreening:
        """Recomenda escalonamento humano em temas sensíveis de conduta."""
        lowered = intel.canonical_query.lower()
        sensitive = any(term in lowered for term in self.RISK_RULES)
        if sensitive or intel.risk_level == RiskLevel.ALTO:
            return AgentScreening(
                requires_human_review=True,
                reason="tema sensível de conduta: recomenda escalonamento humano",
            )
        return AgentScreening()
