"""Camada mínima de autenticação e contexto de usuário (pré-Fase 4).

Esta é uma abstração **plugável** de autenticação. No estágio atual não há um
provedor de identidade real: usamos o ``MockAuthProvider``, que deriva o perfil
de um cabeçalho controlado (``X-User-Role``) e, na ausência dele, assume o perfil
de menor privilégio (``colaborador``). Em produção (Fase 4), o ``MockAuthProvider``
deve ser substituído por um ``AuthProvider`` real (ex.: JWT/OIDC) sem alterar as
rotas — elas dependem apenas da interface ``UserContext``/``AuthProvider``.

Regra de segurança central: o ``role`` **nunca** deve ser confiado a partir do
corpo da requisição; ele vem exclusivamente do contexto autenticado.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.logging import get_logger
from app.core.models import UserRole

logger = get_logger(__name__)

# Perfil seguro mínimo assumido quando não há identidade autenticada.
DEFAULT_SAFE_ROLE = UserRole.COLABORADOR
ANONYMOUS_USER_ID = "anonymous"


class AuthError(Exception):
    """Falha de autenticação (perfil inválido/credencial ausente quando exigida)."""


@dataclass(frozen=True)
class UserContext:
    """Identidade autenticada propagada às rotas e ao pipeline.

    ``user_id`` é um identificador opaco (não PII); ``role`` governa o RBAC e os
    filtros de confidencialidade no retrieval.
    """

    user_id: str
    role: UserRole
    authenticated: bool = False


class AuthProvider(Protocol):
    """Contrato de um provedor de autenticação."""

    def authenticate(self, *, role_header: str | None, user_id_header: str | None) -> UserContext:
        """Resolve o ``UserContext`` a partir de credenciais/headers controlados."""
        ...


class MockAuthProvider:
    """Provedor de autenticação para dev/testes (NÃO usar em produção).

    Deriva o perfil do cabeçalho ``X-User-Role``. Sem cabeçalho, retorna o perfil
    seguro mínimo (``colaborador``) e ``authenticated=False``. Perfil inválido
    resulta em ``AuthError``.
    """

    def authenticate(self, *, role_header: str | None, user_id_header: str | None) -> UserContext:
        user_id = (user_id_header or ANONYMOUS_USER_ID).strip() or ANONYMOUS_USER_ID
        if role_header is None or not role_header.strip():
            return UserContext(user_id=user_id, role=DEFAULT_SAFE_ROLE, authenticated=False)
        try:
            role = UserRole(role_header.strip().lower())
        except ValueError as exc:
            logger.warning("auth_invalid_role")
            raise AuthError("Perfil de usuário inválido.") from exc
        return UserContext(user_id=user_id, role=role, authenticated=True)


def can_access_route(user: UserContext, allowed_roles: tuple[UserRole, ...]) -> bool:
    """RBAC mínimo: ``admin`` acessa tudo; demais precisam estar na lista."""
    if user.role == UserRole.ADMIN:
        return True
    return user.role in allowed_roles
