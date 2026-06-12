"""Testes unitários do agente de recepção (front door)."""

from __future__ import annotations

import pytest

from app.agents.reception_agent import ReceptionAgent


@pytest.fixture()
def reception() -> ReceptionAgent:
    return ReceptionAgent()


@pytest.mark.unit
@pytest.mark.parametrize(
    ("text", "intent"),
    [
        ("oi", "saudacao"),
        ("bom dia, tudo bem?", "saudacao"),
        ("obrigado!", "agradecimento"),
        ("tchau", "despedida"),
        ("o que você faz?", "ajuda"),
        ("me ajuda", "ajuda"),
    ],
)
def test_detects_reception_intents(reception: ReceptionAgent, text: str, intent: str) -> None:
    assert reception.detect_intent(text) == intent


@pytest.mark.unit
def test_domain_question_is_not_reception(reception: ReceptionAgent) -> None:
    # Mensagem com sinal de domínio (férias) não é recepção.
    assert reception.detect_intent("bom dia, quantos dias de férias eu tenho?") is None


@pytest.mark.unit
def test_unknown_text_is_not_reception(reception: ReceptionAgent) -> None:
    assert reception.detect_intent("xptolauda qwerty zzz") is None


@pytest.mark.unit
def test_try_handle_returns_welcome_for_greeting(reception: ReceptionAgent) -> None:
    answer = reception.try_handle("olá")
    assert answer is not None
    assert answer.requires_human_review is False
    assert answer.evidence == []
    assert answer.answer


@pytest.mark.unit
def test_try_handle_returns_none_for_real_question(reception: ReceptionAgent) -> None:
    assert reception.try_handle("qual o prazo do banco de horas?") is None
