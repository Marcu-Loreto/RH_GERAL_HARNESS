"""Testes de propagação do screen() do agente para a resposta (PRIORIDADE 8).

Garante que a decisão de triagem de risco do agente governe a resposta final:
bloqueio impede geração normal; revisão humana é propagada; reconciliação com
``evaluate_escalation``.
"""

from __future__ import annotations

import pytest

from app.rag.pipeline import RagPipeline


@pytest.mark.integration
def test_compensation_individual_salary_is_blocked(pipeline: RagPipeline) -> None:
    result = pipeline.run("quanto o colega recebe de remuneração mensal?")
    assert result.blocked is True
    assert result.answer.screening_decision == "blocked"
    assert result.answer.requires_human_review is True
    assert result.answer.evidence == []


@pytest.mark.integration
def test_compliance_sensitive_requires_human_review(pipeline: RagPipeline) -> None:
    result = pipeline.run("como denunciar um caso de assédio e discriminação?")
    assert result.answer.requires_human_review is True
    assert result.answer.escalation_reason


@pytest.mark.integration
def test_screening_and_escalation_reconciled(pipeline: RagPipeline) -> None:
    # Tema sensível trabalhista: screen() pede revisão humana e escalonamento
    # também sinaliza alto risco. A razão final deve consolidar ambos.
    result = pipeline.run("quais regras para afastamento e advertência disciplinar?")
    assert result.answer.requires_human_review is True
    assert result.answer.escalation_reason
    assert result.answer.screening_decision == "human_review"


@pytest.mark.integration
def test_blocked_screening_skips_normal_generation(pipeline: RagPipeline) -> None:
    result = pipeline.run("quanto o colega de trabalho ganha de salário?")
    assert result.blocked is True
    # Não usa modelo nem gera resposta fundamentada.
    assert result.answer.evidence == []
    assert result.trace.model_tier is None


@pytest.mark.integration
def test_normal_question_no_human_review(pipeline: RagPipeline) -> None:
    result = pipeline.run("quantos dias de férias eu tenho?")
    assert result.answer.requires_human_review is False
    assert result.answer.screening_decision is None


@pytest.mark.integration
def test_final_answer_reflects_requires_human_review(pipeline: RagPipeline) -> None:
    sensitive = pipeline.run("como denunciar fraude e conflito de interesse?")
    normal = pipeline.run("tem reembolso de curso e certificação?")
    assert sensitive.answer.requires_human_review is True
    assert normal.answer.requires_human_review is False
