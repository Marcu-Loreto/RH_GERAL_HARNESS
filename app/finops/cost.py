"""Cálculo de custo e rastreamento FinOps (RF3.1 / RF3.5).

``estimate_cost`` calcula o custo estimado de uma chamada a partir do modelo e
dos tokens de entrada/saída. ``FinOpsTracker`` agrega custos por agente, modelo
e canal para alimentar o relatório de custo (dashboard FinOps).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from app.core.logging import get_logger
from app.core.model_router import BudgetStatus, ModelSpec

logger = get_logger(__name__)


def classify_budget(
    estimated_cost: float, budget: float, *, near_ratio: float = 0.8
) -> BudgetStatus:
    """Classifica a situação do orçamento a partir do custo estimado (RF3.5).

    Args:
        estimated_cost: Custo estimado (USD) da chamada considerada.
        budget: Orçamento máximo de custo por resposta.
        near_ratio: Fração do orçamento a partir da qual ele é considerado
            "próximo do limite".

    Returns:
        ``EXCEEDED`` quando o custo ultrapassa o orçamento; ``NEAR_LIMIT`` quando
        atinge ``near_ratio`` do orçamento; caso contrário ``NORMAL``.
    """
    if budget <= 0:
        return BudgetStatus.NORMAL
    if estimated_cost > budget:
        return BudgetStatus.EXCEEDED
    if estimated_cost >= budget * near_ratio:
        return BudgetStatus.NEAR_LIMIT
    return BudgetStatus.NORMAL


def estimate_cost(model: ModelSpec, input_tokens: int, output_tokens: int) -> float:
    """Estima o custo (USD) de uma chamada de modelo.

    Args:
        model: Especificação do modelo (com custos por 1k tokens).
        input_tokens: Tokens de entrada (não negativo).
        output_tokens: Tokens de saída (não negativo).

    Raises:
        ValueError: Se algum contador de tokens for negativo.
    """
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("Contagem de tokens não pode ser negativa.")
    cost = (input_tokens / 1000.0) * model.input_cost_per_1k + (
        output_tokens / 1000.0
    ) * model.output_cost_per_1k
    return round(cost, 8)


@dataclass
class CostRecord:
    """Registro de custo de uma única interação."""

    trace_id: str
    agent: str
    model: str
    channel: str
    input_tokens: int
    output_tokens: int
    cost: float


@dataclass
class FinOpsSummary:
    """Resumo agregado de custo para o relatório FinOps."""

    total_cost: float
    total_tokens: int
    answer_count: int
    avg_cost_per_answer: float
    cost_by_agent: dict[str, float] = field(default_factory=dict)
    cost_by_model: dict[str, float] = field(default_factory=dict)
    cost_by_channel: dict[str, float] = field(default_factory=dict)


class FinOpsTracker:
    """Acumula registros de custo e produz agregações (RF3.5)."""

    def __init__(self) -> None:
        self._records: list[CostRecord] = []

    def record(self, record: CostRecord) -> None:
        """Registra o custo de uma interação."""
        self._records.append(record)
        logger.info(
            "finops_record",
            trace_id=record.trace_id,
            agent=record.agent,
            model=record.model,
            channel=record.channel,
            cost=record.cost,
        )

    def clear(self) -> None:
        """Limpa os registros acumulados (útil em testes)."""
        self._records.clear()

    def __len__(self) -> int:
        return len(self._records)

    def summary(self) -> FinOpsSummary:
        """Agrega os custos por agente, modelo e canal."""
        total_cost = round(sum(r.cost for r in self._records), 8)
        total_tokens = sum(r.input_tokens + r.output_tokens for r in self._records)
        count = len(self._records)

        by_agent: dict[str, float] = defaultdict(float)
        by_model: dict[str, float] = defaultdict(float)
        by_channel: dict[str, float] = defaultdict(float)
        for r in self._records:
            by_agent[r.agent] += r.cost
            by_model[r.model] += r.cost
            by_channel[r.channel] += r.cost

        return FinOpsSummary(
            total_cost=total_cost,
            total_tokens=total_tokens,
            answer_count=count,
            avg_cost_per_answer=round(total_cost / count, 8) if count else 0.0,
            cost_by_agent={k: round(v, 8) for k, v in by_agent.items()},
            cost_by_model={k: round(v, 8) for k, v in by_model.items()},
            cost_by_channel={k: round(v, 8) for k, v in by_channel.items()},
        )
