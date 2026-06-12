"""Teste de integração de pergunta multidomínio (SPEC Fase 2 §7, RF2.5)."""

from __future__ import annotations

import pytest

from app.agents.orchestrator import Orchestrator
from app.core.models import Confidentiality
from app.evaluation.golden import CorpusEntry
from app.ingestion.service import IngestionService
from app.retrieval.retriever import Retriever
from app.retrieval.vector_store import InMemoryVectorStore

_INTERNAL = [Confidentiality.PUBLICO, Confidentiality.INTERNO]


def _store_with_only_area(corpus: list[CorpusEntry], area: str) -> InMemoryVectorStore:
    store = InMemoryVectorStore()
    service = IngestionService(store=store, max_chars=800, overlap_chars=100)
    for entry in corpus:
        if entry.document.area_rh == area and entry.document.is_indexable():
            service.ingest(entry.document, entry.raw_text)
    return store


@pytest.mark.integration
def test_multidomain_invokes_auxiliary_when_primary_has_no_evidence(
    corpus: list[CorpusEntry],
) -> None:
    # Store contém apenas documentos de compliance: o domínio primário
    # (trabalhista) não terá evidência, acionando o agente auxiliar.
    store = _store_with_only_area(corpus, "compliance")
    orchestrator = Orchestrator(Retriever(store=store))

    decision = orchestrator.route(
        "política de jornada de trabalho e denúncia de assédio", _INTERNAL
    )

    assert decision.agent_used == "agente_trabalhista"
    assert decision.auxiliary_agent == "agente_compliance"
    assert decision.agents_invoked == ["agente_trabalhista", "agente_compliance"]
    assert "auxiliar" in decision.reason
    # A evidência final veio do domínio auxiliar (compliance).
    assert {c.chunk.area_rh for c in decision.chunks} == {"compliance"}
