"""Rota de ingestão documental (RF1.1).

POST /api/v1/documents — ingere um documento aprovado (metadados + texto bruto)
na base de conhecimento, validando governança antes da indexação.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_ingestion_service, require_roles
from app.core.auth import UserContext
from app.core.logging import get_logger
from app.core.models import DocumentMetadata, UserRole
from app.core.tracing import get_trace_id
from app.ingestion.service import IngestionError, IngestionService

router = APIRouter(prefix="/documents", tags=["documents"])
logger = get_logger(__name__)


class IngestRequest(BaseModel):
    """Payload de ingestão: metadados do documento + texto bruto."""

    document: DocumentMetadata
    raw_text: str = Field(min_length=1)


class IngestResponse(BaseModel):
    """Resposta da ingestão."""

    source_id: str
    chunks_indexed: int
    trace_id: str | None = None


@router.post("", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_document(
    payload: IngestRequest,
    service: IngestionService = Depends(get_ingestion_service),
    user: UserContext = Depends(require_roles(UserRole.RH, UserRole.ADMIN)),
) -> IngestResponse:
    """Ingere um documento aprovado na base de conhecimento (RH/Admin)."""
    try:
        result = service.ingest(payload.document, payload.raw_text)
    except IngestionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return IngestResponse(
        source_id=result.source_id,
        chunks_indexed=result.chunks_indexed,
        trace_id=get_trace_id(),
    )
