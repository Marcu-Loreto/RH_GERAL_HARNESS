"""Provedores de embedding (RF1.3).

A interface ``EmbeddingProvider`` desacopla o pipeline do provedor concreto. O
padrão é o ``HashingEmbeddingProvider``: determinístico, local, sem custo e sem
dependência de chave de API — ideal para MVP, testes e CI. Um provedor baseado
em LLM/serviço externo pode ser plugado depois sem alterar o restante do código.

Qualquer alteração de modelo de embedding exige teste de regressão (TEST_STRATEGY).
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

from app.core.config import get_settings

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Tokeniza o texto em palavras minúsculas (unicode-aware)."""
    return _TOKEN_RE.findall(text.lower())


def _stable_hash(token: str, salt: str) -> int:
    """Hash estável entre processos (independente de PYTHONHASHSEED)."""
    digest = hashlib.blake2b(f"{salt}:{token}".encode(), digest_size=8).digest()
    return int.from_bytes(digest, "big")


class EmbeddingProvider(Protocol):
    """Contrato de um provedor de embeddings."""

    name: str
    dim: int

    def embed(self, text: str) -> list[float]:
        """Retorna o vetor de embedding (normalizado) para ``text``."""
        ...


class HashingEmbeddingProvider:
    """Embedding determinístico via *hashing trick* com sinal.

    Mapeia tokens para um vetor de dimensão fixa usando hashing, aplica um sinal
    estável por token e normaliza em L2. Similaridade do cosseno entre vetores
    reflete a sobreposição de vocabulário — suficiente para um MVP de baixo custo.
    """

    def __init__(self, dim: int | None = None) -> None:
        self.dim = dim or get_settings().embedding_dim
        self.name = f"hashing-{self.dim}"

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        tokens = tokenize(text)
        for token in tokens:
            bucket = _stable_hash(token, "idx") % self.dim
            sign = 1.0 if _stable_hash(token, "sign") % 2 == 0 else -1.0
            vector[bucket] += sign
        return _l2_normalize(vector)


def _l2_normalize(vector: list[float]) -> list[float]:
    """Normaliza um vetor em L2; vetor nulo é retornado inalterado."""
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector
    return [value / norm for value in vector]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calcula a similaridade do cosseno entre dois vetores de mesma dimensão."""
    if len(a) != len(b):
        raise ValueError("Vetores de dimensões diferentes.")
    return sum(x * y for x, y in zip(a, b, strict=True))


_default_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    """Retorna o provedor de embedding padrão (singleton)."""
    global _default_provider
    if _default_provider is None:
        _default_provider = HashingEmbeddingProvider()
    return _default_provider
