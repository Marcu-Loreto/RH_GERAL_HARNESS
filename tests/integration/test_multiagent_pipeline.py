"""Testes de integração do pipeline multiagente (SPEC Fase 2 §7)."""

from __future__ import annotations

import pytest

from app.rag.pipeline import RagPipeline


@pytest.mark.integration
@pytest.mark.parametrize(
    ("question", "expected_agent", "expected_domain"),
    [
        ("quantos dias de férias eu tenho?", "agente_beneficios", "beneficios"),
        ("qual o prazo do banco de horas?", "agente_trabalhista", "trabalhista"),
        ("como faço denúncia de assédio no canal de ética?", "agente_compliance", "compliance"),
        (
            "como funciona a promoção e faixa salarial do cargo?",
            "agente_cargos_salarios",
            "cargos_salarios",
        ),
        ("tem reembolso de curso e certificação?", "agente_treinamento", "treinamento"),
        ("como é o processo seletivo da vaga?", "agente_recrutamento", "recrutamento"),
    ],
)
def test_routes_to_correct_agent(
    pipeline: RagPipeline, question: str, expected_agent: str, expected_domain: str
) -> None:
    result = pipeline.run(question)
    assert result.agent == expected_agent
    assert result.domain == expected_domain
    assert result.answer.evidence  # encontrou evidência no domínio correto


@pytest.mark.integration
def test_ambiguous_question_uses_fallback(pipeline: RagPipeline) -> None:
    # Mensagem sem sinal de domínio e sem intenção de recepção → fallback.
    result = pipeline.run("xptolauda qwerty zzz")
    # Sem evidência após fallback → limitação + revisão humana.
    assert result.answer.evidence == []
    assert result.answer.requires_human_review is True


@pytest.mark.integration
def test_greeting_is_handled_by_reception(pipeline: RagPipeline) -> None:
    result = pipeline.run("bom dia, tudo bem com você hoje?")
    assert result.agent == "agente_recepcao"
    assert result.blocked is False
    assert result.answer.requires_human_review is False
    assert result.answer.evidence == []


@pytest.mark.integration
def test_help_request_is_handled_by_reception(pipeline: RagPipeline) -> None:
    result = pipeline.run("oi, o que você faz?")
    assert result.agent == "agente_recepcao"
    assert "RH" in result.answer.answer


@pytest.mark.integration
def test_real_question_skips_reception(pipeline: RagPipeline) -> None:
    # Saudação + pergunta real de domínio → vai para o especialista, não recepção.
    result = pipeline.run("bom dia, quantos dias de férias eu tenho?")
    assert result.agent == "agente_beneficios"


@pytest.mark.integration
def test_decision_is_traceable(pipeline: RagPipeline) -> None:
    result = pipeline.run("quantos dias de férias?")
    trace = result.trace
    assert trace.domain == "beneficios"
    assert trace.agent == "agente_beneficios"
    assert trace.routing_confidence is not None
    assert trace.routing_reason
    assert trace.agents_invoked == ["agente_beneficios"]


@pytest.mark.integration
def test_no_cross_domain_answer(pipeline: RagPipeline) -> None:
    # Pergunta de compliance não deve responder com política de férias.
    result = pipeline.run("denúncia de assédio e conduta ética")
    assert "30 dias de férias" not in result.answer.answer
