"""Prompt Registry versionado (RF3.7).

Carrega prompts de arquivos ``.md`` com front-matter (id, version, owner, scope,
status) e mantém um registro imutável. Garante que:
  - apenas prompts com ``status: approved`` sejam usados em produção;
  - alterações informais sejam detectáveis via checksum (integridade);
  - cada prompt tenha versão e owner (rastreabilidade/governança).

Não há dependência externa: o parsing de front-matter é mínimo e determinístico.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)


class PromptRegistryError(Exception):
    """Erro de governança de prompts (não aprovado, ausente ou adulterado)."""


@dataclass(frozen=True)
class RegisteredPrompt:
    """Prompt versionado e seus metadados de governança."""

    id: str
    version: str
    owner: str
    scope: str
    status: str
    body: str
    checksum: str

    @property
    def is_approved(self) -> bool:
        """Indica se o prompt está aprovado para uso."""
        return self.status.lower() == "approved"


def _compute_checksum(body: str) -> str:
    """Checksum estável do corpo do prompt (detecção de alteração informal)."""
    return hashlib.sha256(body.strip().encode("utf-8")).hexdigest()


def _parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Extrai o front-matter YAML simples (chave: valor) e o corpo."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, parts[2].strip()


def _build_prompt(meta: dict[str, str], body: str) -> RegisteredPrompt:
    return RegisteredPrompt(
        id=meta.get("id", ""),
        version=str(meta.get("version", "")),
        owner=meta.get("owner", ""),
        scope=meta.get("scope", ""),
        status=meta.get("status", "draft"),
        body=body,
        checksum=_compute_checksum(body),
    )


class PromptRegistry:
    """Registro de prompts versionados carregados de um diretório."""

    def __init__(self) -> None:
        self._prompts: dict[str, RegisteredPrompt] = {}

    def register(self, prompt: RegisteredPrompt) -> None:
        """Registra um prompt indexado por ``id:version``."""
        if not prompt.id or not prompt.version:
            raise PromptRegistryError("Prompt sem id/version não pode ser registrado.")
        self._prompts[f"{prompt.id}:{prompt.version}"] = prompt
        logger.info(
            "prompt_registered",
            prompt_id=prompt.id,
            version=prompt.version,
            status=prompt.status,
        )

    def load_dir(self, path: str | Path) -> int:
        """Carrega todos os prompts ``.md`` de um diretório. Retorna a contagem."""
        directory = Path(path)
        count = 0
        for md_file in sorted(directory.glob("*.md")):
            meta, body = _parse_front_matter(md_file.read_text(encoding="utf-8"))
            if not meta.get("id"):
                continue
            self.register(_build_prompt(meta, body))
            count += 1
        return count

    def get(self, prompt_id: str, version: str | None = None) -> RegisteredPrompt:
        """Retorna um prompt aprovado por id (e versão, se informada).

        Raises:
            PromptRegistryError: Se o prompt não existir ou não estiver aprovado.
        """
        if version is not None:
            prompt = self._prompts.get(f"{prompt_id}:{version}")
        else:
            candidates = [p for p in self._prompts.values() if p.id == prompt_id]
            prompt = max(candidates, key=lambda p: p.version, default=None)

        if prompt is None:
            raise PromptRegistryError(f"Prompt '{prompt_id}' (v{version}) não encontrado.")
        if not prompt.is_approved:
            raise PromptRegistryError(
                f"Prompt '{prompt_id}' v{prompt.version} não está aprovado "
                f"(status={prompt.status}); alteração requer aprovação."
            )
        return prompt

    def verify_integrity(self, prompt_id: str, version: str, expected_checksum: str) -> bool:
        """Verifica se o prompt não foi alterado fora do processo (RF3.7)."""
        prompt = self._prompts.get(f"{prompt_id}:{version}")
        if prompt is None:
            raise PromptRegistryError(f"Prompt '{prompt_id}' v{version} não encontrado.")
        ok = prompt.checksum == expected_checksum
        if not ok:
            logger.warning("prompt_integrity_violation", prompt_id=prompt_id, version=version)
        return ok
