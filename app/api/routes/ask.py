"""Rota de consulta RAG (RF1.4 → RF1.9).

POST /api/v1/ask — recebe uma pergunta, executa o pipeline RAG completo e devolve
a resposta com evidências, confiança, limitações e identificadores de trace.

Segurança: o perfil (``role``) vem **exclusivamente** do ``UserContext``
autenticado (cabeçalho controlado), nunca do corpo da requisição.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.agents.query_intelligence import KNOWN_AREAS, is_known_area
from app.api.dependencies import get_current_user, get_pipeline
from app.api.routes.metrics import record_answer, record_escalation, record_question
from app.core.auth import UserContext
from app.core.models import Answer
from app.rag.pipeline import RagPipeline

router = APIRouter(prefix="/ask", tags=["ask"])


class AskRequest(BaseModel):
    """Payload de consulta do usuário (sem perfil: o perfil vem do contexto auth)."""

    query: str = Field(min_length=1)
    area_rh: str | None = None


class AskResponse(BaseModel):
    """Resposta da consulta, com evidências e metadados de rastreamento."""

    answer: Answer
    blocked: bool
    guardrails_triggered: list[str]
    trace_id: str
    confidence: str
    requires_human_review: bool
    agent: str | None = None
    domain: str | None = None
    screening_decision: str | None = None
    escalation_reason: str | None = None


@router.post("", response_model=AskResponse)
def ask(
    payload: AskRequest,
    pipeline: RagPipeline = Depends(get_pipeline),
    user: UserContext = Depends(get_current_user),
) -> AskResponse:
    """Responde a uma pergunta de RH com base em documentos oficiais."""
    # Registra a pergunta
    record_question()

    if payload.area_rh is not None and not is_known_area(payload.area_rh):
        # Domínio inexistente: erro controlado, sem stacktrace cru (RF2.4).
        raise HTTPException(
            status_code=422,
            detail=(
                f"Área de RH desconhecida: '{payload.area_rh}'. "
                f"Áreas válidas: {sorted(KNOWN_AREAS)}."
            ),
        )
    result = pipeline.run(
        payload.query,
        role=user.role,
        area_rh=payload.area_rh,
        user_id=user.user_id,
    )

    # Registra a resposta
    record_answer()

    # Registra escalação se houver
    if result.answer.requires_human_review:
        record_escalation()

    return AskResponse(
        answer=result.answer,
        blocked=result.blocked,
        guardrails_triggered=result.guardrails_triggered,
        trace_id=result.trace.trace_id,
        confidence=str(result.answer.confidence),
        requires_human_review=result.answer.requires_human_review,
        agent=result.agent,
        domain=result.domain,
        screening_decision=result.answer.screening_decision,
        escalation_reason=result.answer.escalation_reason,
    )
