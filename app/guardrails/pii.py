"""Detecção simples de PII em texto (RF1.7 / RF1.8).

Detector baseado em padrões para o MVP, focado em PII brasileira comum (CPF,
e-mail, telefone) e identificadores sensíveis. Não substitui um detector
avançado, mas cobre os casos básicos exigidos na Fase 1.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Padrões de PII. Mantidos simples e auditáveis.
_PATTERNS: dict[str, re.Pattern[str]] = {
    "cpf": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    "cnpj": re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "phone": re.compile(r"\b(?:\+?55\s?)?\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4}\b"),
    "rg": re.compile(r"\bRG\s*:?\s*\d{1,2}\.?\d{3}\.?\d{3}-?\w\b", re.IGNORECASE),
}


@dataclass
class PIIResult:
    """Resultado da detecção de PII."""

    has_pii: bool
    types: list[str] = field(default_factory=list)


def detect_pii(text: str) -> PIIResult:
    """Detecta categorias de PII presentes em ``text``."""
    found = [name for name, pattern in _PATTERNS.items() if pattern.search(text)]
    return PIIResult(has_pii=bool(found), types=sorted(found))


def redact_pii(text: str) -> str:
    """Mascara ocorrências de PII no texto, substituindo por ``[REDACTED:<tipo>]``."""
    redacted = text
    for name, pattern in _PATTERNS.items():
        redacted = pattern.sub(f"[REDACTED:{name}]", redacted)
    return redacted
