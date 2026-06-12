"""Rastreamento de requisições via ``trace_id`` e ``session_id`` (RF0.3).

Usa ``contextvars`` para propagar os identificadores ao longo do ciclo de vida
de uma requisição, sem precisar passá-los explicitamente entre funções. O
logging estruturado lê esses valores para enriquecer cada evento de log.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

_trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
_session_id_var: ContextVar[str | None] = ContextVar("session_id", default=None)


def generate_trace_id() -> str:
    """Gera um novo ``trace_id`` único (UUID4 em formato hex)."""
    return uuid.uuid4().hex


def generate_session_id() -> str:
    """Gera um novo ``session_id`` único (UUID4 em formato hex)."""
    return uuid.uuid4().hex


def set_trace_id(trace_id: str) -> None:
    """Define o ``trace_id`` no contexto atual."""
    _trace_id_var.set(trace_id)


def set_session_id(session_id: str) -> None:
    """Define o ``session_id`` no contexto atual."""
    _session_id_var.set(session_id)


def get_trace_id() -> str | None:
    """Retorna o ``trace_id`` do contexto atual, se houver."""
    return _trace_id_var.get()


def get_session_id() -> str | None:
    """Retorna o ``session_id`` do contexto atual, se houver."""
    return _session_id_var.get()


def bind_trace_context(
    trace_id: str | None = None,
    session_id: str | None = None,
) -> tuple[str, str]:
    """Vincula ``trace_id``/``session_id`` ao contexto, gerando-os se ausentes.

    Returns:
        Tupla ``(trace_id, session_id)`` efetivamente vinculada ao contexto.
    """
    effective_trace = trace_id or generate_trace_id()
    effective_session = session_id or generate_session_id()
    set_trace_id(effective_trace)
    set_session_id(effective_session)
    return effective_trace, effective_session
