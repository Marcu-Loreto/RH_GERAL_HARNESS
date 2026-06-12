"""Testes unitários do prompt registry versionado (RF3.7)."""

from __future__ import annotations

import pytest

from app.governance.prompt_registry import (
    PromptRegistry,
    PromptRegistryError,
    RegisteredPrompt,
    _build_prompt,
    _compute_checksum,
    _parse_front_matter,
)

_APPROVED = """---
id: agent_specialist
version: 1
owner: time-ia-rh
scope: resposta a perguntas de RH
status: approved
---

Corpo do prompt aprovado.
"""

_DRAFT = """---
id: agent_draft
version: 1
owner: time-ia-rh
scope: rascunho
status: draft
---

Rascunho não aprovado.
"""


def _registry_with(*texts: str) -> PromptRegistry:
    registry = PromptRegistry()
    for text in texts:
        meta, body = _parse_front_matter(text)
        registry.register(_build_prompt(meta, body))
    return registry


@pytest.mark.unit
def test_loads_versioned_prompt_from_disk() -> None:
    registry = PromptRegistry()
    count = registry.load_dir("prompts")
    assert count >= 1
    prompt = registry.get("agent_specialist")
    assert prompt.version == "1"
    assert prompt.is_approved is True
    assert prompt.owner


@pytest.mark.unit
def test_approved_prompt_is_returned() -> None:
    registry = _registry_with(_APPROVED)
    prompt = registry.get("agent_specialist", "1")
    assert prompt.is_approved is True


@pytest.mark.unit
def test_draft_prompt_is_blocked() -> None:
    registry = _registry_with(_DRAFT)
    with pytest.raises(PromptRegistryError):
        registry.get("agent_draft", "1")


@pytest.mark.unit
def test_missing_prompt_raises() -> None:
    registry = _registry_with(_APPROVED)
    with pytest.raises(PromptRegistryError):
        registry.get("inexistente")


@pytest.mark.unit
def test_integrity_detects_informal_change() -> None:
    registry = _registry_with(_APPROVED)
    prompt: RegisteredPrompt = registry.get("agent_specialist", "1")
    assert registry.verify_integrity("agent_specialist", "1", prompt.checksum) is True
    tampered = _compute_checksum("conteúdo adulterado")
    assert registry.verify_integrity("agent_specialist", "1", tampered) is False


@pytest.mark.unit
def test_register_without_id_or_version_fails() -> None:
    registry = PromptRegistry()
    with pytest.raises(PromptRegistryError):
        registry.register(
            RegisteredPrompt(
                id="", version="", owner="x", scope="y", status="approved", body="b", checksum="c"
            )
        )
