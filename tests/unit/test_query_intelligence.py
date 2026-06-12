"""Testes unitários da Query Intelligence Layer (RF2.1, RF2.2, RF2.4)."""

from __future__ import annotations

import pytest

from app.agents.query_intelligence import (
    Domain,
    RiskLevel,
    canonicalize,
    classify,
    is_known_area,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("quantos dias de férias eu tenho?", Domain.BENEFICIOS),
        ("qual o prazo do banco de horas?", Domain.TRABALHISTA),
        ("como funciona a promoção e a faixa salarial?", Domain.CARGOS_SALARIOS),
        ("tem reembolso de curso e certificação?", Domain.TREINAMENTO),
        ("como é o processo seletivo da vaga?", Domain.RECRUTAMENTO),
        ("como faço uma denúncia de assédio no canal de ética?", Domain.COMPLIANCE),
    ],
)
def test_classifies_domain(question: str, expected: Domain) -> None:
    intel = classify(question)
    assert intel.domain == expected
    assert intel.agent == f"agente_{expected.value}"


@pytest.mark.unit
def test_canonical_query_removes_stopwords() -> None:
    canonical, terms = canonicalize("quantos dias de férias eu tenho?")
    assert "de" not in terms
    assert "férias" in canonical
    assert "dias" in terms


@pytest.mark.unit
def test_must_terms_are_extracted() -> None:
    intel = classify("qual a política de banco de horas?")
    assert "banco" in intel.must_terms
    assert "horas" in intel.must_terms


@pytest.mark.unit
def test_fallback_when_no_domain() -> None:
    intel = classify("bom dia, tudo bem com você?")
    assert intel.fallback_required is True
    assert intel.confidence == 0.0


@pytest.mark.unit
def test_forced_area_overrides_classification() -> None:
    intel = classify("qualquer pergunta vaga", forced_area="beneficios")
    assert intel.domain == Domain.BENEFICIOS
    assert intel.confidence == 1.0
    assert intel.metadata_filters == {"area_rh": "beneficios"}


@pytest.mark.unit
def test_high_risk_detected() -> None:
    intel = classify("como funciona a demissão por justa causa?")
    assert intel.risk_level == RiskLevel.ALTO


@pytest.mark.unit
def test_metadata_filters_map_domain_to_area() -> None:
    intel = classify("como faço uma denúncia de assédio?")
    assert intel.metadata_filters["area_rh"] == "compliance"


@pytest.mark.unit
def test_multidomain_sets_secondary_domain() -> None:
    # Pergunta cobrindo trabalhista (jornada) e compliance (assédio).
    intel = classify("política de jornada de trabalho e denúncia de assédio")
    assert intel.secondary_domain is not None
    assert intel.domain != intel.secondary_domain


@pytest.mark.unit
def test_low_confidence_flags_fallback() -> None:
    # Um único termo de domínio entre muitos tokens → confiança baixa.
    intel = classify("gostaria de saber sobre o processo seletivo por favor")
    assert intel.domain == Domain.RECRUTAMENTO
    assert 0.0 < intel.confidence <= 1.0


@pytest.mark.unit
def test_unknown_area_is_rejected_by_is_known_area() -> None:
    assert is_known_area("beneficios") is True
    assert is_known_area("inexistente") is False


@pytest.mark.unit
def test_forced_unknown_area_falls_back_to_classification() -> None:
    # Área inexistente é ignorada (fallback para classificação por palavras-chave).
    intel = classify("quantos dias de férias eu tenho?", forced_area="inexistente")
    assert intel.domain == Domain.BENEFICIOS
    # Não usa o atalho de forced_area: o filtro de metadados vem da classificação.
    assert intel.metadata_filters == {"area_rh": "beneficios"}


@pytest.mark.unit
@pytest.mark.parametrize(
    "area",
    ["beneficios", "politicas", "cargos_salarios", "treinamento", "recrutamento", "compliance"],
)
def test_all_six_areas_are_known(area: str) -> None:
    assert is_known_area(area) is True
