"""Testes unitários do policy registry versionado (RF3.8)."""

from __future__ import annotations

import pytest

from app.core.models import Confidentiality, UserRole
from app.governance.policy_registry import PolicyRegistry, get_policy_registry


@pytest.mark.unit
def test_registry_has_version() -> None:
    registry = PolicyRegistry()
    assert registry.version


@pytest.mark.unit
def test_colaborador_cannot_access_confidential() -> None:
    registry = PolicyRegistry()
    allowed = registry.allowed_confidentiality_for(UserRole.COLABORADOR)
    assert Confidentiality.CONFIDENCIAL not in allowed
    assert Confidentiality.PUBLICO in allowed


@pytest.mark.unit
def test_rh_can_access_confidential() -> None:
    registry = PolicyRegistry()
    allowed = registry.allowed_confidentiality_for(UserRole.RH)
    assert Confidentiality.CONFIDENCIAL in allowed


@pytest.mark.unit
def test_admin_has_all_levels() -> None:
    registry = PolicyRegistry()
    allowed = registry.allowed_confidentiality_for(UserRole.ADMIN)
    assert set(allowed) == set(Confidentiality)


@pytest.mark.unit
def test_juridico_requires_human_review() -> None:
    registry = PolicyRegistry()
    assert registry.requires_human_review(UserRole.JURIDICO) is True
    assert registry.requires_human_review(UserRole.COLABORADOR) is False


@pytest.mark.unit
def test_singleton_is_cached() -> None:
    assert get_policy_registry() is get_policy_registry()
