"""Divisão de documentos em chunks (RF1.2).

Estratégia simples e previsível para o MVP: agrupa parágrafos respeitando um
limite de caracteres, com sobreposição configurável para preservar contexto
entre trechos. Qualquer mudança nesta estratégia exige teste de regressão.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_PARAGRAPH_RE = re.compile(r"\n\s*\n")
_WHITESPACE_RE = re.compile(r"[ \t]+")


@dataclass
class Chunk:
    """Trecho de texto com sua seção de origem e índice ordinal."""

    index: int
    text: str
    section: str | None = None


def _normalize(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def chunk_text(
    text: str,
    *,
    max_chars: int,
    overlap_chars: int = 0,
) -> list[Chunk]:
    """Divide ``text`` em chunks de até ``max_chars`` caracteres.

    Parágrafos são mantidos juntos quando cabem no limite. Parágrafos maiores que
    o limite são quebrados com sobreposição (``overlap_chars``).

    Raises:
        ValueError: Se ``max_chars`` <= 0 ou ``overlap_chars`` >= ``max_chars``.
    """
    if max_chars <= 0:
        raise ValueError("max_chars deve ser positivo.")
    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("overlap_chars deve estar em [0, max_chars).")

    paragraphs = [_normalize(p) for p in _PARAGRAPH_RE.split(text) if _normalize(p)]
    chunks: list[str] = []
    buffer = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if buffer:
                chunks.append(buffer)
                buffer = ""
            chunks.extend(_split_long(paragraph, max_chars, overlap_chars))
            continue
        candidate = f"{buffer} {paragraph}".strip() if buffer else paragraph
        if len(candidate) <= max_chars:
            buffer = candidate
        else:
            chunks.append(buffer)
            buffer = paragraph
    if buffer:
        chunks.append(buffer)

    return [Chunk(index=i, text=text) for i, text in enumerate(chunks)]


def _split_long(paragraph: str, max_chars: int, overlap_chars: int) -> list[str]:
    """Quebra um parágrafo maior que ``max_chars`` em janelas com sobreposição."""
    pieces: list[str] = []
    step = max_chars - overlap_chars
    start = 0
    while start < len(paragraph):
        pieces.append(paragraph[start : start + max_chars].strip())
        start += step
    return [p for p in pieces if p]
