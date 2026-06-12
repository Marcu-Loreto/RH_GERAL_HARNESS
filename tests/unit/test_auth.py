"""Testes unitários da camada mínima de autenticação (Prioridade 1)."""

from __future__ import annotations

import pytest

from app.core.auth import (
    DEFAULT_SAFE_ROLE,
    AuthError,
    MockAuthProvider,
    UserContext,
    can_access_route,
)
from app.core.models import UserRole


@pytest.fixture()
def provider() -> MockAuthProvider:
    return MockAuthProvider()


@pytest.mark.unit
def test_absent_role_assumes_safe_minimal(provider: MockAuthProvider) -> None:
    ctx = provider.authenticate(role_header=None, user_id_header=None)
    assert ctx.role == DEFAULT_SAFE_ROLE
    assert ctx.role == UserRole.COLABORADOR
    assert ctx.authenticated is False


@pytest.mark.unit
def test_valid_role_header_is_used(provider: MockAuthProvider) -> None:
    ctx = provider.authenticate(role_header="rh", user_id_header="u-1")
    assert ctx.role == UserRole.RH
    assert ctx.user_id == "u-1"
    assert ctx.authenticated is True


@pytest.mark.unit
def test_invalid_role_raises(provider: MockAuthProvider) -> None:
    with pytest.raises(AuthError):
        provider.authenticate(role_header="superuser", user_id_header=None)


@pytest.mark.unit
def test_admin_can_access_any_route() -> None:
    admin = UserContext(user_id="a", role=UserRole.ADMIN, authenticated=True)
    assert can_access_route(admin, (UserRole.RH,)) is True


@pytest.mark.unit
def test_role_outside_allowed_is_denied() -> None:
    colaborador = UserContext(user_id="c", role=UserRole.COLABORADOR)
    assert can_access_route(colaborador, (UserRole.RH, UserRole.ADMIN)) is False


@pytest.mark.unit
def test_role_in_allowed_is_granted() -> None:
    rh = UserContext(user_id="r", role=UserRole.RH, authenticated=True)
    assert can_access_route(rh, (UserRole.RH, UserRole.ADMIN)) is True
