"""Guardrail de entrada (RF1.7).

Analisa a pergunta antes do processamento: sanitiza, bloqueia prompt injection,
pedidos de PII de terceiros e perguntas claramente fora do escopo de RH.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.logging import get_logger
from app.core.security import InputValidationError, sanitize_input
from app.guardrails.pii import detect_pii
from app.guardrails.policies import BlockReason
from app.guardrails.prompt_injection import detect_prompt_injection

logger = get_logger(__name__)

# Pedido de dados pessoais de terceiros (ex.: "qual o salário/CPF do João").
_PII_REQUEST_RE = re.compile(
    r"\b(cpf|rg|sal[áa]rio|endere[çc]o|telefone|e-?mail|dados pessoais)\b.{0,40}"
    r"\b(d[oea]|do colega|do funcion[áa]rio|de outro|de terceiro|da pessoa)\b",
    re.IGNORECASE,
)


@dataclass
class InputGuardrailResult:
    """Resultado da verificação de entrada."""

    allowed: bool
    sanitized_query: str = ""
    reasons: list[BlockReason] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return not self.allowed


def check_input(raw_query: str) -> InputGuardrailResult:
    """Valida e classifica a entrada do usuário."""
    try:
        sanitized = sanitize_input(raw_query)
    except InputValidationError:
        logger.warning("input_blocked", reason=BlockReason.INVALID_INPUT.value)
        return InputGuardrailResult(allowed=False, reasons=[BlockReason.INVALID_INPUT])

    reasons: list[BlockReason] = []

    if detect_prompt_injection(sanitized).detected:
        reasons.append(BlockReason.PROMPT_INJECTION)
    if _PII_REQUEST_RE.search(sanitized) or detect_pii(sanitized).has_pii:
        reasons.append(BlockReason.PII_REQUEST)

    if reasons:
        logger.warning("input_blocked", reasons=[r.value for r in reasons])
        return InputGuardrailResult(allowed=False, sanitized_query=sanitized, reasons=reasons)

    return InputGuardrailResult(allowed=True, sanitized_query=sanitized)
