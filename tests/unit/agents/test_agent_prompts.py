"""Testes do loader de prompts/escopos dos agentes (manutenção via arquivos)."""

from __future__ import annotations

import pytest

from app.agents.agent_prompts import get_agent_scope, reload_agent_prompts
from app.agents.agent_registry import build_registry
from app.retrieval.retriever import Retriever
from app.retrieval.vector_store import InMemoryVectorStore

_AGENT_IDS = [
    "benefits_agent",
    "labor_policy_agent",
    "compensation_agent",
    "learning_agent",
    "recruiting_agent",
    "compliance_agent",
]


@pytest.mark.unit
def test_all_agent_prompts_load_from_files() -> None:
    reload_agent_prompts()
    for agent_id in _AGENT_IDS:
        assert get_agent_scope(agent_id), f"escopo ausente para {agent_id}"


@pytest.mark.unit
def test_missing_prompt_uses_default_fallback() -> None:
    assert get_agent_scope("inexistente", default="fallback") == "fallback"


@pytest.mark.unit
def test_agents_use_scope_from_prompt_files() -> None:
    agents = build_registry(Retriever(store=InMemoryVectorStore()))
    for agent in agents.values():
        assert agent.scope == get_agent_scope(agent.agent_id, default=agent.scope)
        assert agent.scope  # nunca vazio
