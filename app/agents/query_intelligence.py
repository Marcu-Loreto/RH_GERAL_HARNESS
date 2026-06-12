"""Query Intelligence Layer (RF2.1, RF2.2, RF2.4).

Classifica a pergunta em um domínio de RH, gera a query canônica para retrieval,
extrai termos obrigatórios, estima risco e confiança e sinaliza necessidade de
fallback. Implementação determinística por palavras-chave (sem LLM), alinhada à
estratégia de baixo custo do projeto. A saída segue o contrato da SPEC §5.

Qualquer alteração nas palavras-chave/regras exige teste de regressão de
roteamento (TEST_STRATEGY §2.6).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from app.core.config import get_settings
from app.retrieval.embeddings import tokenize

_STOPWORDS: frozenset[str] = frozenset(
    "a o os as de do da dos das e que em no na nos nas para por com um uma "
    "ao aos pela pelo se eu meu minha tenho ter posso qual quais quanto quantos "
    "como onde quando meu sua seu eh é minha posso devo qual".split()
)


class Domain(StrEnum):
    """Domínios de RH atendidos por agentes especialistas (SPEC §3)."""

    BENEFICIOS = "beneficios"
    TRABALHISTA = "trabalhista"
    CARGOS_SALARIOS = "cargos_salarios"
    TREINAMENTO = "treinamento"
    RECRUTAMENTO = "recrutamento"
    COMPLIANCE = "compliance"


class RiskLevel(StrEnum):
    """Nível de risco da pergunta."""

    BAIXO = "baixo"
    MEDIO = "medio"
    ALTO = "alto"


# Palavras-chave/frases por domínio (substring em query canônica, minúscula).
_DOMAIN_KEYWORDS: dict[Domain, tuple[str, ...]] = {
    Domain.BENEFICIOS: (
        "férias",
        "ferias",
        "vale",
        "refeição",
        "refeicao",
        "alimentação",
        "alimentacao",
        "benefício",
        "beneficio",
        "plano de saúde",
        "plano de saude",
        "transporte",
        "abono",
        "décimo terceiro",
        "decimo terceiro",
        "13",
        "auxílio",
        "auxilio",
        "licença",
        "licenca",
    ),
    Domain.TRABALHISTA: (
        "banco de horas",
        "hora extra",
        "horas extras",
        "jornada",
        "ponto",
        "home office",
        "trabalho remoto",
        "remoto",
        "afastamento",
        "atestado",
        "falta",
        "sindicato",
        "sindical",
        "clt",
        "férias coletivas",
        "política",
        "politica",
    ),
    Domain.CARGOS_SALARIOS: (
        "cargo",
        "salário",
        "salario",
        "promoção",
        "promocao",
        "remuneração",
        "remuneracao",
        "nível",
        "nivel",
        "senioridade",
        "competência",
        "competencia",
        "plano de carreira",
        "carreira",
        "mérito",
        "merito",
        "reajuste",
    ),
    Domain.TREINAMENTO: (
        "treinamento",
        "curso",
        "capacitação",
        "capacitacao",
        "desenvolvimento",
        "trilha",
        "certificação",
        "certificacao",
        "mentoria",
        "onboarding",
        "aprendizagem",
    ),
    Domain.RECRUTAMENTO: (
        "vaga",
        "recrutamento",
        "seleção",
        "selecao",
        "contratação",
        "contratacao",
        "entrevista",
        "candidato",
        "indicação",
        "indicacao",
        "processo seletivo",
        "admissão",
        "admissao",
    ),
    Domain.COMPLIANCE: (
        "compliance",
        "conduta",
        "ética",
        "etica",
        "denúncia",
        "denuncia",
        "assédio",
        "assedio",
        "discriminação",
        "discriminacao",
        "conflito de interesse",
        "código",
        "codigo",
        "anticorrupção",
        "anticorrupcao",
        "fraude",
    ),
}

# Termos que elevam o nível de risco (temas sensíveis — PROMPTS_AND_POLICIES).
_HIGH_RISK_TERMS: tuple[str, ...] = (
    "demissão",
    "demissao",
    "assédio",
    "assedio",
    "discriminação",
    "discriminacao",
    "disciplinar",
    "sindical",
    "afastamento",
    "saúde",
    "saude",
    "processo",
    "advertência",
    "advertencia",
    "justa causa",
)
_MEDIUM_RISK_TERMS: tuple[str, ...] = (
    "salário",
    "salario",
    "promoção",
    "promocao",
    "denúncia",
    "denuncia",
    "reajuste",
    "rescisão",
    "rescisao",
)

# Mapeia cada domínio ao valor de area_rh usado nos metadados dos documentos.
DOMAIN_TO_AREA: dict[Domain, str] = {
    Domain.BENEFICIOS: "beneficios",
    Domain.TRABALHISTA: "politicas",
    Domain.CARGOS_SALARIOS: "cargos_salarios",
    Domain.TREINAMENTO: "treinamento",
    Domain.RECRUTAMENTO: "recrutamento",
    Domain.COMPLIANCE: "compliance",
}

AREA_TO_DOMAIN: dict[str, Domain] = {area: dom for dom, area in DOMAIN_TO_AREA.items()}

# Áreas de RH válidas (valores aceitos em ``area_rh``). Usado para validação
# de entrada e para devolver erro controlado em vez de ignorar silenciosamente.
KNOWN_AREAS: frozenset[str] = frozenset(DOMAIN_TO_AREA.values())


def is_known_area(area: str) -> bool:
    """Indica se ``area`` corresponde a um domínio de RH atendido."""
    return area in KNOWN_AREAS


@dataclass
class QueryIntelligence:
    """Saída da Query Intelligence Layer (SPEC §5)."""

    domain: Domain
    agent: str
    canonical_query: str
    must_terms: list[str] = field(default_factory=list)
    metadata_filters: dict[str, str] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.BAIXO
    confidence: float = 0.0
    fallback_required: bool = False
    secondary_domain: Domain | None = None


def agent_name_for(domain: Domain) -> str:
    """Nome canônico do agente responsável por um domínio."""
    return f"agente_{domain.value}"


def canonicalize(query: str) -> tuple[str, list[str]]:
    """Gera a query canônica (sem stopwords) e a lista de termos de conteúdo."""
    terms = [t for t in tokenize(query) if t not in _STOPWORDS and len(t) > 2]
    return " ".join(terms), terms


def _assess_risk(text: str) -> RiskLevel:
    lowered = text.lower()
    if any(term in lowered for term in _HIGH_RISK_TERMS):
        return RiskLevel.ALTO
    if any(term in lowered for term in _MEDIUM_RISK_TERMS):
        return RiskLevel.MEDIO
    return RiskLevel.BAIXO


def _score_domains(text: str) -> dict[Domain, int]:
    lowered = text.lower()
    scores: dict[Domain, int] = {}
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in lowered)
        if hits:
            scores[domain] = hits
    return scores


def has_domain_keywords(text: str) -> bool:
    """Indica se a pergunta contém algum termo de domínio de RH conhecido.

    Usado pela recepção para distinguir saudações/conversa social (sem sinal de
    domínio) de perguntas reais de RH (que devem ir para os especialistas).
    """
    return bool(_score_domains(text))


def classify(query: str, forced_area: str | None = None) -> QueryIntelligence:
    """Classifica a pergunta e produz a inteligência de roteamento.

    Args:
        query: Pergunta (já sanitizada) do usuário.
        forced_area: Quando informado, força o domínio correspondente à área
            (compatibilidade / dica explícita do cliente).
    """
    settings = get_settings()
    canonical, terms = canonicalize(query)
    risk = _assess_risk(query)

    if forced_area and forced_area in AREA_TO_DOMAIN:
        domain = AREA_TO_DOMAIN[forced_area]
        return QueryIntelligence(
            domain=domain,
            agent=agent_name_for(domain),
            canonical_query=canonical,
            must_terms=terms,
            metadata_filters={"area_rh": forced_area},
            risk_level=risk,
            confidence=1.0,
            fallback_required=False,
        )

    scores = _score_domains(query)
    if not scores:
        # Nenhum domínio reconhecido: fallback para busca ampla.
        return QueryIntelligence(
            domain=Domain.TRABALHISTA,
            agent=agent_name_for(Domain.TRABALHISTA),
            canonical_query=canonical,
            must_terms=terms,
            metadata_filters={},
            risk_level=risk,
            confidence=0.0,
            fallback_required=True,
        )

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_domain, top_score = ranked[0]
    total = sum(scores.values())
    confidence = top_score / total

    secondary: Domain | None = None
    if len(ranked) > 1:
        second_domain, second_score = ranked[1]
        if second_score / top_score >= settings.multidomain_ratio:
            secondary = second_domain

    fallback = confidence < settings.classification_min_confidence
    return QueryIntelligence(
        domain=top_domain,
        agent=agent_name_for(top_domain),
        canonical_query=canonical,
        must_terms=terms,
        metadata_filters={"area_rh": DOMAIN_TO_AREA[top_domain]},
        risk_level=risk,
        confidence=round(confidence, 3),
        fallback_required=fallback,
        secondary_domain=secondary,
    )
