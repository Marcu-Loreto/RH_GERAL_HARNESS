"""Model Router — seleção de modelo por risco, confiança e custo (RF3.3).

Implementa as regras de roteamento da SPEC Fase 3 §4 de forma determinística e
sem dependência de provedor externo. Cada modelo possui um tier e um custo por
1k tokens (entrada/saída) usados pelo FinOps. A decisão é sempre explicável e
possui fallback quando o modelo preferido está indisponível.

Qualquer alteração nas regras/custos exige teste de regressão (TEST_STRATEGY).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.agents.query_intelligence import RiskLevel
from app.core.logging import get_logger

logger = get_logger(__name__)


class ModelTier(StrEnum):
    """Níveis de capacidade/custo dos modelos disponíveis."""

    ECONOMICO = "economico"
    INTERMEDIARIO = "intermediario"
    ROBUSTO = "robusto"


class BudgetStatus(StrEnum):
    """Situação do orçamento de custo para a interação (RF3.5)."""

    NORMAL = "normal"
    NEAR_LIMIT = "near_limit"
    EXCEEDED = "exceeded"


@dataclass(frozen=True)
class ModelSpec:
    """Especificação de um modelo: tier, custos, latência e disponibilidade."""

    name: str
    tier: ModelTier
    input_cost_per_1k: float
    output_cost_per_1k: float
    available: bool = True
    # Latência média esperada (ms) — usada como critério de roteamento (RF3.3).
    avg_latency_ms: float = 0.0


# Catálogo de modelos do MVP. Custos aproximados (USD por 1k tokens); valores de
# referência, sem segredo. Ordenados por capacidade crescente. A latência média
# cresce com a capacidade do modelo (econômico = mais rápido).
_MODEL_CATALOG: dict[ModelTier, ModelSpec] = {
    ModelTier.ECONOMICO: ModelSpec(
        name="minimax-m2.5",
        tier=ModelTier.ECONOMICO,
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
        avg_latency_ms=400.0,
    ),
    ModelTier.INTERMEDIARIO: ModelSpec(
        name="gpt-4o-mini",
        tier=ModelTier.INTERMEDIARIO,
        input_cost_per_1k=0.00015,
        output_cost_per_1k=0.0006,
        avg_latency_ms=900.0,
    ),
    ModelTier.ROBUSTO: ModelSpec(
        name="gpt-4o",
        tier=ModelTier.ROBUSTO,
        input_cost_per_1k=0.0025,
        output_cost_per_1k=0.01,
        avg_latency_ms=2200.0,
    ),
}

# Ordem de preferência para fallback (mais robusto → mais econômico).
_FALLBACK_ORDER: tuple[ModelTier, ...] = (
    ModelTier.ROBUSTO,
    ModelTier.INTERMEDIARIO,
    ModelTier.ECONOMICO,
)


@dataclass
class RoutingDecision:
    """Resultado da seleção de modelo (explicável e rastreável)."""

    model: ModelSpec
    requested_tier: ModelTier
    reason: str
    requires_human_review: bool = False
    fallback_used: bool = False
    budget_status: BudgetStatus = BudgetStatus.NORMAL
    estimated_cost: float = 0.0
    expected_latency_ms: float = 0.0


def get_model(tier: ModelTier) -> ModelSpec:
    """Retorna a especificação do modelo de um tier."""
    return _MODEL_CATALOG[tier]


def _estimate_cost(model: ModelSpec, input_tokens: int, output_tokens: int) -> float:
    """Estimativa de custo (USD) sem dependência de FinOps (evita import circular)."""
    cost = (input_tokens / 1000.0) * model.input_cost_per_1k + (
        output_tokens / 1000.0
    ) * model.output_cost_per_1k
    return round(cost, 8)


def _tier_for(risk: RiskLevel, low_confidence: bool) -> tuple[ModelTier, bool, str]:
    """Mapeia risco/confiança para tier, sinalizando revisão humana (§4)."""
    if low_confidence:
        return ModelTier.ROBUSTO, True, "baixa confiança: modelo robusto + revisão humana"
    if risk == RiskLevel.ALTO:
        return ModelTier.ROBUSTO, False, "alto risco: modelo robusto"
    if risk == RiskLevel.MEDIO:
        return ModelTier.INTERMEDIARIO, False, "risco médio: modelo intermediário"
    return ModelTier.ECONOMICO, False, "pergunta simples e baixo risco: modelo econômico"


def _resolve_available(
    preferred: ModelTier, catalog: dict[ModelTier, ModelSpec]
) -> tuple[ModelSpec, bool]:
    """Resolve o modelo preferido ou o melhor fallback disponível."""
    preferred_model = catalog[preferred]
    if preferred_model.available:
        return preferred_model, False
    for tier in _FALLBACK_ORDER:
        candidate = catalog[tier]
        if candidate.available:
            return candidate, True
    # Nenhum disponível: retorna o preferido mesmo indisponível (caller trata erro).
    return preferred_model, True


def select_model(
    risk: RiskLevel,
    confidence: float,
    *,
    strategy: str = "auto",
    min_confidence: float = 0.34,
    catalog: dict[ModelTier, ModelSpec] | None = None,
    budget_status: BudgetStatus = BudgetStatus.NORMAL,
    estimated_input_tokens: int = 0,
    estimated_output_tokens: int = 0,
) -> RoutingDecision:
    """Seleciona o modelo conforme risco, confiança, custo, latência e orçamento.

    Args:
        risk: Nível de risco da pergunta.
        confidence: Confiança de classificação/roteamento (0..1).
        strategy: ``auto`` aplica as regras §4; valor de tier força o tier.
        min_confidence: Limiar abaixo do qual a confiança é considerada baixa.
        catalog: Catálogo de modelos (injetável para testes de fallback).
        budget_status: Situação do orçamento; quando ``EXCEEDED`` força o modelo
            econômico (e mantém revisão humana se o risco for alto), quando
            ``NEAR_LIMIT`` rebaixa o tier preferido em um nível para conter custo.
        estimated_input_tokens: Tokens de entrada estimados (para custo).
        estimated_output_tokens: Tokens de saída estimados (para custo).
    """
    catalog = catalog or _MODEL_CATALOG
    low_confidence = confidence < min_confidence

    if strategy != "auto":
        requested = ModelTier(strategy)
        requires_review = low_confidence
        reason = f"estratégia fixa '{strategy}'"
        if low_confidence:
            reason += "; baixa confiança aciona revisão humana"
    else:
        requested, requires_review, reason = _tier_for(risk, low_confidence)

    # Enforcement de orçamento: o custo/latência passam a ser critérios reais.
    requested, reason, requires_review = _apply_budget(
        requested, reason, requires_review, risk, budget_status
    )

    model, fallback_used = _resolve_available(requested, catalog)
    if fallback_used:
        reason += f"; fallback para '{model.tier.value}' por indisponibilidade"

    estimated_cost = _estimate_cost(model, estimated_input_tokens, estimated_output_tokens)

    logger.info(
        "model_router_decision",
        requested_tier=requested.value,
        selected_model=model.name,
        risk=risk.value,
        confidence=round(confidence, 3),
        fallback=fallback_used,
        requires_human_review=requires_review,
        budget_status=budget_status.value,
        estimated_cost=estimated_cost,
        expected_latency_ms=model.avg_latency_ms,
        reason=reason,
    )
    return RoutingDecision(
        model=model,
        requested_tier=requested,
        reason=reason,
        requires_human_review=requires_review,
        fallback_used=fallback_used,
        budget_status=budget_status,
        estimated_cost=estimated_cost,
        expected_latency_ms=model.avg_latency_ms,
    )


def _apply_budget(
    requested: ModelTier,
    reason: str,
    requires_review: bool,
    risk: RiskLevel,
    budget_status: BudgetStatus,
) -> tuple[ModelTier, str, bool]:
    """Ajusta o tier preferido conforme a situação do orçamento (RF3.5)."""
    if budget_status == BudgetStatus.EXCEEDED:
        # Orçamento estourado: força modelo econômico. Se o risco era alto, o
        # rebaixamento não comporta o modelo robusto, então exige revisão humana.
        if risk == RiskLevel.ALTO and requested == ModelTier.ROBUSTO:
            requires_review = True
            reason += "; orçamento excedido: modelo econômico + revisão humana (alto risco)"
        else:
            reason += "; orçamento excedido: modelo econômico"
        return ModelTier.ECONOMICO, reason, requires_review

    if budget_status == BudgetStatus.NEAR_LIMIT and requested != ModelTier.ECONOMICO:
        downgraded = (
            ModelTier.INTERMEDIARIO if requested == ModelTier.ROBUSTO else ModelTier.ECONOMICO
        )
        reason += f"; orçamento próximo do limite: tier rebaixado para '{downgraded.value}'"
        return downgraded, reason, requires_review

    return requested, reason, requires_review
