"""Dependências compartilhadas da API (singletons do MVP).

Mantém uma instância única do vector store, retriever, serviço de ingestão,
cache semântico, tracker FinOps e pipeline RAG. No MVP o índice é em memória; em
produção seria substituído por um Vector DB persistente sem alterar as rotas.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache

from fastapi import Depends, Header, HTTPException, status

from app.cache.semantic_cache import SemanticCache
from app.core.auth import AuthError, AuthProvider, MockAuthProvider, UserContext, can_access_route
from app.core.config import get_settings
from app.core.models import UserRole
from app.finops.cost import FinOpsTracker
from app.governance.prompt_registry import PromptRegistry
from app.ingestion.service import IngestionService
from app.rag.pipeline import RagPipeline
from app.retrieval.retriever import Retriever
from app.retrieval.vector_store import InMemoryVectorStore


@lru_cache(maxsize=1)
def get_vector_store() -> InMemoryVectorStore:
    """Retorna o vector store singleton."""
    return InMemoryVectorStore()


@lru_cache(maxsize=1)
def get_ingestion_service() -> IngestionService:
    """Retorna o serviço de ingestão singleton.

    Recebe o mesmo cache semântico do pipeline para que toda reingestão/atualização
    de documento invalide as respostas em cache baseadas na versão anterior (RF3.4).
    """
    settings = get_settings()
    cache = get_semantic_cache() if settings.cache_enabled else None
    return IngestionService(
        store=get_vector_store(),
        max_chars=settings.chunk_max_chars,
        overlap_chars=settings.chunk_overlap_chars,
        cache=cache,
    )


@lru_cache(maxsize=1)
def get_retriever() -> Retriever:
    """Retorna o retriever singleton."""
    return Retriever(store=get_vector_store())


@lru_cache(maxsize=1)
def get_finops_tracker() -> FinOpsTracker:
    """Retorna o tracker FinOps singleton (relatório de custo)."""
    return FinOpsTracker()


@lru_cache(maxsize=1)
def get_semantic_cache() -> SemanticCache:
    """Retorna o cache semântico singleton."""
    settings = get_settings()
    return SemanticCache(similarity_threshold=settings.cache_similarity_threshold)


@lru_cache(maxsize=1)
def get_prompt_registry() -> PromptRegistry:
    """Retorna o prompt registry singleton, carregado do diretório configurado."""
    settings = get_settings()
    registry = PromptRegistry()
    registry.load_dir(settings.prompt_registry_dir)
    return registry


@lru_cache(maxsize=1)
def get_pipeline() -> RagPipeline:
    """Retorna o pipeline RAG singleton."""
    settings = get_settings()
    cache = get_semantic_cache() if settings.cache_enabled else None
    return RagPipeline(
        retriever=get_retriever(),
        cache=cache,
        finops=get_finops_tracker(),
    )


@lru_cache(maxsize=1)
def get_auth_provider() -> AuthProvider:
    """Retorna o provedor de autenticação ativo.

    No estágio atual é o ``MockAuthProvider``; em produção (Fase 4) substitua por
    um provedor real (JWT/OIDC) sem alterar as rotas.
    """
    return MockAuthProvider()


def get_current_user(
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> UserContext:
    """Resolve o ``UserContext`` a partir de cabeçalhos controlados (nunca do body)."""
    provider = get_auth_provider()
    try:
        return provider.authenticate(role_header=x_user_role, user_id_header=x_user_id)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def require_roles(*allowed_roles: UserRole) -> Callable[[UserContext], UserContext]:
    """Cria uma dependência que exige um dos perfis informados (RBAC mínimo)."""

    def _checker(user: UserContext = Depends(get_current_user)) -> UserContext:
        if not can_access_route(user, allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Perfil sem permissão para acessar este recurso.",
            )
        return user

    return _checker
