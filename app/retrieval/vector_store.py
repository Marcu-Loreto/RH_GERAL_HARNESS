"""Vector store em memória com filtros por metadados (RF1.3 / RF1.5).

Implementação mínima para o MVP: armazena chunks com seus vetores e faz busca por
similaridade do cosseno, aplicando filtros de metadados (área, status, vigência e
confidencialidade). Substituível por um Vector DB real (ex.: pgvector, Qdrant)
sem alterar a interface usada pelo retriever.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from app.core.logging import get_logger
from app.core.models import ChunkMetadata, Confidentiality, DocumentStatus
from app.retrieval.embeddings import cosine_similarity

logger = get_logger(__name__)


@dataclass
class StoredChunk:
    """Chunk indexado: metadados + vetor de embedding."""

    chunk: ChunkMetadata
    vector: list[float]


@dataclass
class RetrievalFilters:
    """Filtros aplicáveis na busca (todos opcionais)."""

    area_rh: str | None = None
    allowed_confidentiality: list[Confidentiality] = field(default_factory=list)
    reference_date: datetime | None = None
    only_approved: bool = True


@dataclass
class ScoredChunk:
    """Chunk recuperado com seu score de relevância."""

    chunk: ChunkMetadata
    score: float


class InMemoryVectorStore:
    """Armazenamento vetorial volátil para o MVP."""

    def __init__(self) -> None:
        self._items: list[StoredChunk] = []

    def add(self, items: Iterable[StoredChunk]) -> int:
        """Adiciona chunks ao índice. Retorna a quantidade inserida."""
        added = list(items)
        self._items.extend(added)
        logger.info("vector_store_add", count=len(added), total=len(self._items))
        return len(added)

    def clear(self) -> None:
        """Remove todos os chunks (útil em testes)."""
        self._items.clear()

    def remove_by_source(self, source_id: str) -> int:
        """Remove todos os chunks de um documento. Retorna a quantidade removida.

        Usado na reingestão/reindexação para que a versão antiga de um documento
        não permaneça indexada ao lado da nova (RF1.1 / RF3.4).
        """
        before = len(self._items)
        self._items = [item for item in self._items if item.chunk.source_id != source_id]
        removed = before - len(self._items)
        if removed:
            logger.info("vector_store_remove", source_id=source_id, removed=removed)
        return removed

    def has_source(self, source_id: str) -> bool:
        """Indica se já existem chunks indexados para um documento."""
        return any(item.chunk.source_id == source_id for item in self._items)

    def version_of(self, source_id: str) -> str | None:
        """Retorna a versão atualmente indexada de um documento, se houver."""
        for item in self._items:
            if item.chunk.source_id == source_id:
                return item.chunk.version
        return None

    def __len__(self) -> int:
        return len(self._items)

    def _passes_filters(self, chunk: ChunkMetadata, filters: RetrievalFilters) -> bool:
        if filters.only_approved and chunk.status != DocumentStatus.APPROVED:
            return False
        if filters.area_rh and chunk.area_rh != filters.area_rh:
            return False
        if filters.allowed_confidentiality:
            allowed = {c.value for c in filters.allowed_confidentiality}
            if chunk.confidentiality not in allowed:
                return False
        if filters.reference_date is not None:
            if chunk.valid_from and chunk.valid_from > filters.reference_date:
                return False
            if chunk.valid_until and chunk.valid_until < filters.reference_date:
                return False
        return True

    def search(
        self,
        query_vector: list[float],
        filters: RetrievalFilters,
        top_k: int,
    ) -> list[ScoredChunk]:
        """Retorna os ``top_k`` chunks mais similares que passam pelos filtros."""
        scored = [
            ScoredChunk(chunk=item.chunk, score=cosine_similarity(query_vector, item.vector))
            for item in self._items
            if self._passes_filters(item.chunk, filters)
        ]
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:top_k]
