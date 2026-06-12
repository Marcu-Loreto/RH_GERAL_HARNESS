"""Testes unitários de validação dos modelos de metadados (RF0.4)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.core.models import (
    Confidentiality,
    DocumentMetadata,
    DocumentStatus,
    Permission,
    User,
    UserRole,
)


def _base_doc(**overrides: object) -> DocumentMetadata:
    data: dict[str, object] = {
        "source_id": "doc-1",
        "title": "Política de Férias",
        "owner": "rh@empresa.com",
        "area_rh": "trabalhista",
        "document_type": "politica",
        "version": "1.0",
        "valid_from": datetime(2025, 1, 1, tzinfo=UTC),
        "confidentiality": Confidentiality.INTERNO,
        "language": "pt-BR",
        "hash": "abc123",
    }
    data.update(overrides)
    return DocumentMetadata(**data)  # type: ignore[arg-type]


@pytest.mark.unit
def test_approved_document_is_indexable() -> None:
    doc = _base_doc(status=DocumentStatus.APPROVED)
    assert doc.is_indexable() is True


@pytest.mark.unit
def test_draft_document_not_indexable() -> None:
    doc = _base_doc(status=DocumentStatus.DRAFT)
    assert doc.is_indexable() is False


@pytest.mark.unit
def test_deprecated_document_not_indexable() -> None:
    doc = _base_doc(status=DocumentStatus.DEPRECATED)
    assert doc.is_indexable() is False


@pytest.mark.unit
def test_invalid_status_rejected() -> None:
    with pytest.raises(ValidationError):
        _base_doc(status="invalido")


@pytest.mark.unit
def test_user_requires_valid_role() -> None:
    user = User(user_id="u1", role=UserRole.GESTOR)
    assert user.role == UserRole.GESTOR.value
    with pytest.raises(ValidationError):
        User(user_id="u2", role="hacker")  # type: ignore[arg-type]


@pytest.mark.unit
def test_permission_defaults() -> None:
    perm = Permission(role=UserRole.COLABORADOR)
    assert perm.allowed_confidentiality == []
    assert perm.requires_human_review is False
