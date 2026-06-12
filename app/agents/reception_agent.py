"""Agente de Recepção — porta de entrada da conversa (front door).

Responsável por toda a recepção do usuário: saudações, agradecimentos,
despedidas e pedidos de ajuda/orientação ("o que você faz?"). Quando a mensagem
é puramente social (sem sinal de domínio de RH), a recepção responde de forma
acolhedora e orienta o usuário — sem acionar retrieval, modelo ou revisão humana.

Perguntas reais de RH (que contêm sinal de domínio) **não** são interceptadas:
seguem para o orquestrador e os agentes especialistas. A mensagem de boas-vindas
é uma frase curta e dedicada (constante ``_DEFAULT_WELCOME``) — o corpo do prompt
comportamental em ``prompts/agents/reception_agent.md`` é especificação interna e
**nunca** deve ser devolvido ao usuário.
"""

from __future__ import annotations

import re

from app.agents.query_intelligence import has_domain_keywords
from app.core.clock import greeting_for
from app.core.logging import get_logger
from app.core.models import Answer, Confidence

logger = get_logger(__name__)

RECEPTION_AGENT_ID = "reception_agent"
RECEPTION_AGENT_NAME = "agente_recepcao"

# Padrões de intenção social (sem sinal de domínio de RH).
_GREETING_TERMS: tuple[str, ...] = (
    "oi",
    "ola",
    "olá",
    "ei",
    "eai",
    "e ai",
    "e aí",
    "bom dia",
    "boa tarde",
    "boa noite",
    "tudo bem",
    "tudo bom",
    "como vai",
    "alo",
    "alô",
)
_THANKS_TERMS: tuple[str, ...] = (
    "obrigado",
    "obrigada",
    "valeu",
    "agradeço",
    "agradecido",
    "muito obrigado",
)
_FAREWELL_TERMS: tuple[str, ...] = (
    "tchau",
    "até logo",
    "ate logo",
    "até mais",
    "ate mais",
    "adeus",
    "falou",
)
_HELP_TERMS: tuple[str, ...] = (
    "o que voce faz",
    "o que você faz",
    "o que voce pode fazer",
    "o que você pode fazer",
    "quem e voce",
    "quem é você",
    "como funciona",
    "ajuda",
    "me ajuda",
    "pode ajudar",
    "no que pode ajudar",
)

# Corpo da mensagem de boas-vindas (sem a saudação inicial). A saudação —
# "Bom dia/Boa tarde/Boa noite" — é prefixada dinamicamente conforme o horário
# de São Paulo (ver ``_build_welcome``).
_WELCOME_BODY = (
    "Sou o assistente virtual de RH. Posso ajudar com dúvidas sobre "
    "benefícios, trabalhista e políticas internas, cargos e salários, "
    "treinamento, recrutamento e compliance. Sobre o que você gostaria de saber?"
)
# Fallback estático (usado quando não há instante de referência disponível).
_DEFAULT_WELCOME = f"Olá! {_WELCOME_BODY}"
_THANKS_MESSAGE = "De nada! Posso ajudar com mais alguma dúvida de RH?"
_FAREWELL_MESSAGE = "Até logo! Se precisar de algo sobre RH, é só voltar."


def _build_welcome() -> str:
    """Monta a saudação de boas-vindas sensível ao horário de São Paulo."""
    return f"{greeting_for()}! {_WELCOME_BODY}"


def _matches_any(text: str, terms: tuple[str, ...]) -> bool:
    """Verifica se o texto contém algum dos termos, respeitando limites de palavra."""
    for term in terms:
        if re.search(rf"\b{re.escape(term)}\b", text):
            return True
    return False


class ReceptionAgent:
    """Agente de recepção: acolhe o usuário e orienta antes do roteamento."""

    AGENT_ID = RECEPTION_AGENT_ID
    NAME = RECEPTION_AGENT_NAME

    def __init__(self) -> None:
        self.name = RECEPTION_AGENT_NAME
        self.agent_id = RECEPTION_AGENT_ID

    @property
    def _welcome(self) -> str:
        """Mensagem de boas-vindas exibida ao usuário.

        É uma frase curta e dedicada, com saudação sensível ao horário de São
        Paulo — NUNCA o corpo do prompt comportamental do agente
        (``prompts/agents/reception_agent.md``), que é especificação interna e
        não deve ser exposta ao usuário.
        """
        return _build_welcome()

    def detect_intent(self, text: str) -> str | None:
        """Classifica a intenção social da mensagem, ou ``None`` se não for recepção.

        Mensagens com sinal de domínio de RH nunca são tratadas como recepção —
        elas devem seguir para os agentes especialistas.
        """
        lowered = " ".join(text.lower().split())
        if not lowered:
            return None
        if has_domain_keywords(lowered):
            return None
        if _matches_any(lowered, _FAREWELL_TERMS):
            return "despedida"
        if _matches_any(lowered, _THANKS_TERMS):
            return "agradecimento"
        if _matches_any(lowered, _HELP_TERMS):
            return "ajuda"
        if _matches_any(lowered, _GREETING_TERMS):
            return "saudacao"
        return None

    def try_handle(self, text: str) -> Answer | None:
        """Responde a mensagens de recepção; retorna ``None`` para seguir o fluxo."""
        intent = self.detect_intent(text)
        if intent is None:
            return None

        if intent == "agradecimento":
            message = _THANKS_MESSAGE
        elif intent == "despedida":
            message = _FAREWELL_MESSAGE
        else:  # saudacao | ajuda
            message = self._welcome

        logger.info("reception_handled", intent=intent)
        return Answer(
            answer=message,
            evidence=[],
            confidence=Confidence.ALTA,
            limitations=None,
            requires_human_review=False,
        )
