"""Configuração da aplicação via variáveis de ambiente.

As configurações são acessadas exclusivamente por ``get_settings()`` (singleton
cacheado). Nunca importe variáveis de ambiente diretamente em outros módulos —
isso mantém a configuração centralizada, testável e por ambiente (RF0.2).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação carregadas do ambiente / arquivo ``.env``.

    Nenhum valor padrão contém segredo real. Em produção, ``secret_key`` deve
    ser sempre sobrescrito por variável de ambiente.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Identificação e ambiente
    app_name: str = "rh-geral-harness"
    environment: Literal["dev", "staging", "prod"] = "dev"
    debug: bool = True

    # API
    api_v1_prefix: str = "/api/v1"

    # Persistência de metadados (SQLite em dev)
    database_url: str = "sqlite:///./rh_harness.db"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_json: bool = True

    # Retrieval / RAG (Fase 1)
    embedding_dim: int = 256
    retrieval_top_k: int = 5
    # Peso da similaridade densa na busca híbrida (0..1); o restante é lexical.
    hybrid_dense_weight: float = 0.4
    # Score mínimo absoluto para um chunk ser considerado evidência relevante.
    min_relevance_score: float = 0.12
    # Corte relativo: descarta chunks com score abaixo de ratio * melhor_score.
    relevance_ratio: float = 0.5
    # Estratégia de chunking
    chunk_max_chars: int = 800
    chunk_overlap_chars: int = 100

    # Orquestração multiagente (Fase 2)
    # Confiança mínima da classificação; abaixo disso aciona fallback.
    classification_min_confidence: float = 0.34
    # Razão (segundo/primeiro score) para acionar agente auxiliar (multidomínio).
    multidomain_ratio: float = 0.6

    # Harness completo (Fase 3)
    # Estratégia de seleção de modelo: 'auto' decide por risco/confiança; os
    # demais forçam um tier fixo (útil para testes e contenção de custo).
    model_selection_strategy: Literal["auto", "economico", "intermediario", "robusto"] = "auto"
    # Orçamento máximo de custo estimado (USD) por resposta antes de degradar
    # contexto / preferir cache (RF3.5 / regra de roteamento §4).
    cost_budget_per_answer: float = 0.05
    # Cache semântico (RF3.4)
    cache_enabled: bool = True
    # Similaridade mínima (cosseno) para considerar duas perguntas equivalentes.
    cache_similarity_threshold: float = 0.92
    # Diretório do prompt registry versionado (RF3.7).
    prompt_registry_dir: str = "prompts"
    # Confiança de roteamento abaixo da qual a resposta é escalada (RF3.6).
    human_review_min_confidence: float = 0.34
    # URL do portal de chamados do RH — usada no fallback quando não há resposta
    # na base ou quando o usuário precisa de atendimento humano/dado restrito.
    support_ticket_url: str = "https://jira.cpqd.com.br/servicedesk/customer/portal/27"

    # ── Configurações de Modelo LLM ──────────────────────────────────────────
    # Modelos por nível de dificuldade (configuráveis via .env)
    model_economico: str = "gpt-4o-mini"
    model_intermediario: str = "gpt-4o-mini"
    model_robusto: str = "gpt-4o"
    # Temperatura da geração (0.0 = mais factual, 1.0 = mais criativo)
    model_temperature: float = 0.3
    # Usar LLM para geração de respostas (True) ou extrativo (False)
    use_llm_generator: bool = True

    # Segurança (placeholder — sem segredo real versionado)
    secret_key: str = Field(
        default="change-me-in-production",
        description="Chave de assinatura. DEVE ser sobrescrita em produção.",
    )

    # Rate limiting (RF4.5 / hardening segurança)
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst: int = 10

    # CORS
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8501"],
        description="Origens permitidas para CORS. Em produção, restringir a domínios específicos.",
    )

    # Security headers
    security_headers_enabled: bool = True

    @property
    def is_production(self) -> bool:
        """Retorna ``True`` quando o ambiente é de produção."""
        return self.environment == "prod"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna a instância única (cacheada) das configurações."""
    return Settings()
