"""Agente de Recrutamento e Seleção (SPEC Fase 2 §3.5).

Domínio: Recrutamento e Seleção. Escopo: vagas, processo seletivo, indicação,
admissão, candidatura interna, entrevistas e onboarding admissional.
"""

from __future__ import annotations

from app.agents.base_agent import SpecialistAgent
from app.agents.query_intelligence import DOMAIN_TO_AREA, Domain, agent_name_for
from app.retrieval.retriever import Retriever


class RecruitingAgent(SpecialistAgent):
    """Agente especialista do domínio Recrutamento e Seleção."""

    AGENT_ID = "recruiting_agent"
    DOMAIN = Domain.RECRUTAMENTO
    AREA_RH = DOMAIN_TO_AREA[Domain.RECRUTAMENTO]
    SCOPE = (
        "Recrutamento e Seleção: vagas, processo seletivo, indicação, admissão, "
        "candidatura interna, entrevistas e onboarding admissional."
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
