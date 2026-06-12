"""Testes unitários do detector de PII (RF1.7 / RF1.8)."""

from __future__ import annotations

import pytest

from app.guardrails.pii import detect_pii, redact_pii


@pytest.mark.unit
@pytest.mark.parametrize(
    ("text", "expected_type"),
    [
        ("meu cpf é 123.456.789-00", "cpf"),
        ("contato: joao@empresa.com", "email"),
        ("ligue para (11) 91234-5678", "phone"),
    ],
)
def test_detects_pii(text: str, expected_type: str) -> None:
    result = detect_pii(text)
    assert result.has_pii is True
    assert expected_type in result.types


@pytest.mark.unit
def test_no_pii_in_plain_question() -> None:
    assert detect_pii("quantos dias de férias eu tenho?").has_pii is False


@pytest.mark.unit
def test_redaction_masks_values() -> None:
    redacted = redact_pii("cpf 123.456.789-00 e email a@b.com")
    assert "123.456.789-00" not in redacted
    assert "a@b.com" not in redacted
    assert "[REDACTED:cpf]" in redacted
