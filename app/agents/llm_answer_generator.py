"""Geração de resposta com LLM (versão completa).

Este gerador usa LLMs para sintetizar respostas a partir dos chunks recuperados,
oferecendo respostas mais naturais e contextuais comparado ao gerador extrativo.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.models import Answer, Confidence, Evidence
from app.guardrails.policies import NO_EVIDENCE_RESPONSE
from app.retrieval.vector_store import ScoredChunk

if TYPE_CHECKING:
    from langchain_openai import ChatOpenAI

logger = get_logger(__name__)

# Prompt base para geração de respostas
ANSWER_PROMPT = """Você é um assistente de RH da empresa. Responda a pergunta do colaborador
usando exclusivamente as informações fornecidas nos documentos abaixo.

Requisitos:
- Responda em português brasileiro
- Sea claro e objetivo
- Cite as fontes quando possível
- Se não houver informação suficiente, diga que não sabe

Documentos:
{context}

Pergunta: {question}

Resposta:"""


def _get_llm(model_name: str, temperature: float = 0.3) -> "ChatOpenAI":
    """Retorna instância do LLM configurado."""
    from langchain_openai import ChatOpenAI

    settings = get_settings()

    # Configura a API key baseada no modelo
    if "minimax" in model_name.lower():
        api_key = getattr(settings, "minimax_api_key", None) or "dummy"
        base_url = "https://api.minimax.chat/v1"
    else:
        api_key = getattr(settings, "openai_api_key", None) or "dummy"
        base_url = None

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
    )


def _build_context(chunks: list[ScoredChunk]) -> str:
    """Constrói o contexto a partir dos chunks recuperados."""
    if not chunks:
        return "Nenhum documento encontrado."

    context_parts = []
    for item in chunks:
        chunk = item.chunk
        context_parts.append(
            f"[{chunk.title} v{chunk.version}]\n{chunk.text}\n"
        )
    return "\n---\n".join(context_parts)


def _confidence_from_score(score: float) -> Confidence:
    """Mapeia o score de relevância para nível de confiança."""
    if score >= 0.5:
        return Confidence.ALTA
    if score >= 0.2:
        return Confidence.MEDIA
    return Confidence.BAIXA


class LLMAnswerGenerator:
    """Gera respostas usando LLMs a partir dos chunks recuperados."""

    def __init__(
        self,
        max_excerpt_chars: int = 2000,
        temperature: float | None = None,
    ) -> None:
        self._max_excerpt_chars = max_excerpt_chars
        settings = get_settings()
        self._temperature = temperature or settings.model_temperature

    def generate(self, query: str, chunks: list[ScoredChunk], model_name: str | None = None) -> Answer:
        """Gera uma resposta fundamentada usando LLM."""
        if not chunks:
            return Answer(
                answer=NO_EVIDENCE_RESPONSE,
                evidence=[],
                confidence=Confidence.BAIXA,
                limitations="Nenhum documento aprovado e vigente foi encontrado para a consulta.",
                requires_human_review=False,
            )

        settings = get_settings()

        # Determina qual modelo usar
        if model_name is None:
            # Usa config do .env - primeiro tenta economico
            model_name = getattr(settings, "model_economico", "gpt-4o-mini")

        logger.info("llm_generation_start", model=model_name, chunks=len(chunks))

        try:
            # Prepara o contexto
            context = _build_context(chunks)
            prompt = ANSWER_PROMPT.format(context=context, question=query)

            # Chama o LLM
            llm = _get_llm(model_name, self._temperature)
            response = llm.invoke(prompt)
            answer_text = response.content if hasattr(response, "content") else str(response)

            # Limita o tamanho da resposta
            if len(answer_text) > self._max_excerpt_chars:
                answer_text = answer_text[:self._max_excerpt_chars].rstrip() + "..."

        except Exception as e:
            logger.error("llm_generation_error", error=str(e))
            # Fallback para o gerador extrativo em caso de erro
            return self._fallback_extrative(query, chunks)

        # Constrói a lista de evidências
        evidence: list[Evidence] = []
        for item in chunks:
            chunk = item.chunk
            evidence.append(
                Evidence(
                    source_id=chunk.source_id,
                    title=chunk.title,
                    version=chunk.version,
                    chunk_id=chunk.chunk_id,
                    summary=chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                )
            )

        best_score = chunks[0].score if chunks else 0.0

        return Answer(
            answer=answer_text,
            evidence=evidence,
            confidence=_confidence_from_score(best_score),
            limitations=(
                "Resposta gerada por IA. Para casos específicos ou situações "
                "legais, confirme com o RH responsável."
            ),
            requires_human_review=False,
        )

    def _fallback_extrative(self, query: str, chunks: list[ScoredChunk]) -> Answer:
        """Fallback para gerador extrativo em caso de erro no LLM."""
        from app.agents.answer_generator import ExtractiveAnswerGenerator

        generator = ExtractiveAnswerGenerator()
        return generator.generate(query, chunks)