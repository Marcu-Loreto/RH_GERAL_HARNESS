"""Testes unitários de geração e propagação de trace/session ID (RF0.3)."""

from __future__ import annotations

import pytest

from app.core import tracing


@pytest.mark.unit
def test_generate_trace_id_is_unique() -> None:
    ids = {tracing.generate_trace_id() for _ in range(100)}
    assert len(ids) == 100
    assert all(len(i) == 32 for i in ids)


@pytest.mark.unit
def test_generate_session_id_is_unique() -> None:
    ids = {tracing.generate_session_id() for _ in range(100)}
    assert len(ids) == 100


@pytest.mark.unit
def test_bind_generates_when_absent() -> None:
    trace_id, session_id = tracing.bind_trace_context()
    assert trace_id == tracing.get_trace_id()
    assert session_id == tracing.get_session_id()
    assert trace_id and session_id


@pytest.mark.unit
def test_bind_preserves_incoming_ids() -> None:
    trace_id, session_id = tracing.bind_trace_context("trace-abc", "session-xyz")
    assert trace_id == "trace-abc"
    assert session_id == "session-xyz"
    assert tracing.get_trace_id() == "trace-abc"
    assert tracing.get_session_id() == "session-xyz"
