"""Rota de métricas do sistema (RF3.1).

GET /api/v1/metrics/summary — retorna métricas de uso:
- Total de perguntas feitas
- Total de respostas da IA
- Total de vezes que houve transbordo (escalação para revisão humana)
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import require_roles
from app.core.auth import UserContext
from app.core.models import UserRole

router = APIRouter(prefix="/metrics", tags=["metrics"])


@dataclass
class MetricsSummary:
    """Resumo de métricas do sistema."""

    total_questions: int
    total_answers: int
    total_escalations: int
    escalation_rate: float


class MetricsSummaryResponse(BaseModel):
    """Resposta de métricas."""

    total_questions: int
    total_answers: int
    total_escalations: int
    escalation_rate: float


# Armazenamento em memória (em produção, persistir em banco)
_metrics_store: dict[str, int] = {
    "total_questions": 0,
    "total_answers": 0,
    "total_escalations": 0,
}


def record_question() -> None:
    """Registra uma nova pergunta."""
    _metrics_store["total_questions"] += 1


def record_answer() -> None:
    """Registra uma nova resposta da IA."""
    _metrics_store["total_answers"] += 1


def record_escalation() -> None:
    """Registra uma escalação/transbordo."""
    _metrics_store["total_escalations"] += 1


def get_summary() -> MetricsSummary:
    """Retorna o resumo das métricas."""
    questions = _metrics_store["total_questions"]
    answers = _metrics_store["total_answers"]
    escalations = _metrics_store["total_escalations"]
    rate = escalations / answers if answers > 0 else 0.0
    return MetricsSummary(
        total_questions=questions,
        total_answers=answers,
        total_escalations=escalations,
        escalation_rate=round(rate, 4),
    )


@router.get("/summary", response_model=MetricsSummaryResponse)
def metrics_summary(
    user: UserContext = Depends(require_roles(UserRole.RH, UserRole.ADMIN)),
) -> MetricsSummaryResponse:
    """Retorna o resumo de métricas (RH e Admin)."""
    summary = get_summary()
    return MetricsSummaryResponse(
        total_questions=summary.total_questions,
        total_answers=summary.total_answers,
        total_escalations=summary.total_escalations,
        escalation_rate=summary.escalation_rate,
    )