"""Agente Trabalhista / Políticas Internas (SPEC Fase 2 §3.2).

Domínio: Trabalhista / Políticas Internas. Escopo: jornada, banco de horas,
trabalho remoto, férias, afastamentos, ponto, licenças, atestados e políticas
internas. Sinaliza risco maior em temas trabalhistas sensíveis.
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

# Temas trabalhistas sensíveis que elevam o risco e pedem cautela/revisão.
_SENSITIVE_LABOR_TERMS: tuple[str, ...] = (
    "afastamento",
    "atestado",
    "demissão",
    "demissao",
    "disciplinar",
    "advertência",
    "advertencia",
    "sindical",
    "sindicato",
    "justa causa",
    "rescisão",
    "rescisao",
    "suspensão",
    "suspensao",
)


class LaborPolicyAgent(SpecialistAgent):
    """Agente especialista do domínio Trabalhista / Políticas Internas."""

    AGENT_ID = "labor_policy_agent"
    DOMAIN = Domain.TRABALHISTA
    AREA_RH = DOMAIN_TO_AREA[Domain.TRABALHISTA]
    SCOPE = (
        "Trabalhista / Políticas Internas: jornada, banco de horas, trabalho "
        "remoto, férias, afastamentos, ponto, licenças, atestados e políticas "
        "internas."
    )
    RISK_RULES = _SENSITIVE_LABOR_TERMS

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
        """Sinaliza risco maior e revisão humana em temas trabalhistas sensíveis."""
        lowered = intel.canonical_query.lower()
        sensitive = any(term in lowered for term in self.RISK_RULES)
        if sensitive or intel.risk_level == RiskLevel.ALTO:
            return AgentScreening(
                requires_human_review=True,
                reason="tema trabalhista sensível: risco elevado, recomenda revisão humana",
            )
        return AgentScreening()
