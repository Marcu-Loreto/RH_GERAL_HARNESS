"""Classificador de dificuldade por dicionário (RF3.1 — 3.5).

Classifica perguntas em 3 níveis (fácil, intermediário, difícil) usando
dicionários de termos. A classificação é determinística, sem dependência de
modelo de IA, visando eficiência e previsibilidade.

Prioridade: difícil > intermediário > fácil > default (intermediário).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.core.logging import get_logger

logger = get_logger(__name__)


class DifficultyLevel(StrEnum):
    """Níveis de dificuldade de uma pergunta."""

    FACIL = "facil"
    INTERMEDIARIO = "intermediario"
    DIFICIL = "dificil"


@dataclass(frozen=True)
class DifficultyClassification:
    """Resultado da classificação de dificuldade."""

    level: DifficultyLevel
    matched_terms: list[str]
    reason: str


# Dicionários de termos por nível de dificuldade.
# Palavras-chave que indicam perguntas simples e factuais (busca direta em políticas).
_EASY_TERMS: frozenset[str] = frozenset(
    {
        "quantos dias",
        "férias",
        "vale",
        "refeição",
        "vale transporte",
        "vale alimentação",
        "horário",
        "expediente",
        "ponto",
        "feriado",
        "feriados",
        "recesso",
        "abono",
        "ausência",
        "falta",
        "desconto",
        "salário",
        "13º",
        "décimo terceiro",
        "adiantamento",
        "empréstimo",
        "aposentadoria",
        "idade",
        "tempo de serviço",
        "beneficiário",
        "dependente",
        "documentação",
        "formulário",
        "atestado",
        "comprovante",
        "cópia",
        "original",
        "cpf",
        "rg",
        "pis",
        "ctps",
        "banco",
        "agência",
        "conta",
        "data de nascimento",
    }
)

# Termos que indicam perguntas de complexidade média (requerem interpretação de políticas).
_MEDIUM_TERMS: frozenset[str] = frozenset(
    {
        "promoção",
        "cargo",
        "função",
        "salário",
        "reajuste",
        "aumento",
        "aumento salarial",
        "banco de horas",
        "hora extra",
        "turno",
        "rodízio",
        "escala",
        "jornada",
        "contrato",
        "contratação",
        "terceirizado",
        "clt",
        "pj",
        "estágio",
        "trainee",
        "aprendiz",
        "teletrabalho",
        "home office",
        "trabalho remoto",
        "afastamento",
        "licença",
        "maternidade",
        "paternidade",
        "adoção",
        "gala",
        "luto",
        "casamento",
        "doador de sangue",
        "seguro desemprego",
        "fgts",
        "fundo de garantia",
        "indenização",
        "rescisão",
        "desligamento",
        "exoneração",
        "apoio",
        "programa de bem-estar",
        "saúde mental",
        "terapia",
        "capacitação",
        "treinamento",
        "desenvolvimento",
        "educação corporativa",
        "bolsa de estudos",
        "política",
        "norma",
        "regra",
        "direito",
        "obrigação",
    }
)

# Termos que indicam perguntas sensíveis ou de alta complexidade (requerem cuidado, possível escalonamento).
_HARD_TERMS: frozenset[str] = frozenset(
    {
        "assédio",
        "assédio moral",
        "assédio sexual",
        "discriminação",
        "preconceito",
        "bullying",
        "ameaça",
        "violência",
        "agressão",
        "demissão",
        "demissão por justa causa",
        "justa causa",
        "insubordinação",
        "abandono de emprego",
        "ato falta",
        "falta grave",
        "processo disciplinar",
        "sindicato",
        "greve",
        "paralisação",
        "ação trabalhista",
        "justiça trabalhista",
        "tribunal",
        "advogado",
        "recurso",
        "apelação",
        "denúncia",
        "reclamação",
        "represália",
        "vingança",
        "retaliation",
        "coação",
        "chantagem",
        "fraude",
        "roubo",
        "furto",
        "negligência",
        "imprudência",
        "desvio de função",
        "exploração",
        "trabalho infantil",
        "trabalho forçado",
        "tráfico",
        "corrupção",
        "suborno",
        "conflito de interesse",
        "nepotismo",
        "favoritismo",
        "justiça",
        "ética",
        "compliance",
        "investigação",
        "auditoria",
        "multa",
        "penalidade",
        "sanção",
        "morte",
        "falecimento",
        "suicídio",
        "acidente",
        "lesão",
        "doença ocupacional",
        "segurança do trabalho",
        "ambiente de trabalho",
        "equipamento de proteção",
        "epi",
    }
)


def _normalize_query(query: str) -> str:
    """Normaliza a query para matching case-insensitive."""
    return query.lower().strip()


def _find_matched_terms(
    normalized_query: str, term_dict: frozenset[str]
) -> list[str]:
    """Encontra termos do dicionário que estão presentes na query."""
    matched = []
    for term in sorted(term_dict):
        if term in normalized_query:
            matched.append(term)
    return matched


def classify_difficulty(query: str) -> DifficultyClassification:
    """Classifica a dificuldade de uma pergunta usando dicionários de termos.

    Regra de prioridade: difícil > intermediário > fácil > default (intermediário).
    Se a query contém termos de múltiplos níveis, classifica pelo nível mais alto.

    Args:
        query: A pergunta do usuário.

    Returns:
        DifficultyClassification com nível, termos encontrados e razão.

    Raises:
        Nenhuma — sempre retorna um nível válido (nunca falha).
    """
    if not query or not query.strip():
        logger.warning("classify_difficulty_empty_query")
        return DifficultyClassification(
            level=DifficultyLevel.INTERMEDIARIO,
            matched_terms=[],
            reason="Pergunta vazia; classificada como intermediária por padrão",
        )

    normalized = _normalize_query(query)

    # Buscar termos em cada dicionário (ordem de prioridade: difícil primeiro).
    hard_matches = _find_matched_terms(normalized, _HARD_TERMS)
    medium_matches = _find_matched_terms(normalized, _MEDIUM_TERMS)
    easy_matches = _find_matched_terms(normalized, _EASY_TERMS)

    # Aplicar prioridade: difícil > intermediário > fácil.
    if hard_matches:
        level = DifficultyLevel.DIFICIL
        matched = hard_matches
        reason = f"Pergunta sensível/complexa; encontrados {len(hard_matches)} termo(s) crítico(s): {', '.join(hard_matches[:3])}"
    elif medium_matches:
        level = DifficultyLevel.INTERMEDIARIO
        matched = medium_matches
        reason = f"Pergunta de complexidade média; encontrados {len(medium_matches)} termo(s): {', '.join(medium_matches[:3])}"
    elif easy_matches:
        level = DifficultyLevel.FACIL
        matched = easy_matches
        reason = f"Pergunta simples/factual; encontrados {len(easy_matches)} termo(s): {', '.join(easy_matches[:3])}"
    else:
        # Nenhum termo encontrado → default intermediário
        level = DifficultyLevel.INTERMEDIARIO
        matched = []
        reason = "Nenhum termo conhecido encontrado; classificada como intermediária por padrão"

    logger.info(
        "classify_difficulty",
        level=level.value,
        matched_count=len(matched),
        reason=reason,
    )

    return DifficultyClassification(level=level, matched_terms=matched, reason=reason)
