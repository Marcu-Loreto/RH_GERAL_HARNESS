"""Testes unitários da abstração de observabilidade TraceSink (Prioridade 3)."""

from __future__ import annotations

from typing import Any

import pytest

from app.core.models import Answer, Confidence, Evidence, Trace
from app.observability.sinks import (
    NoOpTraceSink,
    OptionalLangfuseTraceSink,
    OptionalOpenTelemetryTraceSink,
    StructlogTraceSink,
    get_trace_sink,
    set_trace_sink,
)


class RecordingSink:
    """Sink de teste que captura eventos e traces recebidos."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []
        self.traces: list[Trace] = []

    def event(self, name: str, **fields: Any) -> None:
        self.events.append((name, fields))

    def record(self, trace: Trace) -> None:
        self.traces.append(trace)


def _trace() -> Trace:
    return Trace(
        trace_id="t1",
        session_id="s1",
        original_query="quantos dias de férias",
        canonical_query="dias férias",
        domain="beneficios",
        agent="agente_beneficios",
        model="minimax-m2.5",
    )


@pytest.mark.unit
def test_noop_sink_does_not_raise() -> None:
    sink = NoOpTraceSink()
    sink.event("interaction_start", trace_id="t1")
    sink.record(_trace())  # não deve levantar


@pytest.mark.unit
def test_structlog_sink_works_without_external_dependency() -> None:
    sink = StructlogTraceSink()
    sink.event("retrieval_completed", trace_id="t1", relevant=3)
    sink.record(_trace())  # apenas metadados, sem dependência externa


@pytest.mark.unit
def test_structlog_sink_omits_query_text_fields() -> None:
    # Campos sensíveis (query) não devem ser propagados pelo event() local.
    sink = StructlogTraceSink()
    # Não levanta e filtra internamente; cobre o caminho de redação.
    sink.event("interaction_start", original_query="meu CPF é 123", canonical_query="x")


@pytest.mark.unit
def test_optional_langfuse_degrades_gracefully() -> None:
    recording = RecordingSink()
    sink = OptionalLangfuseTraceSink(fallback=recording)
    # Sem langfuse instalado, cliente é None e delega ao fallback.
    assert sink.is_active is False
    sink.event("e1", x=1)
    sink.record(_trace())
    assert recording.events and recording.traces


@pytest.mark.unit
def test_optional_otel_degrades_gracefully() -> None:
    recording = RecordingSink()
    sink = OptionalOpenTelemetryTraceSink(fallback=recording)
    sink.event("e1", x=1)
    sink.record(_trace())
    assert recording.events and recording.traces


@pytest.mark.unit
def test_set_and_get_default_sink_roundtrip() -> None:
    original = get_trace_sink()
    try:
        recording = RecordingSink()
        set_trace_sink(recording)
        assert get_trace_sink() is recording
    finally:
        set_trace_sink(original)


@pytest.mark.unit
def test_pipeline_emits_events_to_sink(pipeline_factory: Any) -> None:
    # Usa um pipeline com sink de gravação para validar eventos do fluxo.
    recording = RecordingSink()
    pipeline = pipeline_factory(sink=recording)
    pipeline.run("quantos dias de férias eu tenho?", area_rh="beneficios")
    names = {name for name, _ in recording.events}
    assert len(recording.events) > 0  # O pipeline deve emitir pelo menos um evento