"""Agente especialista base (RF2.3, RF2.6).

Cada agente atende a um único domínio de RH e consulta apenas documentos da sua
área (filtro por metadados). Os agentes não acessam ferramentas fora do escopo:
no MVP a única ferramenta permitida é o retrieval filtrado por domínio.

Os agentes concretos vivem em arquivos separados (``benefits_agent.py``,
``labor_policy_agent.py`` etc.) e herdam desta classe, declarando explicitamente
domínio, área, escopo, regras de risco e comportamento de revisão humana.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.agents.agent_prompts import get_agent_scope
from app.agents.query_intelligence import Domain, QueryIntelligence, agent_name_for
from app.core.logging import get_logger
from app.core.models import Confidentiality
from app.retrieval.retriever import RetrievalResult, Retriever
from app.retrieval.vector_store import RetrievalFilters

logger = get_logger(__name__)


@dataclass
class AgentScreening:
    """Resultado da triagem de risco de um agente sobre uma pergunta.

    Atributos:
        blocked: A pergunta não pode ser respondida pelo agente (ex.: pedido de
            dado individual sensível).
        requires_human_review: A resposta deve ser encaminhada para revisão
            humana (ex.: tema sensível de compliance ou trabalhista).
        reason: Justificativa explicável da decisão (registrada no trace).
    """

    blocked: bool = False
    requires_human_review: bool = False
    reason: str = ""


class SpecialistAgent:
    """Agente de um domínio específico de RH.

    Subclasses declaram, via atributos de classe, ``AGENT_ID``, ``DOMAIN``,
    ``AREA_RH``, ``SCOPE`` e ``RISK_RULES``, e podem sobrescrever ``screen`` para
    expressar regras de risco/escala humana próprias do domínio.
    """

    AGENT_ID: str = ""
    DOMAIN: Domain | None = None
    AREA_RH: str = ""
    SCOPE: str = ""
    RISK_RULES: tuple[str, ...] = ()

    def __init__(
        self,
        name: str,
        domain: Domain,
        area_rh: str,
        scope: str,
        retriever: Retriever,
        *,
        agent_id: str = "",
        risk_rules: tuple[str, ...] = (),
    ) -> None:
        self.name = name
        self.domain = domain
        self.area_rh = area_rh
        self.agent_id = agent_id or name
        # O escopo (prompt) vem do arquivo em ``prompts/agents``; o valor passado
        # pela classe do agente é o fallback caso o arquivo esteja ausente.
        self.scope = get_agent_scope(self.agent_id, default=scope)
        self.risk_rules = risk_rules
        self._retriever = retriever

    def retrieve(
        self,
        intel: QueryIntelligence,
        allowed_confidentiality: list[Confidentiality],
        *,
        broad: bool = False,
        reference_date: datetime | None = None,
    ) -> RetrievalResult:
        """Recupera evidências do domínio do agente.

        Args:
            intel: Saída da Query Intelligence Layer.
            allowed_confidentiality: Níveis permitidos para o perfil do usuário.
            broad: Se ``True``, ignora o filtro de área (fallback de busca ampla).
            reference_date: Data de referência para o filtro de vigência. Quando
                ``None``, usa a data atual (UTC), garantindo que documentos
                aprovados porém expirados não sejam recuperados (RF1.5).
        """
        effective_date = reference_date or datetime.now(UTC)
        filters = RetrievalFilters(
            area_rh=None if broad else self.area_rh,
            allowed_confidentiality=allowed_confidentiality,
            reference_date=effective_date,
            only_approved=True,
        )
        result = self._retriever.retrieve(intel.canonical_query, filters)
        logger.info(
            "agent_retrieval",
            agent=self.name,
            domain=self.domain.value if self.domain else None,
            broad=broad,
            relevant=len(result.results),
        )
        return result

    def screen(self, intel: QueryIntelligence) -> AgentScreening:
        """Triagem de risco específica do agente (default: sem ação)."""
        return AgentScreening()


def default_agent_name(domain: Domain) -> str:
    """Nome canônico do agente para um domínio (compatibilidade de trace)."""
    return agent_name_for(domain)
