"""Interface para avaliação semântica (EVALUATION_HARNESS §5).

Este módulo fornece:
- ``SemanticJudge``: protocolo para avaliadores semânticos plugáveis
- ``ExtractiveSemanticJudge``: juiz extrativo padrão (determinístico, sem custo)
- ``LLMAsJudge``: evaluator semântico usando LLM-as-judge para avaliar:
  - Faithfulness: a resposta está fiel às evidências?
  - Citation accuracy: as fontes citadas são relevantes e corretas?
  - Tom apropriado: o tom da resposta é adequado?
  - Citação de fontes: cited fontes quando necessário?

O LLM-as-judge usa o modelo econômico (minimax-m2.5) para minimizar custos.
"""

from __future__ import annotations

from typing import Protocol

from app.core.models import Answer

# Re-export para compatibilidade
from app.core.models import Evidence


class SemanticJudge(Protocol):
    """Contrato de um avaliador semântico de fidelidade e citação.

    Implementações futuras (LLM-as-judge, embeddings) devem respeitar este
    contrato para serem plugáveis no Evaluation Harness sem alterar o fluxo.
    """

    def faithfulness(self, question: str, answer: Answer) -> float:
        """Grau de fidelidade da resposta às evidências (0..1)."""
        ...

    def citation_accuracy(self, answer: Answer, expected_sources: list[str]) -> float:
        """Acurácia das citações frente às fontes esperadas (0..1)."""
        ...


class ExtractiveSemanticJudge:
    """Juiz padrão extrativo, determinístico e sem custo (placeholder).

    Mantém a semântica atual do harness; serve como implementação de referência
    e ponto de extensão para um juiz semântico real no futuro.
    """

    def faithfulness(self, question: str, answer: Answer) -> float:
        return 1.0 if answer.evidence else 0.0

    def citation_accuracy(self, answer: Answer, expected_sources: list[str]) -> float:
        cited = [e.source_id for e in answer.evidence]
        if not expected_sources:
            return 1.0
        if not cited:
            return 0.0
        in_set = sum(1 for s in cited if s in expected_sources)
        return in_set / len(cited)


class LLMAsJudge:
    """Avaliador semântico usando LLM-as-judge.

    Usa o modelo econômico (minimax-m2.5) para avaliar:
    - Faithfulness: a resposta está fiel às evidências recuperadas?
    - Citation accuracy: as fontes citadas são relevantes para a pergunta?
    - Tone appropriateness: o tom da resposta é profissional e adequado?
    - Source citation needed: a resposta deveria citar fontes?

    Custo: ~0 tokens (modelo econômico) por avaliação.
    """

    def __init__(self, llm_client=None):
        """Inicializa o avaliador com cliente LLM opcional (para injeção em testes)."""
        self._llm = llm_client

    def _get_llm(self):
        """Lazy load do cliente LLM para evitar import circular."""
        if self._llm is None:
            from langchain_openai import ChatOpenAI
            import os

            # Usa o modelo econômico configurado
            self._llm = ChatOpenAI(
                model="minimax-m2.5",
                base_url=os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1"),
                api_key=os.getenv("MINIMAX_API_KEY"),
                temperature=0.0,
            )
        return self._llm

    def faithfulness(self, question: str, answer: Answer) -> float:
        """Avalia se a resposta está fiel às evidências.

        Prompt guiding:
        - Resposta baseada nos fatos das evidências?
        - Não adiciona informações não presentes nas fontes?
        - Interpretação correta do contexto?
        """
        if not answer.evidence:
            return 0.0

        # Contexto das evidências
        evidence_texts = "\n".join(
            f"- {e.title} (ID: {e.source_id}): {e.summary or 'sem resumo'}"
            for e in answer.evidence
        )

        prompt = f"""Você é um avaliador de qualidade de respostas. Avalie quão fiel a resposta está às evidências fornecidas.

Pergunta: {question}

Evidências recuperadas:
{evidence_texts}

Resposta gerada:
{answer.answer}

Avalie a fidelidade em uma escala de 0 a 1, onde:
- 1.0 = resposta perfeitamente fiel, baseada apenas nas evidências
- 0.5 = resposta parcialmente fiel, com algumas inferências razoveis
- 0.0 = resposta não fiel, contradiz as evidências ou adiciona informações falsas

Responda APENAS com um número entre 0 e 1 (ex: 0.85)."""

        try:
            llm = self._get_llm()
            result = llm.invoke(prompt)
            score = float(result.content.strip())
            return max(0.0, min(1.0, score))
        except Exception:
            # Fallback parajuiz extrativo em caso de erro
            return 1.0 if answer.evidence else 0.0

    def citation_accuracy(self, answer: Answer, expected_sources: list[str]) -> float:
        """Avalia se as fontes citadas são relevantes e corretas.

        Verifica:
        - Fuentes citadas realmente existem no contexto?
        - As citações são relevantes para a pergunta?
        - Não cita fontes fora do conjunto esperado (quando fornecido)?
        """
        if not answer.evidence:
            return 0.0

        cited = [e.source_id for e in answer.evidence]

        # Se temos fontes esperadas, verifica se as citadas estão no conjunto
        if expected_sources:
            correct = sum(1 for s in cited if s in expected_sources)
            return correct / len(cited) if cited else 0.0

        # Avaliação sem conjunto esperado: usa LLM para verificar relevância
        prompt = f"""Você é um avaliador de qualidade de citações. Avalie se as fontes citadas são relevantes para a pergunta.

Resposta gerada:
{answer.answer}

Fontes citadas (IDs):
{', '.join(cited)}

Avalie a acurácia das citações em uma escala de 0 a 1, onde:
- 1.0 = todas as fontes são relevantes e suportam a resposta
- 0.5 = algumas fontes são relevantes
- 0.0 = fontes não são relevantes ou são incorretas

Responda APENAS com um número entre 0 e 1 (ex: 0.85)."""

        try:
            llm = self._get_llm()
            result = llm.invoke(prompt)
            score = float(result.content.strip())
            return max(0.0, min(1.0, score))
        except Exception:
            # Fallback: se há evidências, assume que são relevantes
            return 1.0 if answer.evidence else 0.0

    def tone_appropriateness(self, answer: Answer) -> float:
        """Avalia se o tom da resposta é profissional e adequado.

        O tom deve ser:
        - Formal mas acessível (pt-BR)
        - Respeitoso
        - Claro e objetivo
        """
        prompt = f"""Você é um avaliador de tom de respostas. Avalie se o tom da resposta é profissional e adequado.

Resposta gerada:
{answer.answer}

Avalie o tom em uma escala de 0 a 1, onde:
- 1.0 = tom perfeito, profissional, respeitoso e claro
- 0.5 = tom aceitável, mas poderia melhorar
- 0.0 = tom inadequado, desrespeitoso ou muito informal

Responda APENAS com um número entre 0 e 1 (ex: 0.90)."""

        try:
            llm = self._get_llm()
            result = llm.invoke(prompt)
            score = float(result.content.strip())
            return max(0.0, min(1.0, score))
        except Exception:
            return 0.8  # Default conservador

    def should_cite_sources(self, question: str, answer: Answer) -> bool:
        """Determina se a resposta deveria citar fontes.

        Algumas perguntas não requerem citação (ex: opiniões gerais,
        explicações conceituais sem referência específica).
        """
        prompt = f"""Determine se a resposta abaixo deveria citar fontes documentais.

Pergunta: {question}

Resposta: {answer.answer}

Responda apenas com "SIM" ou "NÃO"."""

        try:
            llm = self._get_llm()
            result = llm.invoke(prompt)
            return "SIM" in result.content.upper()
        except Exception:
            return bool(answer.evidence)  # Default: cite se houver evidências


def get_default_judge() -> SemanticJudge:
    """Retorna o juiz padrão (extrativo). Substituível por um juiz semântico."""
    return ExtractiveSemanticJudge()


def get_llm_judge(llm_client=None) -> SemanticJudge:
    """Retorna um avaliador LLM-as-judge.

    Args:
        llm_client: Cliente LLM opcional (para injeção em testes).
    """
    return LLMAsJudge(llm_client)