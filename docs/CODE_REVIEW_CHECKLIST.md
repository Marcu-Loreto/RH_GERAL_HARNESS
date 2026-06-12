# Checklist de Code Review — Fase 0

Derivado de `CODE_REVIEW_GUIDELINES.md`, aplicado a esta fase.

## Geral (obrigatório)

- [ ] Sem credenciais/segredos no código (`.env` ignorado; só `.env.example`).
- [ ] Estrutura de pastas aderente à `SPEC_Fase_0`.
- [ ] Nomes claros e código modular.
- [ ] Erros tratados (config, DB, sanitização).
- [ ] Logs estruturados, sem dados sensíveis.
- [ ] Configuração por ambiente via `get_settings()`.

## Testes

- [ ] Unitários: trace ID, config, metadados, sanitização.
- [ ] Integração: health check, conexão com DB.
- [ ] Testes negativos incluídos (entrada inválida, status não indexável).
- [ ] Evidência de execução anexada (saída do pytest).

## Observabilidade

- [ ] `trace_id` gerado por requisição.
- [ ] `session_id` registrado.
- [ ] Latência registrada no middleware.

## CI

- [ ] Pipeline executa black, ruff, mypy e pytest.
- [ ] Verificação básica de segurança (regras `S` do ruff).

## Critérios de aceite (SPEC_Fase_0, §7)

- [ ] Projeto executa localmente.
- [ ] Testes de exemplo passam.
- [ ] Lint executa com sucesso.
- [ ] `.env.example` disponível.
- [ ] Documentação inicial criada.
- [ ] Trace ID gerado por requisição.
- [ ] Checklist de code review disponível.

---

# Checklist de Code Review — Fase 1 (MVP RAG)

## RAG (SPEC_Fase_1 §9)

- [x] Retrieval usa filtros por metadados (área, status, vigência, confidencialidade).
- [x] Documentos obsoletos/não aprovados são bloqueados na ingestão e na busca.
- [x] Resposta exige evidência; sem fonte ⇒ bloqueada pelo output guardrail.
- [x] Top-k e reranking híbrido controlados por configuração.
- [x] Não há acesso indevido entre domínios (filtro por área + RBAC simples).

## Guardrails

- [x] Input guardrail testado (injeção, PII de terceiros, entrada inválida).
- [x] Output guardrail testado (sem fonte, vazamento de PII).
- [x] Prompt injection e PII tratados com testes de segurança dedicados.

## Prompts e regressão

- [x] Prompt do especialista versionado em `prompts/agent_specialist_v1.md`.
- [x] Golden dataset executado como teste de regressão (`tests/rag/`).
- [x] Mudança de embedding/chunking/retrieval coberta por teste de regressão.

## Observabilidade

- [x] Trace por interação com tokens, latência, chunks e guardrails acionados.

## Evidências

- 85 testes (unit/integração/RAG/segurança) passando; cobertura 98%.
- Golden dataset: precision@k=1.0, acurácia de comportamento=1.0, source recall=1.0.
- black, ruff e mypy (strict) sem erros.

---

# Checklist de Code Review — Fase 2 (Multiagente)

## Orquestração (SPEC_Fase_2 §8)

- [x] Orquestrador não chama todos os agentes por padrão (`agents_invoked` mínimo).
- [x] Decisões são explicáveis (`routing_reason`, `routing_confidence` no trace).
- [x] Filtros por domínio aplicados (cada agente só consulta sua `area_rh`).
- [x] Fallback de busca ampla em baixa confiança.
- [x] Agentes não acessam ferramentas proibidas (apenas retrieval do domínio).
- [x] Traces incluem agente e domínio.

## Agentes

- [x] Cada agente possui escopo claro e único.
- [x] Sem vazamento entre domínios (teste de isolamento).
- [x] Perguntas multidomínio acionam auxiliar com razão registrada.

## Regressão

- [x] Acurácia de roteamento medida em `datasets/routing_rh.json` (≥90%).
- [x] Mudança no classificador coberta por teste de regressão (`tests/rag/test_routing.py`).

## Evidências

- 113 testes passando; cobertura 96%.
- Acurácia de roteamento = 100% (limiar ≥90%).
- black, ruff e mypy (strict) sem erros.

---

# Checklist de Code Review — Refatoração dos Agentes (Fase 2)

## Agentes especialistas

- [x] Cada agente tem escopo claro e declarado (`SCOPE`, `DOMAIN`, `AREA_RH`).
- [x] Cada agente reside em arquivo próprio (`*_agent.py`) e herda de `SpecialistAgent`.
- [x] Agente não acessa domínio proibido (filtro por `area_rh`; teste de isolamento).
- [x] Agente possui filtros de retrieval compatíveis com a área.
- [x] Agente registra trace (decisão do orquestrador inclui `agent`, `agent_id`, `domain`).
- [x] Comportamento de risco definido quando aplicável:
  - [x] `CompensationAgent` bloqueia pedido de salário individual.
  - [x] `ComplianceAgent` sinaliza revisão humana em temas sensíveis.
  - [x] `LaborPolicyAgent` sinaliza risco maior em temas trabalhistas sensíveis.
- [x] Agente possui testes unitários e de integração.

## Registry e router

- [x] `AGENT_REGISTRY` centraliza os 6 agentes (um por domínio).
- [x] `agent_router` seleciona o agente correto e expõe `fallback_required`.
- [x] Orquestrador usa registry/router e não depende de `specialists.py`.
- [x] `specialists.build_agents()` preservado como camada de compatibilidade.

## Orquestração e segurança

- [x] Orquestrador invoca apenas o agente necessário (`agents_invoked` mínimo).
- [x] Multidomínio aciona auxiliar só quando o primário não tem evidência.
- [x] Decisões explicáveis no trace (`routing_reason`, `routing_confidence`).
- [x] Logs sem dados sensíveis (apenas metadados de decisão e motivo de risco).
- [x] Sem segredos no código.

## Regressão e evidências

- [x] `test_orchestrator.py`, `test_multiagent_pipeline.py` e `test_routing.py` mantidos.
- [x] 189 testes passando; black, ruff e mypy (strict) sem erros.
