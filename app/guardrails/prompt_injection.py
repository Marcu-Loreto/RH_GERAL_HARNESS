"""Detecção simples de prompt injection / jailbreak (RF1.7).

Detector baseado em padrões para tentativas comuns de manipulação: pedidos para
ignorar instruções, revelar o prompt do sistema, assumir outra persona ou burlar
políticas. Cobre PT-BR e EN. Não é exaustivo, mas atende ao escopo do MVP.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_PATTERNS: dict[str, re.Pattern[str]] = {
    "ignore_instructions": re.compile(
        r"\b(ignore|desconsidere|esque[çc]a|disregard)\b.{0,30}"
        r"\b(instru[çc][õo]es|regras|pol[íi]ticas|instructions|rules)\b",
        re.IGNORECASE,
    ),
    "reveal_prompt": re.compile(
        r"\b(revele|mostre|exiba|repita|imprima|show|reveal|print)\b.{0,30}"
        r"\b(system prompt|prompt do sistema|prompt interno|instru[çc][õo]es internas)\b",
        re.IGNORECASE,
    ),
    "override_role": re.compile(
        r"\b(voc[êe] agora [ée]|a partir de agora voc[êe]|you are now|act as|"
        r"finja que|pretend to be|ignore que voc[êe])\b",
        re.IGNORECASE,
    ),
    "bypass_policy": re.compile(
        r"\b(sem restri[çc][õo]es|sem filtros|modo desenvolvedor|developer mode|"
        r"jailbreak|dan mode|bypass)\b",
        re.IGNORECASE,
    ),
}


@dataclass
class InjectionResult:
    """Resultado da detecção de prompt injection."""

    detected: bool
    categories: list[str] = field(default_factory=list)


def detect_prompt_injection(text: str) -> InjectionResult:
    """Detecta padrões de prompt injection / jailbreak em ``text``."""
    matches = [name for name, pattern in _PATTERNS.items() if pattern.search(text)]
    return InjectionResult(detected=bool(matches), categories=sorted(matches))
