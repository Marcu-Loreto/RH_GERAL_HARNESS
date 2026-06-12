"""Geração de resposta com evidência (RF1.6).

A interface ``AnswerGenerator`` desacopla o pipeline do gerador concreto. O
padrão é o ``ExtractiveAnswerGenerator``: monta a resposta a partir dos chunks
recuperados, sem LLM — determinístico, sem custo e sem alucinação por
construção. Um gerador baseado em LLM pode ser plugado depois mantendo a mesma
interface e as mesmas regras de evidência (PROMPTS_AND_POLICIES §2).
"""

from __future__ import annotations

from typing import Protocol

from app.core.models import Answer, Confidence, Evidence
from app.guardrails.policies import no_evidence_response
from app.retrieval.vector_store import ScoredChunk


class AnswerGenerator(Protocol):
    """Contrato de um gerador de resposta."""

    def generate(self, query: str, chunks: list[ScoredChunk]) -> Answer:
        """Gera uma resposta fundamentada nos ``chunks`` recuperados."""
        ...


def _confidence_from_score(score: float) -> Confidence:
    """Mapeia o melhor score de relevância para um nível de confiança."""
    if score >= 0.5:
        return Confidence.ALTA
    if score >= 0.2:
        return Confidence.MEDIA
    return Confidence.BAIXA


class ExtractiveAnswerGenerator:
    """Gera respostas extrativas a partir dos trechos recuperados."""

    def __init__(self, max_excerpt_chars: int = 320) -> None:
        self._max_excerpt_chars = max_excerpt_chars

    def generate(self, query: str, chunks: list[ScoredChunk]) -> Answer:
        if not chunks:
            return Answer(
                answer=no_evidence_response(),
                evidence=[],
                confidence=Confidence.BAIXA,
                limitations="Nenhum documento aprovado e vigente foi encontrado para a consulta.",
                requires_human_review=False,
            )

        evidence: list[Evidence] = []
        excerpts: list[str] = []
        for item in chunks:
            chunk = item.chunk
            excerpt = self._excerpt(chunk.text)
            excerpts.append(f"- {excerpt} (fonte: {chunk.title} v{chunk.version})")
            evidence.append(
                Evidence(
                    source_id=chunk.source_id,
                    title=chunk.title,
                    version=chunk.version,
                    chunk_id=chunk.chunk_id,
                    summary=excerpt,
                )
            )

        body = "Com base nos documentos oficiais consultados:\n" + "\n".join(excerpts)
        best_score = chunks[0].score
        return Answer(
            answer=body,
            evidence=evidence,
            confidence=_confidence_from_score(best_score),
            limitations=(
                "Resposta baseada exclusivamente nos trechos recuperados. "
                "Para casos específicos, confirme com o RH responsável."
            ),
            requires_human_review=False,
        )

    def _excerpt(self, text: str) -> str:
        clean = " ".join(text.split())
        if len(clean) <= self._max_excerpt_chars:
            return clean
        return clean[: self._max_excerpt_chars].rstrip() + "…"
