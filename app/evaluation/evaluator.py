"""Avaliador do golden dataset (EVALUATION_HARNESS §2, §5 + SPEC Fase 3 §6).

Executa o pipeline RAG sobre os itens do golden dataset e calcula:
  - qualidade de retrieval: precision@k, recall de fonte esperada;
  - comportamento: acurácia de comportamento, checagens de conteúdo;
  - resposta: faithfulness, citation accuracy;
  - eficiência (Fase 3): custo médio, tokens médios, latência P95, taxa de
    fallback e taxa de revisão humana.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.logging import get_logger
from app.core.models import UserRole
from app.evaluation.golden import GoldenItem
from app.rag.pipeline import RagPipeline, RagResponse

logger = get_logger(__name__)


def classify_behavior(response: RagResponse) -> str:
    """Deriva o comportamento observado a partir da resposta do pipeline."""
    if response.blocked:
        return "refuse"
    if not response.answer.evidence or response.answer.requires_human_review:
        return "human_review"
    return "answer"


def _percentile(values: list[float], pct: float) -> float:
    """Percentil (interpolação linear) de uma lista de valores."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = pct / 100.0 * (len(ordered) - 1)
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    frac = rank - low
    return ordered[low] + (ordered[high] - ordered[low]) * frac


@dataclass
class ItemResult:
    """Resultado da avaliação de um único item."""

    id: str
    behavior_ok: bool
    precision_at_k: float
    source_hit: bool
    content_ok: bool
    citation_ok: bool
    faithful: bool
    human_review: bool
    fallback: bool
    cost: float
    tokens: int
    latency_ms: float
    guardrail_blocked: bool = False

    @property
    def passed(self) -> bool:
        return self.behavior_ok and self.content_ok


@dataclass
class EvaluationReport:
    """Relatório agregado da avaliação (EVALUATION_HARNESS §6 + Fase 3 §6)."""

    total: int
    behavior_accuracy: float
    avg_precision_at_k: float
    source_recall: float
    content_pass_rate: float
    citation_accuracy: float
    faithfulness: float
    avg_cost_per_answer: float
    avg_tokens_per_answer: float
    latency_p95_ms: float
    fallback_rate: float
    human_review_rate: float
    guardrail_block_rate: float = 0.0
    items: list[ItemResult] = field(default_factory=list)

    def meets_thresholds(self, *, min_precision: float = 0.85, min_behavior: float = 0.90) -> bool:
        """Verifica os limiares mínimos sugeridos (EVALUATION_HARNESS §5)."""
        return self.avg_precision_at_k >= min_precision and self.behavior_accuracy >= min_behavior


def _evaluate_item(pipeline: RagPipeline, item: GoldenItem) -> ItemResult:
    response = pipeline.run(item.question, role=UserRole.COLABORADOR, area_rh=item.expected_domain)
    answer_text = response.answer.answer.lower()

    behavior_ok = classify_behavior(response) == item.expected_behavior

    retrieved_sources = [e.source_id for e in response.answer.evidence]
    if item.expected_sources:
        hits = sum(1 for s in retrieved_sources if s in item.expected_sources)
        precision = hits / len(retrieved_sources) if retrieved_sources else 0.0
        source_hit = any(s in item.expected_sources for s in retrieved_sources)
        # Citation accuracy: nenhuma fonte citada fora do conjunto esperado.
        citation_ok = bool(retrieved_sources) and all(
            s in item.expected_sources for s in retrieved_sources
        )
    else:
        precision = 1.0
        source_hit = True
        citation_ok = True

    content_ok = all(t.lower() in answer_text for t in item.must_include) and all(
        t.lower() not in answer_text for t in item.must_not_include
    )

    # Faithfulness (extrativo): respostas afirmativas devem ter evidência citada.
    if item.expected_behavior == "answer":
        faithful = bool(response.answer.evidence)
    else:
        faithful = not response.answer.evidence

    fallback = "fallback" in (response.trace.routing_reason or "")

    return ItemResult(
        id=item.id,
        behavior_ok=behavior_ok,
        precision_at_k=precision,
        source_hit=source_hit,
        content_ok=content_ok,
        citation_ok=citation_ok,
        faithful=faithful,
        human_review=response.answer.requires_human_review,
        fallback=fallback,
        cost=response.estimated_cost,
        tokens=response.trace.input_tokens + response.trace.output_tokens,
        latency_ms=response.trace.latency_ms,
        guardrail_blocked=response.blocked or bool(response.guardrails_triggered),
    )


def evaluate(pipeline: RagPipeline, golden: list[GoldenItem]) -> EvaluationReport:
    """Avalia o pipeline sobre o golden dataset e retorna o relatório agregado."""
    results = [_evaluate_item(pipeline, item) for item in golden]
    total = len(results)

    answerable = [r for r, g in zip(results, golden, strict=True) if g.expected_sources]
    avg_precision = (
        sum(r.precision_at_k for r in answerable) / len(answerable) if answerable else 1.0
    )
    citation_accuracy = (
        sum(r.citation_ok for r in answerable) / len(answerable) if answerable else 1.0
    )
    report = EvaluationReport(
        total=total,
        behavior_accuracy=sum(r.behavior_ok for r in results) / total if total else 0.0,
        avg_precision_at_k=avg_precision,
        source_recall=(
            sum(r.source_hit for r in answerable) / len(answerable) if answerable else 1.0
        ),
        content_pass_rate=sum(r.content_ok for r in results) / total if total else 0.0,
        citation_accuracy=citation_accuracy,
        faithfulness=sum(r.faithful for r in results) / total if total else 0.0,
        avg_cost_per_answer=sum(r.cost for r in results) / total if total else 0.0,
        avg_tokens_per_answer=sum(r.tokens for r in results) / total if total else 0.0,
        latency_p95_ms=_percentile([r.latency_ms for r in results], 95.0),
        fallback_rate=sum(r.fallback for r in results) / total if total else 0.0,
        human_review_rate=sum(r.human_review for r in results) / total if total else 0.0,
        guardrail_block_rate=sum(r.guardrail_blocked for r in results) / total if total else 0.0,
        items=results,
    )
    logger.info(
        "evaluation_completed",
        total=report.total,
        behavior_accuracy=round(report.behavior_accuracy, 3),
        avg_precision_at_k=round(report.avg_precision_at_k, 3),
        citation_accuracy=round(report.citation_accuracy, 3),
        faithfulness=round(report.faithfulness, 3),
        avg_cost_per_answer=round(report.avg_cost_per_answer, 6),
        latency_p95_ms=round(report.latency_p95_ms, 2),
        fallback_rate=round(report.fallback_rate, 3),
        human_review_rate=round(report.human_review_rate, 3),
        guardrail_block_rate=round(report.guardrail_block_rate, 3),
    )
    return report
