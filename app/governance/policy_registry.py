"""Policy Registry versionado (RF3.8).

Centraliza e versiona as políticas de acesso (perfil → confidencialidade
permitida) e as regras de risco que exigem revisão humana. Versionar a política
permite auditoria, rollback e regressão controlada de mudanças de governança.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.logging import get_logger
from app.core.models import Confidentiality, UserRole

logger = get_logger(__name__)


@dataclass(frozen=True)
class AccessPolicy:
    """Política de acesso de um perfil (níveis de confidencialidade permitidos)."""

    role: UserRole
    allowed_confidentiality: tuple[Confidentiality, ...]
    requires_human_review: bool = False


# Versão corrente da política de acesso (RBAC simples). Alterações aqui são
# mudanças de governança e exigem code review + regressão.
_POLICY_VERSION = "1.0.0"

_ACCESS_POLICIES: dict[UserRole, AccessPolicy] = {
    UserRole.COLABORADOR: AccessPolicy(
        role=UserRole.COLABORADOR,
        allowed_confidentiality=(Confidentiality.PUBLICO, Confidentiality.INTERNO),
    ),
    UserRole.GESTOR: AccessPolicy(
        role=UserRole.GESTOR,
        allowed_confidentiality=(
            Confidentiality.PUBLICO,
            Confidentiality.INTERNO,
            Confidentiality.RESTRITO,
        ),
    ),
    UserRole.RH: AccessPolicy(
        role=UserRole.RH,
        allowed_confidentiality=(
            Confidentiality.PUBLICO,
            Confidentiality.INTERNO,
            Confidentiality.RESTRITO,
            Confidentiality.CONFIDENCIAL,
        ),
    ),
    UserRole.JURIDICO: AccessPolicy(
        role=UserRole.JURIDICO,
        allowed_confidentiality=(
            Confidentiality.PUBLICO,
            Confidentiality.INTERNO,
            Confidentiality.RESTRITO,
            Confidentiality.CONFIDENCIAL,
        ),
        requires_human_review=True,
    ),
    UserRole.ADMIN: AccessPolicy(
        role=UserRole.ADMIN,
        allowed_confidentiality=tuple(Confidentiality),
    ),
}


@dataclass
class PolicyRegistry:
    """Registro versionado de políticas de acesso e risco."""

    version: str = _POLICY_VERSION
    policies: dict[UserRole, AccessPolicy] = field(default_factory=lambda: dict(_ACCESS_POLICIES))

    def allowed_confidentiality_for(self, role: UserRole) -> list[Confidentiality]:
        """Retorna os níveis de confidencialidade permitidos para um perfil."""
        policy = self.policies.get(role)
        if policy is None:
            logger.warning("policy_role_not_found", role=str(role))
            return [Confidentiality.PUBLICO]
        return list(policy.allowed_confidentiality)

    def requires_human_review(self, role: UserRole) -> bool:
        """Indica se o perfil exige revisão humana por política."""
        policy = self.policies.get(role)
        return bool(policy and policy.requires_human_review)


_default_registry: PolicyRegistry | None = None


def get_policy_registry() -> PolicyRegistry:
    """Retorna o policy registry padrão (singleton)."""
    global _default_registry
    if _default_registry is None:
        _default_registry = PolicyRegistry()
    return _default_registry
