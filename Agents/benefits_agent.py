"""Agente de Benefícios (SPEC Fase 2 §3.1).

Domínio: Benefícios. Escopo: férias, vale-refeição, vale-alimentação, plano de
saúde, abonos, auxílio-creche, vale-transporte, reembolsos e elegibilidade.
"""

from __future__ import annotations

from app.agents.base_agent import SpecialistAgent
from app.agents.query_intelligence import DOMAIN_TO_AREA, Domain, agent_name_for
from app.retrieval.retriever import Retriever


class BenefitsAgent(SpecialistAgent):
    """Agente especialista do domínio de Benefícios."""

    AGENT_ID = "benefits_agent"
    DOMAIN = Domain.BENEFICIOS
    AREA_RH = DOMAIN_TO_AREA[Domain.BENEFICIOS]
    SCOPE = (
        "Benefícios: férias, vale-refeição, vale-alimentação, plano de saúde, "
        "abonos, auxílio-creche, vale-transporte, reembolsos e elegibilidade de "
        "benefícios."
    )

    def __init__(self, retriever: Retriever) -> None:
        super().__init__(
            name=agent_name_for(self.DOMAIN),
            domain=self.DOMAIN,
            area_rh=self.AREA_RH,
            scope=self.SCOPE,
            retriever=retriever,
            agent_id=self.AGENT_ID,
        )
