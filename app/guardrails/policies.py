"""Respostas e categorias padronizadas de guardrail (PROMPTS_AND_POLICIES).

Centraliza as mensagens de recusa segura, sem evidência e de encaminhamento ao
RH, garantindo consistência e facilitando versionamento/regressão.

As mensagens que oferecem abertura de chamado leem a URL de
``Settings.support_ticket_url`` (nunca hardcode espalhado pelo código).
"""

from __future__ import annotations

from enum import StrEnum

from app.core.config import get_settings

# Texto base (sem URL) de ausência de evidência. Mantido separado para reuso em
# estimativas de tokens e testes.
NO_EVIDENCE_BASE = (
    "Não encontrei evidência suficiente na base consultada para responder com "
    "segurança. Recomendo validar este caso com o RH responsável ou com a área "
    "jurídica, conforme a natureza da dúvida."
)

# Resposta padrão para pedido proibido / tentativa de burlar o sistema
# (prompt injection, entrada inválida). É recusa de segurança pura: NÃO oferece
# abertura de chamado, para não incentivar tentativas de bypass.
FORBIDDEN_REQUEST_RESPONSE = (
    "Não posso ajudar com essa solicitação porque ela envolve informação "
    "restrita, dado pessoal sensível ou uma ação fora do escopo permitido. "
    "Posso ajudar com orientações gerais baseadas em políticas internas "
    "autorizadas."
)


def no_evidence_response() -> str:
    """Resposta educada quando não há evidência/escopo, com link de chamado.

    Usada quando a pergunta é legítima mas o sistema não tem base para responder
    (fora de escopo dos agentes, sem documento vigente, ou resposta reprovada
    por falta de fonte) — orienta o usuário a abrir um chamado no RH.
    """
    url = get_settings().support_ticket_url
    return f"{NO_EVIDENCE_BASE} Se preferir, abra um chamado no RH: {url}"


def restricted_data_response() -> str:
    """Resposta para pedido legítimo porém restrito (dado pessoal do próprio).

    Diferente da recusa de segurança: o pedido não é malicioso, então orienta o
    usuário ao atendimento humano (RH presencial / chamado).
    """
    url = get_settings().support_ticket_url
    return (
        "Não posso tratar informações pessoais ou restritas por este canal. "
        "Para esse tipo de solicitação, procure o RH presencialmente ou abra um "
        f"chamado: {url}"
    )


class BlockReason(StrEnum):
    """Motivos de bloqueio acionados pelos guardrails (para trace/observabilidade)."""

    PROMPT_INJECTION = "prompt_injection"
    PII_REQUEST = "pii_request"
    PII_LEAKAGE = "pii_leakage"
    OUT_OF_SCOPE = "out_of_scope"
    NO_EVIDENCE = "no_evidence"
    INVALID_INPUT = "invalid_input"
