"""Serviço de ingestão documental (RF1.1 → RF1.3).

Orquestra: validação de metadados → governança (só documentos aprovados e com
campos obrigatórios) → chunking → embedding → indexação no vector store.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

from app.core.logging import get_logger
from app.core.models import ChunkMetadata, DocumentMetadata
from app.ingestion.chunker import chunk_text
from app.observability.sinks import TraceSink, get_trace_sink
from app.retrieval.embeddings import EmbeddingProvider, get_embedding_provider
from app.retrieval.vector_store import InMemoryVectorStore, StoredChunk

logger = get_logger(__name__)


class IngestionError(ValueError):
    """Erro de ingestão (documento não aprovado ou metadados incompletos)."""


@dataclass
class IngestionResult:
    """Resultado de uma ingestão bem-sucedida."""

    source_id: str
    chunks_indexed: int
    reindexed: bool = False
    previous_version: str | None = None
    cache_entries_invalidated: int = 0


class CacheInvalidator(Protocol):
    """Contrato mínimo de invalidação de cache por documento (RF3.4)."""

    def invalidate_by_document(self, source_id: str, new_version: str) -> int:
        """Invalida entradas de cache de uma versão antiga do documento."""
        ...


class IngestionService:
    """Ingere documentos aprovados na base de conhecimento."""

    def __init__(
        self,
        store: InMemoryVectorStore,
        embedder: EmbeddingProvider | None = None,
        *,
        max_chars: int,
        overlap_chars: int,
        cache: CacheInvalidator | None = None,
        sink: TraceSink | None = None,
    ) -> None:
        self._store = store
        self._embedder = embedder or get_embedding_provider()
        self._max_chars = max_chars
        self._overlap_chars = overlap_chars
        self._cache = cache
        self._sink = sink or get_trace_sink()

    def ingest(self, document: DocumentMetadata, raw_text: str) -> IngestionResult:
        """Valida, divide, vetoriza e indexa um documento.

        Quando o documento já está indexado (reingestão/atualização), os chunks
        da versão anterior são removidos e o cache semântico relacionado é
        invalidado, garantindo que respostas baseadas na versão antiga não sejam
        reutilizadas (RF1.1 / RF3.4).

        Raises:
            IngestionError: Se o documento não for indexável (governança RF0.4)
                ou o texto estiver vazio.
        """
        if not document.is_indexable():
            logger.warning(
                "ingestion_rejected",
                source_id=document.source_id,
                status=document.status,
                reason="documento_nao_indexavel",
            )
            raise IngestionError(
                "Documento não pode ser indexado: precisa estar 'approved' e ter "
                "todos os campos obrigatórios de metadados."
            )
        if not raw_text or not raw_text.strip():
            raise IngestionError("Texto do documento está vazio.")

        # Detecta reingestão/atualização: já há chunks indexados deste documento.
        previous_version = self._store.version_of(document.source_id)
        reindexed = previous_version is not None
        if reindexed:
            self._store.remove_by_source(document.source_id)

        chunks = chunk_text(
            raw_text,
            max_chars=self._max_chars,
            overlap_chars=self._overlap_chars,
        )
        stored: list[StoredChunk] = []
        for chunk in chunks:
            metadata = ChunkMetadata(
                chunk_id=f"{document.source_id}::chunk-{chunk.index}",
                source_id=document.source_id,
                title=document.title,
                section=chunk.section,
                text=chunk.text,
                token_count=len(chunk.text.split()),
                embedding_model=self._embedder.name,
                area_rh=document.area_rh,
                document_type=document.document_type,
                version=document.version,
                valid_from=document.valid_from,
                valid_until=document.valid_until,
                confidentiality=document.confidentiality,
                status=document.status,
                hash=hashlib.sha256(chunk.text.encode()).hexdigest(),
            )
            vector = self._embedder.embed(chunk.text)
            stored.append(StoredChunk(chunk=metadata, vector=vector))

        self._store.add(stored)

        # Invalida o cache semântico relacionado ao documento atualizado para que
        # nenhuma resposta baseada na versão antiga continue sendo reutilizada.
        invalidated = 0
        if reindexed and self._cache is not None:
            invalidated = self._cache.invalidate_by_document(document.source_id, document.version)
            self._sink.event(
                "cache_invalidated_on_reingestion",
                source_id=document.source_id,
                previous_version=previous_version,
                new_version=document.version,
                cache_entries_invalidated=invalidated,
            )
            logger.info(
                "document_reingested",
                source_id=document.source_id,
                previous_version=previous_version,
                new_version=document.version,
                cache_entries_invalidated=invalidated,
            )

        logger.info(
            "ingestion_completed",
            source_id=document.source_id,
            chunks_indexed=len(stored),
            embedding_model=self._embedder.name,
            reindexed=reindexed,
        )
        return IngestionResult(
            source_id=document.source_id,
            chunks_indexed=len(stored),
            reindexed=reindexed,
            previous_version=previous_version,
            cache_entries_invalidated=invalidated,
        )
