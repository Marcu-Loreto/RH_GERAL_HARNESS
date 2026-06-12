"""Regra de escalação human-in-the-loop (RF3.6).

Decide se uma resposta precisa de revisão humana com base no nível de risco,
confiança da resposta, presença de evidência e confiança de roteamento.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agents.query_intelligence import RiskLevel
from app.core.models import Confidence


@dataclass
class EscalationDecision:
    """Resultado da avaliação de escalação."""

    escalate: bool
    reason: str = ""


def evaluate_escalation(
    *,
    risk: RiskLevel,
    confidence: Confidence,
    has_evidence: bool,
    routing_confidence: float,
    min_routing_confidence: float,
) -> EscalationDecision:
    """Avalia se a resposta deve ser escalada para revisão humana.

    Escala quando:
    - Risco alto (tema sensível)
    - Sem evidência documental
    - Confiança baixa na resposta
    - Confiança de roteamento abaixo do mínimo
    """
    if risk == RiskLevel.ALTO:
        return EscalationDecision(escalate=True, reason="alto risco: tema sensível requer revisão")

    if not has_evidence:
        return EscalationDecision(
            escalate=True, reason="sem evidência documental para sustentar a resposta"
        )

    if confidence == Confidence.BAIXA:
        return EscalationDecision(
            escalate=True, reason="confiança baixa na resposta gerada"
        )

    if routing_confidence < min_routing_confidence:
        return EscalationDecision(
            escalate=True, reason="confiança de roteamento abaixo do limiar"
        )

    return EscalationDecision(escalate=False, reason="")
