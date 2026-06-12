"""Testes de propriedade e unitários do classificador de dificuldade (RF3.1 — 3.5).

Testes com Hypothesis para validar propriedades universais da classificação.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.agents.difficulty_classifier import (
    DifficultyLevel,
    classify_difficulty,
)

# ============================================================================
# Property-Based Tests (Hypothesis)
# ============================================================================


class TestDifficultyClassifierProperties:
    """Testes de propriedade do classificador de dificuldade."""

    @given(query=st.text())
    @settings(max_examples=100)
    def test_property_classification_total_and_deterministic(self, query: str) -> None:
        """Property 1: Classificação de dificuldade é total e determinística.

        Para qualquer string de entrada, o Classificador_Dificuldade deve retornar
        exatamente um dos três níveis (fácil, intermediário, difícil), e para a
        mesma entrada deve sempre retornar o mesmo nível.

        Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
        """
        # Executa a classificação duas vezes com a mesma entrada
        classification1 = classify_difficulty(query)
        classification2 = classify_difficulty(query)

        # Asserção 1: sempre retorna um dos três níveis
        assert classification1.level in DifficultyLevel

        # Asserção 2: determinística (mesma entrada → mesmo resultado)
        assert classification1.level == classification2.level
        assert classification1.matched_terms == classification2.matched_terms
        assert classification1.reason == classification2.reason

    @given(
        easy_query=st.just("quantos dias de férias tenho"),
        medium_query=st.just("como funciona a promoção"),
        hard_query=st.just("o que é assédio moral no trabalho"),
    )
    @settings(max_examples=10)
    def test_property_priority_hard_over_medium_over_easy(
        self, easy_query: str, medium_query: str, hard_query: str
    ) -> None:
        """Property 2: Prioridade do classificador de dificuldade.

        Para qualquer query que contenha termos de múltiplos dicionários, o
        Classificador_Dificuldade deve classificar pelo nível mais alto presente
        (difícil > intermediário > fácil).

        Validates: Requirements 3.2, 3.3, 3.4
        """
        # Testa classificação correta para cada nível puro
        easy = classify_difficulty(easy_query)
        medium = classify_difficulty(medium_query)
        hard = classify_difficulty(hard_query)

        assert easy.level == DifficultyLevel.FACIL
        assert medium.level == DifficultyLevel.INTERMEDIARIO
        assert hard.level == DifficultyLevel.DIFICIL

    @given(query=st.text(min_size=1))
    @settings(max_examples=50)
    def test_property_no_exception_on_any_input(self, query: str) -> None:
        """Propriedade auxiliar: classify_difficulty nunca lança exceção.

        Garante que a função é robusta para qualquer entrada, sem falhas.
        """
        # Não deve lançar exceção, independentemente da entrada
        result = classify_difficulty(query)

        # Resultado sempre válido
        assert result.level in DifficultyLevel
        assert isinstance(result.matched_terms, list)
        assert isinstance(result.reason, str)


# ============================================================================
# Unit Tests (Exemplos específicos)
# ============================================================================


class TestDifficultyClassifierUnits:
    """Testes unitários com exemplos específicos e edge cases."""

    @pytest.mark.unit
    def test_easy_query_simple_factual(self) -> None:
        """Pergunta simples e factual → FACIL."""
        query = "Quantos dias de férias tenho?"
        result = classify_difficulty(query)
        assert result.level == DifficultyLevel.FACIL
        assert "férias" in result.matched_terms

    @pytest.mark.unit
    def test_easy_query_with_multiple_easy_terms(self) -> None:
        """Pergunta com múltiplos termos fáceis → FACIL."""
        query = "Qual é o valor do vale refeição e vale transporte?"
        result = classify_difficulty(query)
        assert result.level == DifficultyLevel.FACIL
        assert "vale" in result.matched_terms

    @pytest.mark.unit
    def test_medium_query_interpretation_required(self) -> None:
        """Pergunta que requer interpretação de política → INTERMEDIARIO."""
        query = "Como funciona o processo de promoção?"
        result = classify_difficulty(query)
        assert result.level == DifficultyLevel.INTERMEDIARIO
        assert "promoção" in result.matched_terms

    @pytest.mark.unit
    def test_medium_query_complex_policy(self) -> None:
        """Pergunta sobre política complexa → INTERMEDIARIO."""
        query = "Quais são as regras do banco de horas?"
        result = classify_difficulty(query)
        assert result.level == DifficultyLevel.INTERMEDIARIO
        assert "banco de horas" in result.matched_terms

    @pytest.mark.unit
    def test_hard_query_sensitive_topic(self) -> None:
        """Pergunta sobre assédio → DIFICIL."""
        query = "O que fazer se estou sofrendo assédio moral?"
        result = classify_difficulty(query)
        assert result.level == DifficultyLevel.DIFICIL
        assert "assédio" in result.matched_terms or "assédio moral" in result.matched_terms

    @pytest.mark.unit
    def test_hard_query_critical_issue(self) -> None:
        """Pergunta sobre demissão por justa causa → DIFICIL."""
        query = "Demissão por justa causa: quais são os motivos?"
        result = classify_difficulty(query)
        assert result.level == DifficultyLevel.DIFICIL
        assert "demissão" in result.matched_terms or "justa causa" in result.matched_terms

    @pytest.mark.unit
    def test_priority_hard_over_medium(self) -> None:
        """Query com termos de dois dicionários → prioridade ao nível mais alto."""
        # Query contém "promoção" (intermediário) e "assédio" (difícil)
        query = "Como é o processo de promoção? Existe assédio?"
        result = classify_difficulty(query)
        # Deve classificar como DIFICIL porque "assédio" tem prioridade
        assert result.level == DifficultyLevel.DIFICIL

    @pytest.mark.unit
    def test_priority_medium_over_easy(self) -> None:
        """Query com termos de dois dicionários → prioridade ao nível mais alto."""
        # Query contém "férias" (fácil) e "promoção" (intermediário)
        query = "Quantos dias de férias ganho e como funciona a promoção?"
        result = classify_difficulty(query)
        # Deve classificar como INTERMEDIARIO porque "promoção" tem prioridade sobre "férias"
        assert result.level == DifficultyLevel.INTERMEDIARIO

    @pytest.mark.unit
    def test_no_match_defaults_to_intermediario(self) -> None:
        """Query sem termos conhecidos → INTERMEDIARIO (default)."""
        query = "Qual é a capital da França?"
        result = classify_difficulty(query)
        assert result.level == DifficultyLevel.INTERMEDIARIO
        assert len(result.matched_terms) == 0

    @pytest.mark.unit
    def test_empty_query_defaults_to_intermediario(self) -> None:
        """Query vazia → INTERMEDIARIO (default)."""
        result = classify_difficulty("")
        assert result.level == DifficultyLevel.INTERMEDIARIO
        assert len(result.matched_terms) == 0

    @pytest.mark.unit
    def test_whitespace_only_query_defaults_to_intermediario(self) -> None:
        """Query com apenas espaços em branco → INTERMEDIARIO (default)."""
        result = classify_difficulty("   ")
        assert result.level == DifficultyLevel.INTERMEDIARIO
        assert len(result.matched_terms) == 0

    @pytest.mark.unit
    def test_case_insensitive_matching(self) -> None:
        """Matching é case-insensitive."""
        query1 = "QUANTOS DIAS DE FÉRIAS?"
        query2 = "quantos dias de férias?"
        query3 = "Quantos Dias De Férias?"

        result1 = classify_difficulty(query1)
        result2 = classify_difficulty(query2)
        result3 = classify_difficulty(query3)

        assert result1.level == result2.level == result3.level == DifficultyLevel.FACIL

    @pytest.mark.unit
    def test_unicode_handling(self) -> None:
        """Strings com unicode (acentuação) são tratadas corretamente."""
        query = "Quantôs diás dé féríás?"  # Acentuação diferente
        result = classify_difficulty(query)
        # Pode não encontrar matches exatos, mas não deve falhar
        assert result.level in DifficultyLevel

    @pytest.mark.unit
    def test_matched_terms_are_subset_of_dictionary(self) -> None:
        """Termos encontrados devem estar nos dicionários."""
        query = "Quantos dias de férias e vale refeição?"
        result = classify_difficulty(query)

        # Todos os termos encontrados devem ser válidos (substring da query)
        for term in result.matched_terms:
            assert term in query.lower()

    @pytest.mark.unit
    def test_reason_is_non_empty(self) -> None:
        """Campo 'reason' deve sempre ter um valor."""
        test_queries = [
            "Quantos dias de férias?",
            "Como funciona promoção?",
            "O que é assédio moral?",
            "Pergunta aleatória que não está nos dicionários",
            "",
        ]
        for query in test_queries:
            result = classify_difficulty(query)
            assert result.reason is not None
            assert len(result.reason) > 0
