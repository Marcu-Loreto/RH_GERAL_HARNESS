"""Cache semântico seguro com validação de domínio, acesso, versão e risco (RF3.4).

Reaproveita respostas para perguntas equivalentes (similaridade de embedding
acima do limiar) somente quando, cumulativamente:
  1. pertencem ao **mesmo domínio** (não há reuso entre domínios distintos);
  2. o perfil que consulta tem acesso a todos os níveis de confidencialidade das
     evidências usadas na resposta em cache (sem vazamento de acesso);
  3. as versões dos documentos que sustentam a resposta continuam vigentes
     (invalidação por versão de documento).

Além disso, o pipeline deve **ignorar o cache** (bypass) em contextos sensíveis:
PII detectada, risco alto ou necessidade de revisão humana — ver
``cache_bypass_reason``. O motivo do bypass é registrado no trace.

Implementação em memória, determinística, alinhada ao MVP. Substituível por um
cache distribuído (ex.: Redis + embeddings) sem alterar a interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.agents.query_intelligence import RiskLevel
from app.core.logging import get_logger
from app.core.models import Answer, Confidentiality
from app.retrieval.embeddings import cosine_similarity

logger = get_logger(__name__)


def cache_bypass_reason(
    *,
    has_pii: bool,
    risk_level: RiskLevel,
    requires_human_review: bool,
) -> str | None:
    """Retorna o motivo para ignorar o cache, ou ``None`` se o cache é permitido.

    O cache é ignorado em contextos sensíveis para evitar reuso indevido de
    respostas que dependem de contexto/decisão humana.
    """
    if has_pii:
        return "pii_detectada"
    if risk_level == RiskLevel.ALTO:
        return "risco_alto"
    if requires_human_review:
        return "revisao_humana_obrigatoria"
    return None


@dataclass
class CacheEntry:
    """Entrada do cache: resposta + restrições de domínio, permissão e versão."""

    canonical_query: str
    domain: str
    embedding: list[float]
    answer: Answer
    # Níveis de confidencialidade exigidos pelas evidências da resposta.
    required_confidentiality: frozenset[str]
    # Versões dos documentos que sustentam a resposta (source_id → version).
    document_versions: dict[str, str]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CacheLookupResult:
    """Resultado de uma consulta ao cache."""

    hit: bool
    answer: Answer | None = None
    reason: str = ""


class SemanticCache:
    """Cache semântico volátil com validação de domínio, acesso e vigência."""

    def __init__(self, similarity_threshold: float = 0.92) -> None:
        self._threshold = similarity_threshold
        self._entries: list[CacheEntry] = []

    def clear(self) -> None:
        """Remove todas as entradas (útil em testes)."""
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)

    def _permission_ok(
        self, entry: CacheEntry, allowed_confidentiality: list[Confidentiality]
    ) -> bool:
        allowed = {c.value for c in allowed_confidentiality}
        return entry.required_confidentiality.issubset(allowed)

    def _versions_ok(self, entry: CacheEntry, current_versions: dict[str, str]) -> bool:
        for source_id, version in entry.document_versions.items():
            if current_versions.get(source_id) != version:
                return False
        return True

    def lookup(
        self,
        query_embedding: list[float],
        *,
        domain: str,
        allowed_confidentiality: list[Confidentiality],
        current_versions: dict[str, str],
    ) -> CacheLookupResult:
        """Busca uma resposta equivalente, do mesmo domínio, válida para o perfil."""
        best: CacheEntry | None = None
        best_score = 0.0
        for entry in self._entries:
            if entry.domain != domain:
                continue
            score = cosine_similarity(query_embedding, entry.embedding)
            if score >= self._threshold and score > best_score:
                best, best_score = entry, score

        if best is None:
            logger.info("cache_miss", reason="sem_pergunta_equivalente", domain=domain)
            return CacheLookupResult(hit=False, reason="miss")

        if not self._permission_ok(best, allowed_confidentiality):
            logger.info("cache_miss", reason="permissao_incompativel", domain=domain)
            return CacheLookupResult(hit=False, reason="permissao_incompativel")

        if not self._versions_ok(best, current_versions):
            logger.info("cache_miss", reason="documento_desatualizado", domain=domain)
            return CacheLookupResult(hit=False, reason="documento_desatualizado")

        logger.info("cache_hit", similarity=round(best_score, 3), domain=domain)
        return CacheLookupResult(hit=True, answer=best.answer, reason="hit")

    def store(
        self,
        canonical_query: str,
        query_embedding: list[float],
        answer: Answer,
        *,
        domain: str,
        required_confidentiality: frozenset[str],
        document_versions: dict[str, str],
    ) -> None:
        """Armazena uma resposta no cache com suas restrições de uso."""
        self._entries.append(
            CacheEntry(
                canonical_query=canonical_query,
                domain=domain,
                embedding=query_embedding,
                answer=answer,
                required_confidentiality=required_confidentiality,
                document_versions=document_versions,
            )
        )
        logger.info("cache_store", entries=len(self._entries), domain=domain)

    def invalidate_by_document(self, source_id: str, new_version: str) -> int:
        """Invalida entradas que dependem de uma versão antiga de um documento.

        Returns:
            Quantidade de entradas removidas.
        """
        before = len(self._entries)
        self._entries = [
            e
            for e in self._entries
            if source_id not in e.document_versions or e.document_versions[source_id] == new_version
        ]
        removed = before - len(self._entries)
        if removed:
            logger.info("cache_invalidated", source_id=source_id, removed=removed)
        return removed
