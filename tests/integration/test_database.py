"""Testes de integração da conexão com o banco de metadados (RF0.5)."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.infrastructure.database import get_session, health_check


@pytest.mark.integration
def test_health_check_returns_true() -> None:
    assert health_check() is True


@pytest.mark.integration
def test_session_executes_query() -> None:
    with get_session() as session:
        result = session.execute(text("SELECT 1")).scalar_one()
    assert result == 1
