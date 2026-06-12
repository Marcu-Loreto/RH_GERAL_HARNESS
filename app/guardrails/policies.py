"""Respostas e categorias padronizadas de guardrail (PROMPTS_AND_POLICIES).

Centraliza as mensagens de recusa segura e sem evidência, garantindo
consistência e facilitando versionamento/regressão.
"""

from __future__ import annotations

from enum import StrEnum

# Resposta padrão quando não há evidência suficiente (política §6).
NO_EVIDENCE_RESPONSE = (
    "Não encontrei evidência suficiente na base consultada para responder com "
    "segurança. Recomendo validar este caso com o RH responsável ou com a área "
    "jurídica, conforme a natureza da dúvida."
)

# Resposta padrão para pedido proibido / fora de escopo (política §7).
FORBIDDEN_REQUEST_RESPONSE = (
    "Não posso ajudar com essa solicitação porque ela envolve informação "
    "restrita, dado pessoal sensível ou uma ação fora do escopo permitido. "
    "Posso ajudar com orientações gerais baseadas em políticas internas "
    "autorizadas."
)


class BlockReason(StrEnum):
    """Motivos de bloqueio acionados pelos guardrails (para trace/observabilidade)."""

    PROMPT_INJECTION = "prompt_injection"
    PII_REQUEST = "pii_request"
    PII_LEAKAGE = "pii_leakage"
    OUT_OF_SCOPE = "out_of_scope"
    NO_EVIDENCE = "no_evidence"
    INVALID_INPUT = "invalid_input"
