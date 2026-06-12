"""Testes unitários do cache semântico (RF3.4)."""

from __future__ import annotations

import pytest

from app.cache.semantic_cache import SemanticCache
from app.core.models import Answer, Confidence, Confidentiality, Evidence
from app.retrieval.embeddings import get_embedding_provider


def _answer() -> Answer:
    return Answer(
        answer="Você tem direito a 30 dias de férias.",
        evidence=[Evidence(source_id="ben-ferias-001", title="Férias", version="1", chunk_id="c1")],
        confidence=Confidence.ALTA,
    )


def _embed(text: str) -> list[float]:
    return get_embedding_provider().embed(text)


@pytest.mark.unit
def test_cache_hit_for_equivalent_query() -> None:
    cache = SemanticCache(similarity_threshold=0.9)
    q = "quantos dias de férias eu tenho"
    cache.store(
        q,
        _embed(q),
        _answer(),
        domain="beneficios",
        required_confidentiality=frozenset({"interno"}),
        document_versions={"ben-ferias-001": "1"},
    )

    result = cache.lookup(
        _embed(q),
        domain="beneficios",
        allowed_confidentiality=[Confidentiality.PUBLICO, Confidentiality.INTERNO],
        current_versions={"ben-ferias-001": "1"},
    )
    assert result.hit is True
    assert result.answer is not None


@pytest.mark.unit
def test_cache_miss_for_unrelated_query() -> None:
    cache = SemanticCache(similarity_threshold=0.9)
    q = "quantos dias de férias eu tenho"
    cache.store(
        q,
        _embed(q),
        _answer(),
        domain="beneficios",
        required_confidentiality=frozenset({"interno"}),
        document_versions={"ben-ferias-001": "1"},
    )

    result = cache.lookup(
        _embed("como funciona o processo seletivo de vagas"),
        domain="beneficios",
        allowed_confidentiality=[Confidentiality.INTERNO],
        current_versions={"ben-ferias-001": "1"},
    )
    assert result.hit is False


@pytest.mark.unit
def test_cache_miss_for_different_domain() -> None:
    cache = SemanticCache(similarity_threshold=0.9)
    q = "quantos dias de férias eu tenho"
    cache.store(
        q,
        _embed(q),
        _answer(),
        domain="beneficios",
        required_confidentiality=frozenset({"interno"}),
        document_versions={"ben-ferias-001": "1"},
    )

    result = cache.lookup(
        _embed(q),
        domain="trabalhista",
        allowed_confidentiality=[Confidentiality.INTERNO],
        current_versions={"ben-ferias-001": "1"},
    )
    assert result.hit is False
    assert result.reason == "miss"


@pytest.mark.unit
def test_cache_respects_permission() -> None:
    cache = SemanticCache(similarity_threshold=0.9)
    q = "política confidencial de desligamento"
    cache.store(
        q,
        _embed(q),
        _answer(),
        domain="beneficios",
        required_confidentiality=frozenset({"confidencial"}),
        document_versions={"ben-ferias-001": "1"},
    )

    result = cache.lookup(
        _embed(q),
        domain="beneficios",
        allowed_confidentiality=[Confidentiality.PUBLICO, Confidentiality.INTERNO],
        current_versions={"ben-ferias-001": "1"},
    )
    assert result.hit is False
    assert result.reason == "permissao_incompativel"


@pytest.mark.unit
def test_cache_invalidated_by_document_version_on_lookup() -> None:
    cache = SemanticCache(similarity_threshold=0.9)
    q = "quantos dias de férias eu tenho"
    cache.store(
        q,
        _embed(q),
        _answer(),
        domain="beneficios",
        required_confidentiality=frozenset({"interno"}),
        document_versions={"ben-ferias-001": "1"},
    )

    result = cache.lookup(
        _embed(q),
        domain="beneficios",
        allowed_confidentiality=[Confidentiality.INTERNO],
        current_versions={"ben-ferias-001": "2"},
    )
    assert result.hit is False
    assert result.reason == "documento_desatualizado"


@pytest.mark.unit
def test_invalidate_by_document_removes_stale_entries() -> None:
    cache = SemanticCache(similarity_threshold=0.9)
    q = "quantos dias de férias eu tenho"
    cache.store(
        q,
        _embed(q),
        _answer(),
        domain="beneficios",
        required_confidentiality=frozenset({"interno"}),
        document_versions={"ben-ferias-001": "1"},
    )

    removed = cache.invalidate_by_document("ben-ferias-001", new_version="2")
    assert removed == 1
    assert len(cache) == 0


@pytest.mark.unit
def test_bypass_reason_for_pii() -> None:
    from app.agents.query_intelligence import RiskLevel
    from app.cache.semantic_cache import cache_bypass_reason

    assert (
        cache_bypass_reason(has_pii=True, risk_level=RiskLevel.BAIXO, requires_human_review=False)
        == "pii_detectada"
    )


@pytest.mark.unit
def test_bypass_reason_for_high_risk() -> None:
    from app.agents.query_intelligence import RiskLevel
    from app.cache.semantic_cache import cache_bypass_reason

    assert (
        cache_bypass_reason(has_pii=False, risk_level=RiskLevel.ALTO, requires_human_review=False)
        == "risco_alto"
    )


@pytest.mark.unit
def test_bypass_reason_for_human_review() -> None:
    from app.agents.query_intelligence import RiskLevel
    from app.cache.semantic_cache import cache_bypass_reason

    assert (
        cache_bypass_reason(has_pii=False, risk_level=RiskLevel.BAIXO, requires_human_review=True)
        == "revisao_humana_obrigatoria"
    )


@pytest.mark.unit
def test_no_bypass_for_safe_context() -> None:
    from app.agents.query_intelligence import RiskLevel
    from app.cache.semantic_cache import cache_bypass_reason

    assert (
        cache_bypass_reason(has_pii=False, risk_level=RiskLevel.BAIXO, requires_human_review=False)
        is None
    )
