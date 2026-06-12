"""Rota de relatório FinOps (RF3.5).

GET /api/v1/finops/summary — retorna o custo agregado por agente, modelo e canal,
além de custo médio e total de tokens (dashboard de custo).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import get_finops_tracker, require_roles
from app.core.auth import UserContext
from app.core.models import UserRole
from app.finops.cost import FinOpsTracker

router = APIRouter(prefix="/finops", tags=["finops"])


class FinOpsSummaryResponse(BaseModel):
    """Resumo agregado de custo de inferência."""

    total_cost: float
    total_tokens: int
    answer_count: int
    avg_cost_per_answer: float
    cost_by_agent: dict[str, float]
    cost_by_model: dict[str, float]
    cost_by_channel: dict[str, float]


@router.get("/summary", response_model=FinOpsSummaryResponse)
def finops_summary(
    tracker: FinOpsTracker = Depends(get_finops_tracker),
    user: UserContext = Depends(require_roles(UserRole.ADMIN)),
) -> FinOpsSummaryResponse:
    """Retorna o relatório de custo agregado (somente Admin)."""
    summary = tracker.summary()
    return FinOpsSummaryResponse(
        total_cost=summary.total_cost,
        total_tokens=summary.total_tokens,
        answer_count=summary.answer_count,
        avg_cost_per_answer=summary.avg_cost_per_answer,
        cost_by_agent=summary.cost_by_agent,
        cost_by_model=summary.cost_by_model,
        cost_by_channel=summary.cost_by_channel,
    )
