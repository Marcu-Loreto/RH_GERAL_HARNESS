"""Testes unitários de sanitização básica de entrada (RF0.4 / segurança)."""

from __future__ import annotations

import pytest

from app.core.security import InputValidationError, sanitize_input


@pytest.mark.unit
def test_trims_and_collapses_whitespace() -> None:
    assert sanitize_input("  quantos   dias   de   férias?  ") == "quantos dias de férias?"


@pytest.mark.unit
def test_removes_control_characters() -> None:
    assert sanitize_input("ola\x00\x07mundo") == "olamundo"


@pytest.mark.unit
def test_normalizes_unicode() -> None:
    # Caractere de compatibilidade NFKC é normalizado.
    assert sanitize_input("ﬁm") == "fim"


@pytest.mark.unit
def test_empty_input_rejected() -> None:
    with pytest.raises(InputValidationError):
        sanitize_input("   ")


@pytest.mark.unit
def test_non_string_rejected() -> None:
    with pytest.raises(InputValidationError):
        sanitize_input(123)  # type: ignore[arg-type]


@pytest.mark.unit
def test_max_length_enforced() -> None:
    with pytest.raises(InputValidationError):
        sanitize_input("a" * 10, max_length=5)
