"""Golden dataset: modelos e carregadores (EVALUATION_HARNESS §3).

Carrega o corpus de documentos e os itens do golden dataset usados para avaliar
retrieval, fidelidade da resposta e comportamentos de segurança.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from app.core.models import DocumentMetadata

# Comportamentos esperados possíveis para um item do golden dataset.
ExpectedBehavior = str  # "answer" | "refuse" | "human_review" | "clarify"


class CorpusEntry(BaseModel):
    """Entrada do corpus: documento + texto bruto a ingerir."""

    document: DocumentMetadata
    raw_text: str


class GoldenItem(BaseModel):
    """Item do golden dataset."""

    id: str
    question: str
    expected_domain: str
    expected_agent: str
    expected_sources: list[str] = []
    risk_level: str = "baixo"
    expected_behavior: ExpectedBehavior = "answer"
    must_include: list[str] = []
    must_not_include: list[str] = []


def load_corpus(path: str | Path) -> list[CorpusEntry]:
    """Carrega o corpus de documentos de um arquivo JSON."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [CorpusEntry.model_validate(item) for item in data]


def load_golden(path: str | Path) -> list[GoldenItem]:
    """Carrega os itens do golden dataset de um arquivo JSON."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [GoldenItem.model_validate(item) for item in data]
