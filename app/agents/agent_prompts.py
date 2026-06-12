"""Loader dos prompts/escopos dos agentes (consolidados em ``prompts/agents``).

Centraliza a leitura dos textos de escopo de cada agente especialista a partir de
arquivos ``.md`` versionados (front-matter ``id``, ``version``, ``owner``,
``status``). Manter o texto fora do código facilita a manutenção: editar o escopo
de um agente passa a ser editar um arquivo, sem tocar em Python.

O diretório base é ``<prompt_registry_dir>/agents`` (ver ``Settings``). O loader é
cacheado; em ambientes de teste use ``reload_agent_prompts()`` para forçar nova
leitura após alterar os arquivos.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger
from app.governance.prompt_registry import _parse_front_matter

logger = get_logger(__name__)


def _agents_dir() -> Path:
    """Diretório onde vivem os prompts por agente."""
    return Path(get_settings().prompt_registry_dir) / "agents"


@lru_cache(maxsize=1)
def _load_agent_prompts() -> dict[str, str]:
    """Lê os prompts de ``prompts/agents/*.md`` indexados por ``id`` do agente."""
    directory = _agents_dir()
    prompts: dict[str, str] = {}
    if not directory.is_dir():
        logger.warning("agent_prompts_dir_missing", path=str(directory))
        return prompts
    for md_file in sorted(directory.glob("*.md")):
        meta, body = _parse_front_matter(md_file.read_text(encoding="utf-8"))
        agent_id = meta.get("id")
        if not agent_id:
            continue
        prompts[agent_id] = body.strip()
    logger.info("agent_prompts_loaded", count=len(prompts))
    return prompts


def get_agent_scope(agent_id: str, default: str = "") -> str:
    """Retorna o escopo (prompt) de um agente, com fallback para ``default``.

    O fallback garante que o sistema continue funcionando mesmo se o arquivo de
    prompt estiver ausente, usando o valor declarado na classe do agente.
    """
    return _load_agent_prompts().get(agent_id) or default


def reload_agent_prompts() -> None:
    """Limpa o cache de prompts (útil após editar arquivos em testes/manutenção)."""
    _load_agent_prompts.cache_clear()
