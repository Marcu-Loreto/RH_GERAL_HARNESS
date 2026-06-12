"""Testes unitários de carregamento de configuração (RF0.2)."""

from __future__ import annotations

import pytest

from app.core.config import Settings, get_settings


@pytest.mark.unit
def test_defaults_are_safe() -> None:
    settings = Settings()
    assert settings.app_name == "rh-geral-harness"
    assert settings.environment == "dev"
    assert settings.api_v1_prefix == "/api/v1"
    # Sem segredo real: o padrão é um placeholder explícito.
    assert "change-me" in settings.secret_key


@pytest.mark.unit
def test_get_settings_is_cached_singleton() -> None:
    assert get_settings() is get_settings()


@pytest.mark.unit
def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "prod")
    monkeypatch.setenv("DEBUG", "false")
    settings = Settings()
    assert settings.environment == "prod"
    assert settings.is_production is True
    assert settings.debug is False
