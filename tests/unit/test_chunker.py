"""Testes unitários do chunker (RF1.2)."""

from __future__ import annotations

import pytest

from app.ingestion.chunker import chunk_text


@pytest.mark.unit
def test_keeps_paragraphs_within_limit() -> None:
    text = "Parágrafo um.\n\nParágrafo dois."
    chunks = chunk_text(text, max_chars=100)
    assert len(chunks) == 1
    assert "Parágrafo um." in chunks[0].text


@pytest.mark.unit
def test_splits_when_exceeding_limit() -> None:
    text = "A" * 50 + "\n\n" + "B" * 50
    chunks = chunk_text(text, max_chars=60)
    assert len(chunks) == 2


@pytest.mark.unit
def test_long_paragraph_is_windowed_with_overlap() -> None:
    text = "x" * 250
    chunks = chunk_text(text, max_chars=100, overlap_chars=20)
    assert len(chunks) >= 3
    assert all(len(c.text) <= 100 for c in chunks)


@pytest.mark.unit
def test_indices_are_sequential() -> None:
    text = "um.\n\ndois.\n\ntrês."
    chunks = chunk_text(text, max_chars=5)
    assert [c.index for c in chunks] == list(range(len(chunks)))


@pytest.mark.unit
def test_invalid_params_raise() -> None:
    with pytest.raises(ValueError):
        chunk_text("abc", max_chars=0)
    with pytest.raises(ValueError):
        chunk_text("abc", max_chars=10, overlap_chars=10)
