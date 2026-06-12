"""Testes de enforcement de orçamento no pipeline (PRIORIDADE 7 / RF3.5).

Garante que o orçamento não seja apenas registrado: ele deve influenciar o
comportamento real (modelo econômico, redução de contexto, cache seguro) e
registrar o enforcement no trace.
"""

from __future__ import annotations

import pytest

from app.cache.semantic_cache import SemanticCache
from app.core.model_router import BudgetStatus
from app.finops.cost import FinOpsTracker
from app.rag.pipeline import RagPipeline
from app.retrieval.retriever import Retriever
from app.retrieval.vector_store import InMemoryVectorStore


def _pipeline(store: InMemoryVectorStore, budget: float) -> RagPipeline:
    return RagPipeline(
        retriever=Retriever(store=store),
        cache=SemanticCache(similarity_threshold=0.92),
        finops=FinOpsTracker(),
        cost_budget_per_answer=budget,
    )


@pytest.mark.integration
def test_normal_budget_does_not_alter_flow(populated_store: InMemoryVectorStore) -> None:
    pipe = _pipeline(populated_store, budget=1.0)
    # Pergunta de alto risco selecionaria modelo robusto sob orçamento normal.
    result = pipe.run("quais são as regras para demissão por justa causa?")
    assert result.budget_status == BudgetStatus.NORMAL.value
    assert result.budget_action is None
    assert result.trace.model_tier == "robusto"


@pytest.mark.integration
def test_exceeded_budget_forces_economico(populated_store: InMemoryVectorStore) -> None:
    # Orçamento minúsculo: o custo do modelo robusto excede o limite.
    pipe = _pipeline(populated_store, budget=1e-9)
    result = pipe.run("quais são as regras para demissão por justa causa?")
    assert result.budget_status == BudgetStatus.EXCEEDED.value
    assert result.trace.model_tier == "economico"
    assert result.model == "minimax-m2.5"
    assert result.budget_action == "contexto_reduzido_e_modelo_economico"


@pytest.mark.integration
def test_exceeded_budget_does_not_allow_expensive_model(
    populated_store: InMemoryVectorStore,
) -> None:
    pipe = _pipeline(populated_store, budget=1e-9)
    result = pipe.run("quais são as regras para demissão por justa causa?")
    # Custo registrado é zero (modelo econômico), nunca o custo do modelo caro.
    assert result.estimated_cost == 0.0


@pytest.mark.integration
def test_budget_enforcement_event_recorded(populated_store: InMemoryVectorStore) -> None:
    events: list[tuple[str, dict]] = []

    class _Sink:
        def event(self, name: str, **fields: object) -> None:
            events.append((name, dict(fields)))

        def record(self, trace: object) -> None:
            return None

    pipe = RagPipeline(
        retriever=Retriever(store=populated_store),
        cache=SemanticCache(similarity_threshold=0.92),
        finops=FinOpsTracker(),
        cost_budget_per_answer=1e-9,
        sink=_Sink(),
    )
    pipe.run("quais são as regras para demissão por justa causa?")
    names = [n for n, _ in events]
    assert "finops_budget_enforced" in names


@pytest.mark.integration
def test_safe_message_when_no_quality_answer(populated_store: InMemoryVectorStore) -> None:
    # Pergunta sem evidência + orçamento estourado: resposta segura, sem stacktrace.
    pipe = _pipeline(populated_store, budget=1e-9)
    result = pipe.run("xpto qualquer coisa irrelevante zzz")
    assert result.answer.answer  # mensagem segura presente
    assert result.answer.requires_human_review is True
