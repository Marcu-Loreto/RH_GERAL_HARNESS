"""Construção e registro de traces de interação (RF1.9).

Monta o modelo ``Trace`` (DATA_MODEL_AND_METADATA §5) e o registra via logging
estruturado, garantindo rastreabilidade de pergunta, documentos, tokens,
latência, guardrails e confiança.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.logging import get_logger
from app.core.models import Answer, Trace
from app.observability.sinks import get_trace_sink

logger = get_logger(__name__)


def estimate_tokens(text: str) -> int:
    """Estimativa simples de tokens (aprox. palavras) para observabilidade."""
    return len(text.split())


def record_trace(trace: Trace) -> Trace:
    """Registra o trace via sink de observabilidade plugável e o retorna."""
    get_trace_sink().record(trace)
    return trace


def build_answer_trace(
    *,
    trace_id: str,
    session_id: str,
    user_id: str | None,
    original_query: str,
    canonical_query: str,
    domain: str | None,
    agent: str,
    model: str,
    answer: Answer,
    retrieved_chunk_ids: list[str],
    guardrails_triggered: list[str],
    latency_ms: float,
    channel: str | None = None,
    estimated_cost: float = 0.0,
    output_tokens: int | None = None,
    routing_confidence: float | None = None,
    routing_reason: str | None = None,
    agents_invoked: list[str] | None = None,
    model_tier: str | None = None,
    cache_hit: bool = False,
    prompt_version: str | None = None,
    escalation_reason: str | None = None,
    cache_bypass_reason: str | None = None,
    budget_status: str | None = None,
    budget_action: str | None = None,
    screening_decision: str | None = None,
) -> Trace:
    """Constrói um ``Trace`` a partir do resultado do pipeline."""
    return Trace(
        trace_id=trace_id,
        session_id=session_id,
        user_id=user_id,
        channel=channel,
        original_query=original_query,
        canonical_query=canonical_query,
        domain=domain,
        agent=agent,
        model=model,
        input_tokens=estimate_tokens(original_query),
        output_tokens=(
            output_tokens if output_tokens is not None else estimate_tokens(answer.answer)
        ),
        estimated_cost=estimated_cost,
        latency_ms=latency_ms,
        retrieved_chunks=retrieved_chunk_ids,
        guardrails_triggered=guardrails_triggered,
        final_confidence=answer.confidence,
        requires_human_review=answer.requires_human_review,
        created_at=datetime.now(UTC),
        routing_confidence=routing_confidence,
        routing_reason=routing_reason,
        agents_invoked=agents_invoked or [],
        model_tier=model_tier,
        cache_hit=cache_hit,
        prompt_version=prompt_version,
        escalation_reason=escalation_reason,
        cache_bypass_reason=cache_bypass_reason,
        budget_status=budget_status,
        budget_action=budget_action,
        screening_decision=screening_decision,
    )
