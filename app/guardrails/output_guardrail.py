"""Guardrail de saída (RF1.8).

Valida a resposta gerada antes da entrega: exige evidência (fonte), bloqueia
vazamento de PII e verifica formato mínimo. Resposta sem fonte é reprovada.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.logging import get_logger
from app.core.models import Answer
from app.guardrails.pii import detect_pii
from app.guardrails.policies import BlockReason

logger = get_logger(__name__)


@dataclass
class OutputGuardrailResult:
    """Resultado da verificação de saída."""

    approved: bool
    reasons: list[BlockReason] = field(default_factory=list)


def check_output(answer: Answer) -> OutputGuardrailResult:
    """Valida a resposta final.

    Regras:
    - deve haver ao menos uma evidência (fonte);
    - o texto não pode conter PII;
    - a resposta não pode ser vazia.
    """
    reasons: list[BlockReason] = []

    if not answer.answer.strip() or not answer.evidence:
        reasons.append(BlockReason.NO_EVIDENCE)
    if detect_pii(answer.answer).has_pii:
        reasons.append(BlockReason.PII_LEAKAGE)

    approved = not reasons
    if not approved:
        logger.warning("output_blocked", reasons=[r.value for r in reasons])
    return OutputGuardrailResult(approved=approved, reasons=reasons)
