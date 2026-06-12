"""Teste RAG de acurácia de roteamento (SPEC Fase 2 §6, ≥90%).

Serve como regressão para mudanças no classificador de domínio / orquestrador.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.agents.query_intelligence import classify

_ROUTING_PATH = Path("datasets/routing_rh.json")


@pytest.fixture()
def routing_items() -> list[dict[str, object]]:
    return json.loads(_ROUTING_PATH.read_text(encoding="utf-8"))


@pytest.mark.integration
def test_routing_accuracy_meets_threshold(routing_items: list[dict[str, object]]) -> None:
    correct = 0
    for item in routing_items:
        intel = classify(str(item["question"]))
        if item["expect_fallback"]:
            ok = intel.fallback_required
        else:
            ok = (not intel.fallback_required) and intel.agent == item["expected_agent"]
        correct += int(ok)
    accuracy = correct / len(routing_items)
    assert accuracy >= 0.90


@pytest.mark.integration
def test_fallback_items_flagged(routing_items: list[dict[str, object]]) -> None:
    for item in routing_items:
        if item["expect_fallback"]:
            assert classify(str(item["question"])).fallback_required is True
