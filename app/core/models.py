"""Modelos de metadados do domínio (RF0.4).

Define os contratos de dados para Documento, Chunk, Usuário, Permissão, Trace e
Resposta, conforme ``DATA_MODEL_AND_METADATA.md``. Os modelos usam Pydantic v2 e
enums para garantir validação e consistência em todas as fases seguintes.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class DocumentStatus(StrEnum):
    """Ciclo de vida de um documento na base de conhecimento."""

    DRAFT = "draft"
    APPROVED = "approved"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class Confidentiality(StrEnum):
    """Nível de confidencialidade de um documento/chunk."""

    PUBLICO = "publico"
    INTERNO = "interno"
    RESTRITO = "restrito"
    CONFIDENCIAL = "confidencial"


class UserRole(StrEnum):
    """Perfis de acesso do usuário."""

    COLABORADOR = "colaborador"
    GESTOR = "gestor"
    RH = "rh"
    JURIDICO = "juridico"
    ADMIN = "admin"


class Confidence(StrEnum):
    """Nível de confiança de uma resposta gerada."""

    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"


# Campos mínimos obrigatórios para que um documento possa ser indexado
# (DATA_MODEL_AND_METADATA.md, seção 7).
REQUIRED_INDEXING_FIELDS: tuple[str, ...] = (
    "source_id",
    "title",
    "owner",
    "area_rh",
    "document_type",
    "version",
    "valid_from",
    "confidentiality",
    "language",
    "hash",
)


class DocumentMetadata(BaseModel):
    """Metadados de um documento oficial da base de conhecimento."""

    model_config = ConfigDict(use_enum_values=True)

    source_id: str
    title: str
    owner: str
    area_rh: str
    document_type: str
    version: str
    status: DocumentStatus = DocumentStatus.DRAFT
    valid_from: datetime
    valid_until: datetime | None = None
    confidentiality: Confidentiality = Confidentiality.INTERNO
    language: str = "pt-BR"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    hash: str

    def is_indexable(self) -> bool:
        """Indica se o documento atende aos critérios para indexação.

        Exige status ``approved`` e presença de todos os campos obrigatórios.
        """
        if self.status != DocumentStatus.APPROVED.value:
            return False
        return all(getattr(self, field, None) for field in REQUIRED_INDEXING_FIELDS)


class ChunkMetadata(BaseModel):
    """Metadados de um chunk derivado de um documento."""

    model_config = ConfigDict(use_enum_values=True)

    chunk_id: str
    source_id: str
    title: str
    section: str | None = None
    text: str
    token_count: int = Field(ge=0, default=0)
    embedding_model: str | None = None
    area_rh: str
    document_type: str
    version: str
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    confidentiality: Confidentiality = Confidentiality.INTERNO
    status: DocumentStatus = DocumentStatus.APPROVED
    hash: str


class User(BaseModel):
    """Usuário do sistema e seus atributos de acesso."""

    model_config = ConfigDict(use_enum_values=True)

    user_id: str
    role: UserRole
    department: str | None = None
    access_level: str | None = None
    location: str | None = None
    tenant_id: str | None = None


class Permission(BaseModel):
    """Política de acesso associada a um perfil (RBAC/ABAC)."""

    model_config = ConfigDict(use_enum_values=True)

    role: UserRole
    allowed_confidentiality: list[Confidentiality] = Field(default_factory=list)
    allowed_domains: list[str] = Field(default_factory=list)
    denied_domains: list[str] = Field(default_factory=list)
    requires_human_review: bool = False


class Evidence(BaseModel):
    """Evidência documental que sustenta uma resposta."""

    source_id: str
    title: str
    version: str
    chunk_id: str
    summary: str | None = None


class Trace(BaseModel):
    """Registro rastreável de uma interação completa (observabilidade)."""

    model_config = ConfigDict(use_enum_values=True)

    trace_id: str
    session_id: str
    user_id: str | None = None
    channel: str | None = None
    original_query: str
    canonical_query: str | None = None
    domain: str | None = None
    agent: str | None = None
    model: str | None = None
    input_tokens: int = Field(ge=0, default=0)
    output_tokens: int = Field(ge=0, default=0)
    estimated_cost: float = Field(ge=0, default=0.0)
    latency_ms: float = Field(ge=0, default=0.0)
    retrieved_chunks: list[str] = Field(default_factory=list)
    guardrails_triggered: list[str] = Field(default_factory=list)
    final_confidence: Confidence | None = None
    requires_human_review: bool = False
    created_at: datetime | None = None
    # Extensão Fase 2: explicabilidade da decisão do orquestrador (RF2.7).
    routing_confidence: float | None = None
    routing_reason: str | None = None
    agents_invoked: list[str] = Field(default_factory=list)
    # Extensão Fase 3: harness completo (RF3.1/RF3.3/RF3.4/RF3.7).
    model_tier: str | None = None
    cache_hit: bool = False
    prompt_version: str | None = None
    escalation_reason: str | None = None
    cache_bypass_reason: str | None = None
    # Enforcement de orçamento (RF3.5) e governança de risco do agente (RF2.6/RF3.6).
    budget_status: str | None = None
    budget_action: str | None = None
    screening_decision: str | None = None


class Answer(BaseModel):
    """Resposta entregue ao usuário, com evidências e limitações."""

    model_config = ConfigDict(use_enum_values=True)

    answer: str
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: Confidence = Confidence.BAIXA
    limitations: str | None = None
    requires_human_review: bool = False
    # Governança de risco propagada do agente/escalonamento (RF2.6 / RF3.6).
    screening_decision: str | None = None
    escalation_reason: str | None = None
