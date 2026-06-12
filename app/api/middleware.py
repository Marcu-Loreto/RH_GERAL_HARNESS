"""Middleware de rastreamento de requisições (RF0.3).

Para cada requisição HTTP, gera/propaga ``trace_id`` e ``session_id``, vincula-os
ao contexto de logging e os devolve em cabeçalhos de resposta, garantindo
rastreabilidade ponta a ponta.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger
from app.core.tracing import bind_trace_context

logger = get_logger(__name__)

TRACE_HEADER = "X-Trace-Id"
SESSION_HEADER = "X-Session-Id"


class TraceContextMiddleware(BaseHTTPMiddleware):
    """Injeta ``trace_id``/``session_id`` no contexto e registra a requisição."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        incoming_trace = request.headers.get(TRACE_HEADER)
        incoming_session = request.headers.get(SESSION_HEADER)
        trace_id, session_id = bind_trace_context(incoming_trace, incoming_session)

        start = time.perf_counter()
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
        )
        try:
            response = await call_next(request)
        except Exception:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                latency_ms=round(latency_ms, 2),
                exc_info=True,
            )
            raise

        latency_ms = (time.perf_counter() - start) * 1000
        response.headers[TRACE_HEADER] = trace_id
        response.headers[SESSION_HEADER] = session_id
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=round(latency_ms, 2),
        )
        return response
