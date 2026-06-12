"""Utilitários de data/hora no fuso horário de São Paulo (America/Sao_Paulo).

Centraliza a obtenção do "agora" no fuso oficial do produto (pt-BR / Brasil),
evitando ``datetime.now()`` sem timezone espalhado pelo código. Use estas
funções sempre que a hora local do usuário for relevante — por exemplo, para
saudações sensíveis ao período do dia (bom dia / boa tarde / boa noite).
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

# Fuso horário oficial do produto. America/Sao_Paulo cobre o horário de Brasília
# (e eventual horário de verão, caso volte a vigorar) de forma correta.
SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")


def now_sao_paulo() -> datetime:
    """Retorna o ``datetime`` atual com timezone em America/Sao_Paulo."""
    return datetime.now(SAO_PAULO_TZ)


def greeting_for(moment: datetime | None = None) -> str:
    """Retorna a saudação adequada ao período do dia em São Paulo.

    - 05:00–11:59 → "Bom dia"
    - 12:00–17:59 → "Boa tarde"
    - 18:00–04:59 → "Boa noite"

    Args:
        moment: Instante de referência. Quando ``None``, usa o agora em SP.
    """
    reference = moment or now_sao_paulo()
    hour = reference.hour
    if 5 <= hour < 12:
        return "Bom dia"
    if 12 <= hour < 18:
        return "Boa tarde"
    return "Boa noite"
