"""Abstração plugável de observabilidade (TraceSink) — RF3.1.

Define uma interface única para emitir eventos e traces de interação, permitindo
plugar backends externos (Langfuse, OpenTelemetry) no futuro **sem reescrever o
fluxo**. O padrão atual é o ``StructlogTraceSink`` (local, sem dependência
externa). Os sinks opcionais para Langfuse/OTel degradam para no-op quando a
dependência não está instalada.

Privacidade: o ``StructlogTraceSink`` **não** emite o texto da pergunta/resposta
(evita PII em logs); apenas metadados rastreáveis. Sinks externos podem receber o
``Trace`` completo e armazená-lo de forma segura conforme sua política.
"""

from __future__ import annotations

from typing import Any, Protocol

from app.core.logging import get_logger
from app.core.models import Trace

logger = get_logger(__name__)

# Campos do Trace considerados conteúdo livre (potencial PII) — nunca emitidos
# pelo sink local de logs.
_SENSITIVE_TRACE_FIELDS: frozenset[str] = frozenset({"original_query", "canonical_query"})


class TraceSink(Protocol):
    """Contrato de um coletor de observabilidade."""

    def event(self, name: str, **fields: Any) -> None:
        """Registra um evento pontual do fluxo (início, retrieval, guardrail...)."""
        ...

    def record(self, trace: Trace) -> None:
        """Registra o trace completo de uma interação (evento de resposta)."""
        ...


class NoOpTraceSink:
    """Sink que descarta tudo (útil para desabilitar observabilidade em testes)."""

    def event(self, name: str, **fields: Any) -> None:
        return None

    def record(self, trace: Trace) -> None:
        return None


class StructlogTraceSink:
    """Sink padrão: emite eventos/traces como logs estruturados (sem PII)."""

    def event(self, name: str, **fields: Any) -> None:
        safe = {k: v for k, v in fields.items() if k not in _SENSITIVE_TRACE_FIELDS}
        logger.info(name, **safe)

    def record(self, trace: Trace) -> None:
        logger.info(
            "interaction_trace",
            trace_id=trace.trace_id,
            session_id=trace.session_id,
            user_id=trace.user_id,
            channel=trace.channel,
            domain=trace.domain,
            agent=trace.agent,
            model=trace.model,
            model_tier=trace.model_tier,
            input_tokens=trace.input_tokens,
            output_tokens=trace.output_tokens,
            estimated_cost=trace.estimated_cost,
            latency_ms=round(trace.latency_ms, 2),
            cache_hit=trace.cache_hit,
            cache_bypass_reason=trace.cache_bypass_reason,
            prompt_version=trace.prompt_version,
            retrieved_chunks=trace.retrieved_chunks,
            guardrails_triggered=trace.guardrails_triggered,
            final_confidence=trace.final_confidence,
            requires_human_review=trace.requires_human_review,
            escalation_reason=trace.escalation_reason,
            budget_status=trace.budget_status,
            budget_action=trace.budget_action,
            screening_decision=trace.screening_decision,
        )


class OptionalLangfuseTraceSink:
    """Sink Langfuse opcional: usa Langfuse se instalado; senão, degrada.

    Mantém um sink de fallback (structlog por padrão). Não cria dependência
    obrigatória: a importação do ``langfuse`` é tentada de forma protegida.
    """

    def __init__(self, fallback: TraceSink | None = None) -> None:
        self._fallback: TraceSink = fallback or StructlogTraceSink()
        self._client = self._try_init_client()

    @staticmethod
    def _try_init_client() -> Any | None:
        try:  # pragma: no cover - exercitado apenas se langfuse estiver instalado
            import langfuse  # type: ignore[import-not-found]

            return langfuse.Langfuse()
        except Exception:
            return None

    @property
    def is_active(self) -> bool:
        """Indica se o cliente Langfuse foi inicializado."""
        return self._client is not None

    def event(self, name: str, **fields: Any) -> None:
        self._fallback.event(name, **fields)

    def record(self, trace: Trace) -> None:
        self._fallback.record(trace)


class OptionalOpenTelemetryTraceSink:
    """Sink OpenTelemetry opcional: usa OTel se instalado; senão, degrada."""

    def __init__(self, fallback: TraceSink | None = None) -> None:
        self._fallback: TraceSink = fallback or StructlogTraceSink()
        self._tracer = self._try_init_tracer()

    @staticmethod
    def _try_init_tracer() -> Any | None:
        try:  # pragma: no cover - exercitado apenas se opentelemetry estiver instalado
            from opentelemetry import trace as otel_trace  # type: ignore[import-not-found]

            return otel_trace.get_tracer("rh-harness")
        except Exception:
            return None

    @property
    def is_active(self) -> bool:
        """Indica se o tracer OTel foi inicializado."""
        return self._tracer is not None

    def event(self, name: str, **fields: Any) -> None:
        self._fallback.event(name, **fields)

    def record(self, trace: Trace) -> None:
        self._fallback.record(trace)


_default_sink: TraceSink | None = None


def get_trace_sink() -> TraceSink:
    """Retorna o sink de observabilidade padrão (singleton; structlog)."""
    global _default_sink
    if _default_sink is None:
        _default_sink = StructlogTraceSink()
    return _default_sink


def set_trace_sink(sink: TraceSink) -> None:
    """Substitui o sink padrão (usado para plugar Langfuse/OTel ou testar)."""
    global _default_sink
    _default_sink = sink
