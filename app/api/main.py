"""Aplicação FastAPI — ponto de entrada (RF0.1).

Configura logging estruturado, registra o middleware de trace e monta as rotas
versionadas sob o prefixo ``/api/v1``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.middleware import TraceContextMiddleware
from app.api.routes import ask, documents, finops, health, metrics
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Ciclo de vida da aplicação: inicializa logging e registra start/stop."""
    configure_logging()
    logger = get_logger(__name__)
    settings = get_settings()
    logger.info("application_startup", app_name=settings.app_name, env=settings.environment)
    yield
    logger.info("application_shutdown", app_name=settings.app_name)


def create_app() -> FastAPI:
    """Factory que constrói e configura a instância FastAPI."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Harness de IA para RAG multiagente de RH — Fase 0",
        lifespan=lifespan,
    )
    app.add_middleware(TraceContextMiddleware)
    app.include_router(health.router, prefix=settings.api_v1_prefix)
    app.include_router(documents.router, prefix=settings.api_v1_prefix)
    app.include_router(ask.router, prefix=settings.api_v1_prefix)
    app.include_router(finops.router, prefix=settings.api_v1_prefix)
    app.include_router(metrics.router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
