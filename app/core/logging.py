"""Configuração de logging estruturado com structlog (RF0.3).

Cada evento de log é enriquecido automaticamente com ``trace_id`` e
``session_id`` do contexto da requisição. Logs nunca devem conter dados
sensíveis (PII, segredos) — essa é uma regra de revisão obrigatória.

Uso:
    from app.core.logging import configure_logging, get_logger

    configure_logging()
    logger = get_logger(__name__)
    logger.info("event_name", key="value")
"""

from __future__ import annotations

import logging
from collections.abc import MutableMapping
from typing import Any

import structlog

from app.core.config import get_settings
from app.core.tracing import get_session_id, get_trace_id


def _add_trace_context(
    _logger: Any, _method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Processador structlog que injeta ``trace_id``/``session_id`` no log."""
    trace_id = get_trace_id()
    session_id = get_session_id()
    if trace_id is not None:
        event_dict.setdefault("trace_id", trace_id)
    if session_id is not None:
        event_dict.setdefault("session_id", session_id)
    return event_dict


def configure_logging() -> None:
    """Configura o structlog conforme as ``Settings`` (nível e formato)."""
    settings = get_settings()
    log_level = getattr(logging, settings.log_level, logging.INFO)

    logging.basicConfig(format="%(message)s", level=log_level)

    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer()
        if settings.log_json
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _add_trace_context,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Retorna um logger estruturado vinculado ao nome do módulo."""
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger
