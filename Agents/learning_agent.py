"""Agente de Treinamento e Desenvolvimento (SPEC Fase 2 §3.4).

Domínio: Treinamento e Desenvolvimento. Escopo: cursos, trilhas, certificações,
onboarding, PDI, avaliação de desempenho e desenvolvimento de carreira.
"""

from __future__ import annotations

from app.agents.base_agent import SpecialistAgent
from app.agents.query_intelligence import DOMAIN_TO_AREA, Domain, agent_name_for
from app.retrieval.retriever import Retriever


class LearningAgent(SpecialistAgent):
    """Agente especialista do domínio Treinamento e Desenvolvimento."""

    AGENT_ID = "learning_agent"
    DOMAIN = Domain.TREINAMENTO
    AREA_RH = DOMAIN_TO_AREA[Domain.TREINAMENTO]
    SCOPE = (
        "Treinamento e Desenvolvimento: cursos, trilhas, certificações, "
        "onboarding, PDI, avaliação de desempenho e desenvolvimento de carreira."
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
