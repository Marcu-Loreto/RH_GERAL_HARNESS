"""Recuperação híbrida com filtros por metadados (RF1.4 / RF1.5).

Combina similaridade densa (embeddings) com sobreposição lexical de tokens,
ponderadas por ``hybrid_dense_weight``. A busca sempre aplica os filtros de
governança (área, status aprovado, vigência e confidencialidade permitida).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings
from app.core.logging import get_logger
from app.retrieval.embeddings import EmbeddingProvider, get_embedding_provider, tokenize
from app.retrieval.vector_store import (
    InMemoryVectorStore,
    RetrievalFilters,
    ScoredChunk,
)

logger = get_logger(__name__)

# Stopwords PT-BR ignoradas no cálculo de cobertura lexical (reduz ruído).
_STOPWORDS: frozenset[str] = frozenset(
    "a o os as de do da dos das e que em no na nos nas para por com um uma "
    "ao aos pela pelo se eu meu minha tenho ter posso qual quais quanto quantos "
    "como onde quando meu sua seu eh é da na".split()
)


def lexical_overlap(query: str, text: str) -> float:
    """Cobertura dos termos de conteúdo da query presentes no texto.

    Ignora stopwords e tokens muito curtos. Métrica assimétrica (foco na query):
    ``|termos_da_query ∩ texto| / |termos_da_query|``.
    """
    query_tokens = {t for t in tokenize(query) if t not in _STOPWORDS and len(t) > 2}
    text_tokens = set(tokenize(text))
    if not query_tokens:
        return 0.0
    return len(query_tokens & text_tokens) / len(query_tokens)


@dataclass
class RetrievalResult:
    """Resultado da recuperação: chunks relevantes acima do limiar."""

    results: list[ScoredChunk]

    @property
    def has_evidence(self) -> bool:
        """Indica se há ao menos um chunk relevante recuperado."""
        return len(self.results) > 0


class Retriever:
    """Executa busca híbrida sobre o vector store."""

    def __init__(
        self,
        store: InMemoryVectorStore,
        embedder: EmbeddingProvider | None = None,
    ) -> None:
        self._store = store
        self._embedder = embedder or get_embedding_provider()

    def retrieve(self, query: str, filters: RetrievalFilters) -> RetrievalResult:
        """Recupera os chunks mais relevantes para ``query`` sob ``filters``."""
        settings = get_settings()
        top_k = settings.retrieval_top_k
        weight = settings.hybrid_dense_weight

        query_vector = self._embedder.embed(query)
        # Pool maior para reranking híbrido; depois cortamos para top_k.
        pool = self._store.search(query_vector, filters, top_k=top_k * 4)

        reranked: list[ScoredChunk] = []
        for item in pool:
            lexical = lexical_overlap(query, item.chunk.text)
            blended = weight * item.score + (1.0 - weight) * lexical
            reranked.append(ScoredChunk(chunk=item.chunk, score=blended))

        reranked.sort(key=lambda s: s.score, reverse=True)
        best = reranked[0].score if reranked else 0.0
        cutoff = max(settings.min_relevance_score, best * settings.relevance_ratio)
        relevant = [s for s in reranked if s.score >= cutoff][:top_k]

        logger.info(
            "retrieval_completed",
            candidates=len(pool),
            relevant=len(relevant),
            area_rh=filters.area_rh,
        )
        return RetrievalResult(results=relevant)
