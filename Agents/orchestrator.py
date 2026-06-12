"""Orquestrador multiagente (RF2.3, RF2.4, RF2.5, RF2.7).

Seleciona apenas o agente necessário com base na Query Intelligence Layer e no
roteador de agentes (``agent_router``). Os agentes são obtidos do registro
central (``agent_registry``). Em baixa confiança, usa fallback de busca ampla.
Em perguntas multidomínio, aciona um agente auxiliar com razão registrada. Toda
decisão é explicável e rastreável.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.agents.agent_registry import build_registry
from app.agents.agent_router import route as route_agent
from app.agents.base_agent import AgentScreening, SpecialistAgent
from app.agents.query_intelligence import (
    Domain,
    QueryIntelligence,
    agent_name_for,
    classify,
)
from app.core.logging import get_logger
from app.core.models import Confidentiality
from app.retrieval.retriever import Retriever
from app.retrieval.vector_store import ScoredChunk

logger = get_logger(__name__)


@dataclass
class OrchestrationDecision:
    """Decisão de roteamento com evidências recuperadas (explicável)."""

    intel: QueryIntelligence
    agent_used: str
    chunks: list[ScoredChunk]
    fallback_used: bool
    auxiliary_agent: str | None
    reason: str
    agents_invoked: list[str] = field(default_factory=list)
    agent_id: str | None = None
    screening: AgentScreening | None = None


class Orchestrator:
    """Roteia a pergunta para o agente especialista adequado."""

    def __init__(self, retriever: Retriever) -> None:
        self._agents: dict[Domain, SpecialistAgent] = build_registry(retriever)

    def route(
        self,
        query: str,
        allowed_confidentiality: list[Confidentiality],
        *,
        forced_area: str | None = None,
    ) -> OrchestrationDecision:
        """Classifica, seleciona o agente e recupera evidências."""
        intel = classify(query, forced_area=forced_area)
        router_decision = route_agent(intel)

        # Fallback: classificação incerta → busca ampla (sem filtro de domínio).
        if intel.fallback_required:
            agent = self._agents[intel.domain]
            result = agent.retrieve(intel, allowed_confidentiality, broad=True)
            screening = agent.screen(intel)
            logger.info(
                "orchestrator_decision",
                agent=agent.name,
                agent_id=agent.agent_id,
                domain=intel.domain.value,
                confidence=intel.confidence,
                fallback=True,
                requires_human_review=screening.requires_human_review,
                reason=router_decision.reason,
            )
            return OrchestrationDecision(
                intel=intel,
                agent_used=agent.name,
                chunks=result.results,
                fallback_used=True,
                auxiliary_agent=None,
                reason=router_decision.reason,
                agents_invoked=[agent.name],
                agent_id=agent.agent_id,
                screening=screening,
            )

        primary = self._agents[intel.domain]
        result = primary.retrieve(intel, allowed_confidentiality)
        screening = primary.screen(intel)
        invoked = [primary.name]
        reason = router_decision.reason
        auxiliary_name: str | None = None

        # Multidomínio: aciona auxiliar apenas se o primário não trouxe evidência.
        if intel.secondary_domain is not None and not result.has_evidence:
            auxiliary = self._agents[intel.secondary_domain]
            aux_result = auxiliary.retrieve(intel, allowed_confidentiality)
            auxiliary_name = auxiliary.name
            invoked.append(auxiliary.name)
            reason += (
                f"; agente auxiliar '{intel.secondary_domain.value}' acionado "
                "por ausência de evidência no domínio principal"
            )
            if aux_result.has_evidence:
                result = aux_result

        logger.info(
            "orchestrator_decision",
            agent=primary.name,
            agent_id=primary.agent_id,
            domain=intel.domain.value,
            confidence=intel.confidence,
            fallback=False,
            auxiliary=auxiliary_name,
            requires_human_review=screening.requires_human_review,
            reason=reason,
        )
        return OrchestrationDecision(
            intel=intel,
            agent_used=primary.name,
            chunks=result.results,
            fallback_used=False,
            auxiliary_agent=auxiliary_name,
            reason=reason,
            agents_invoked=invoked,
            agent_id=primary.agent_id,
            screening=screening,
        )

    def known_agents(self) -> list[str]:
        """Lista os nomes dos agentes registrados."""
        return [agent_name_for(domain) for domain in self._agents]
