"""Utilitários de segurança da Fase 0: sanitização básica de entrada.

Esta é a primeira camada (mínima) de proteção de entrada. Guardrails completos
(prompt injection, jailbreak, PII) serão implementados na Fase 1. Aqui tratamos
apenas normalização e remoção de caracteres de controle perigosos.
"""

from __future__ import annotations

import re
import unicodedata

# Caracteres de controle (exceto tab, newline e carriage return) são removidos.
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MULTISPACE_RE = re.compile(r"[ \t]{2,}")


class InputValidationError(ValueError):
    """Erro levantado quando a entrada é inválida (vazia ou excede o limite)."""


def sanitize_input(text: str, *, max_length: int = 4000) -> str:
    """Sanitiza uma entrada textual de usuário.

    - normaliza unicode (NFKC);
    - remove caracteres de controle perigosos;
    - colapsa espaços redundantes;
    - remove espaços nas bordas.

    Args:
        text: Texto bruto fornecido pelo usuário.
        max_length: Tamanho máximo permitido após a sanitização.

    Returns:
        Texto sanitizado.

    Raises:
        InputValidationError: Se o texto não for ``str``, for vazio após a
            sanitização ou exceder ``max_length``.
    """
    if not isinstance(text, str):
        raise InputValidationError("A entrada deve ser uma string.")

    normalized = unicodedata.normalize("NFKC", text)
    without_control = _CONTROL_CHARS_RE.sub("", normalized)
    collapsed = _MULTISPACE_RE.sub(" ", without_control).strip()

    if not collapsed:
        raise InputValidationError("A entrada não pode ser vazia.")
    if len(collapsed) > max_length:
        raise InputValidationError(f"A entrada excede o tamanho máximo de {max_length} caracteres.")
    return collapsed
