# Policies

Diretório destinado às políticas versionadas do harness (governança de acesso,
guardrails e regras de negócio que podem ser expressas como dados).

Hoje as políticas estão implementadas em código:

- Acesso por perfil (RBAC/ABAC): `app/governance/policy_registry.py`
- Guardrails e mensagens de recusa: `app/guardrails/policies.py`
- Prompts versionados: `app/governance/prompt_registry.py` (carrega de `prompts/`)

Esta pasta reserva o espaço para externalizar essas políticas em arquivos
versionados (ex.: YAML/JSON) quando a Fase 4 priorizar a governança como dado,
mantendo rastreabilidade e revisão independente do ciclo de release do código.
