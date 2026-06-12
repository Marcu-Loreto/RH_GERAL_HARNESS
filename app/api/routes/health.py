"""Rotas de health check (RF0.5 / testes de integração).

Expõe verificação de liveness (a aplicação responde) e readiness (dependências,
como o banco de metadados, estão acessíveis).
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.tracing import get_trace_id
from app.infrastructure.database import health_check as db_health_check

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Resposta padrão de health check."""

    status: str
    environment: str
    trace_id: str | None = None


class ReadinessResponse(BaseModel):
    """Resposta de readiness, incluindo o estado das dependências."""

    status: str
    database: str
    trace_id: str | None = None


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness: confirma que a aplicação está no ar."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        trace_id=get_trace_id(),
    )


@router.get("/ready", response_model=ReadinessResponse)
def ready() -> ReadinessResponse:
    """Readiness: confirma que as dependências essenciais respondem."""
    db_ok = db_health_check()
    return ReadinessResponse(
        status="ok" if db_ok else "degraded",
        database="up" if db_ok else "down",
        trace_id=get_trace_id(),
    )
