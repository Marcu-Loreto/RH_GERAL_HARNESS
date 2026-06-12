"""Agente de Cargos, Salários e Competências (SPEC Fase 2 §3.3).

Domínio: Cargos, Salários e Competências. Escopo: remuneração, promoção, níveis,
senioridade, competências, plano de carreira e descrições de cargo.

Restrição: não revelar salários individuais — pedidos desse tipo são bloqueados.
"""

from __future__ import annotations

from app.agents.base_agent import AgentScreening, SpecialistAgent
from app.agents.query_intelligence import (
    DOMAIN_TO_AREA,
    Domain,
    QueryIntelligence,
    agent_name_for,
)
from app.retrieval.retriever import Retriever

# Termos de remuneração e indicadores de individualização (dado pessoal).
_SALARY_TERMS: tuple[str, ...] = (
    "salário",
    "salario",
    "remuneração",
    "remuneracao",
    "ganha",
    "ganho",
    "recebe",
)
_INDIVIDUAL_INDICATORS: tuple[str, ...] = (
    "individual",
    "colega",
    "funcionário",
    "funcionario",
    "colaborador",
    "pessoa",
    "fulano",
    "terceiro",
    "outro",
)


class CompensationAgent(SpecialistAgent):
    """Agente especialista do domínio Cargos, Salários e Competências."""

    AGENT_ID = "compensation_agent"
    DOMAIN = Domain.CARGOS_SALARIOS
    AREA_RH = DOMAIN_TO_AREA[Domain.CARGOS_SALARIOS]
    SCOPE = (
        "Cargos, Salários e Competências: remuneração, promoção, níveis, "
        "senioridade, competências, plano de carreira e descrições de cargo. "
        "Não revela salários individuais."
    )
    RISK_RULES = ("não revelar salário individual",)

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
        """Bloqueia pedidos de salário individual de terceiros."""
        lowered = intel.canonical_query.lower()
        asks_salary = any(term in lowered for term in _SALARY_TERMS)
        is_individual = any(term in lowered for term in _INDIVIDUAL_INDICATORS)
        if asks_salary and is_individual:
            return AgentScreening(
                blocked=True,
                reason="pedido de salário individual de terceiro não é permitido",
            )
        return AgentScreening()
