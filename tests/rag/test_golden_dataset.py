"""Teste RAG sobre o golden dataset (EVALUATION_HARNESS §5).

Valida precision@k, comportamento esperado e checagens de conteúdo. Serve como
teste de regressão para mudanças em prompt, chunking, embedding ou retrieval.
"""

from __future__ import annotations

import pytest

from app.evaluation.evaluator import evaluate
from app.evaluation.golden import GoldenItem
from app.rag.pipeline import RagPipeline


@pytest.mark.integration
def test_golden_dataset_meets_thresholds(
    pipeline: RagPipeline, golden_items: list[GoldenItem]
) -> None:
    report = evaluate(pipeline, golden_items)
    assert report.avg_precision_at_k >= 0.85
    assert report.behavior_accuracy >= 0.90
    assert report.meets_thresholds()


@pytest.mark.integration
def test_golden_expected_sources_retrieved(
    pipeline: RagPipeline, golden_items: list[GoldenItem]
) -> None:
    report = evaluate(pipeline, golden_items)
    # Toda pergunta respondível deve recuperar ao menos uma fonte esperada.
    assert report.source_recall >= 0.85


@pytest.mark.integration
def test_golden_content_checks(pipeline: RagPipeline, golden_items: list[GoldenItem]) -> None:
    report = evaluate(pipeline, golden_items)
    assert report.content_pass_rate == 1.0
