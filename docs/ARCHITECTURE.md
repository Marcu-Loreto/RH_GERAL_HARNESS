# Arquitetura — Harness IA RH (Fase 0)

## Visão geral

Assistente corporativo de RH baseado em RAG multiagente. A Fase 0 estabelece a
fundação técnica: estrutura modular, configuração por ambiente, logging
estruturado com rastreamento, modelos de metadados, persistência de metadados,
API com health check e pipeline de CI.

## Estrutura de pastas

```text
app/
  api/            # FastAPI: app, middleware de trace, rotas versionadas (/api/v1)
  agents/         # agentes especialistas e orquestrador (Fase 2)
  retrieval/      # busca híbrida, filtros, reranking (Fase 1)
  guardrails/     # guardrails de entrada/retrieval/saída (Fase 1)
  ingestion/      # parsing, chunking, indexação (Fase 1)
  observability/  # traces, custo, tokens, latência (Fase 3)
  evaluation/     # golden dataset e métricas (Fase 3)
  core/           # config, logging, tracing, security, models de metadados
  infrastructure/ # persistência de metadados (SQLAlchemy)
tests/            # unit / integration / rag / security
docs/             # documentação de arquitetura e governança
prompts/ policies/ datasets/ scripts/ infra/
```

## Componentes da Fase 0

| Componente   | Arquivo                                | Responsabilidade                                          |
| ------------ | -------------------------------------- | --------------------------------------------------------- |
| Configuração | `app/core/config.py`                   | Settings via pydantic-settings, `get_settings()` cacheado |
| Tracing      | `app/core/tracing.py`                  | `trace_id`/`session_id` por contexto                      |
| Logging      | `app/core/logging.py`                  | structlog JSON + injeção de trace                         |
| Segurança    | `app/core/security.py`                 | sanitização básica de entrada                             |
| Metadados    | `app/core/models.py`                   | Documento, Chunk, Usuário, Permissão, Trace, Resposta     |
| Persistência | `app/infrastructure/database.py`       | engine, sessão e health check                             |
| API          | `app/api/main.py` + `routes/health.py` | app, middleware, health/ready                             |

## Decisões técnicas (ADR resumido)

- **uv + Python 3.13**: gestor de pacotes rápido; versão já fixada no projeto.
- **pydantic-settings**: configuração validada e por ambiente; sem env vars
  importadas diretamente.
- **structlog (JSON)**: logs estruturados e rastreáveis; sem dados sensíveis.
- **contextvars para trace**: propagação sem acoplar assinaturas de funções.
- **SQLAlchemy 2.0 + SQLite (dev)**: metadados; PostgreSQL previsto para prod.
- **Escopo controlado**: nesta fase não há LLM, retrieval ou agentes — apenas
  fundação, conforme `SPEC_Fase_0`.

## Rastreabilidade (RF0.3)

Toda requisição recebe `trace_id` e `session_id` via `TraceContextMiddleware`,
propagados pelo contexto e devolvidos nos cabeçalhos `X-Trace-Id`/`X-Session-Id`.
IDs recebidos do cliente são preservados, permitindo correlação ponta a ponta.

## Próximos passos

Fase 1 — MVP RAG de RH: ingestão documental, embeddings, busca e resposta com
evidência (concluída — ver abaixo).

---

# Fase 1 — MVP RAG de RH

## Fluxo

```text
entrada → guardrail de entrada → interpretação simples → retrieval filtrado
→ geração → guardrail de saída → resposta com evidência → trace
```

## Componentes

| Componente      | Arquivo                          | Responsabilidade                      |
| --------------- | -------------------------------- | ------------------------------------- |
| Chunking        | `app/ingestion/chunker.py`       | divide documentos em trechos          |
| Ingestão        | `app/ingestion/service.py`       | governança + chunk + embed + index    |
| Embeddings      | `app/retrieval/embeddings.py`    | provedor plugável (hashing local)     |
| Vector store    | `app/retrieval/vector_store.py`  | índice em memória + filtros           |
| Retriever       | `app/retrieval/retriever.py`     | busca híbrida (densa + lexical)       |
| Guardrails      | `app/guardrails/*`               | entrada, saída, PII, prompt injection |
| Geração         | `app/agents/answer_generator.py` | resposta extrativa com evidência      |
| Pipeline        | `app/rag/pipeline.py`            | orquestra o fluxo completo            |
| Observabilidade | `app/observability/trace.py`     | trace de interação                    |
| Avaliação       | `app/evaluation/*`               | golden dataset + métricas             |

## Decisões técnicas (ADR resumido)

- **Provedores plugáveis com fallback local determinístico**: embeddings por
  hashing, vector store em memória e geração extrativa. Roda sem chave de API,
  custo zero e 100% testável; LLM/Vector DB reais podem ser plugados depois sem
  alterar o pipeline. _Content was rephrased for compliance._
- **Busca híbrida**: similaridade densa (peso 0.4) + cobertura lexical de termos
  sem stopwords (peso 0.6), com limiar absoluto + corte relativo para precisão.
- **Governança no retrieval**: filtros por área, status `approved`, vigência e
  confidencialidade por perfil (RBAC simples) aplicados antes da geração.
- **Sem alucinação por construção**: a resposta extrativa só usa trechos
  recuperados; sem evidência ⇒ mensagem de limitação + revisão humana.

## Métricas (golden dataset inicial)

precision@k = 1.0 · acurácia de comportamento = 1.0 · source recall = 1.0 ·
cobertura de testes 98% (módulos de segurança 100%).

## Próximos passos (Fase 2)

Multiagente e orquestração: agentes especialistas por domínio, orquestrador com
roteamento por intenção e controle de acesso por domínio (concluída — ver abaixo).

---

# Fase 2 — Multiagente e Orquestração

## Fluxo

```text
entrada → guardrail de entrada → Query Intelligence (classifica domínio,
query canônica, risco, confiança) → orquestrador (seleciona agente / fallback /
auxiliar) → retrieval por domínio → geração → guardrail de saída → trace explicável
```

## Componentes

| Componente          | Arquivo                            | Responsabilidade                                                |
| ------------------- | ---------------------------------- | --------------------------------------------------------------- |
| Query Intelligence  | `app/agents/query_intelligence.py` | domínio, query canônica, must_terms, risco, confiança, fallback |
| Agente especialista | `app/agents/base_agent.py`         | retrieval filtrado pelo domínio do agente                       |
| Registro de agentes | `app/agents/specialists.py`        | 6 agentes de domínio com escopo                                 |
| Orquestrador        | `app/agents/orchestrator.py`       | seleção, fallback e agente auxiliar                             |
| Pipeline            | `app/rag/pipeline.py`              | integra guardrails + orquestrador + trace                       |

## Agentes (SPEC §3)

`agente_beneficios`, `agente_trabalhista`, `agente_cargos_salarios`,
`agente_treinamento`, `agente_recrutamento`, `agente_compliance`.

## Decisões técnicas (ADR resumido)

- **Classificação determinística por palavras-chave/frases** (sem LLM): mantém
  custo zero e reprodutibilidade; `confidence` = participação do domínio top.
- **Fallback em baixa confiança**: busca ampla (sem filtro de domínio) quando a
  confiança fica abaixo de `classification_min_confidence`.
- **Agente auxiliar (multidomínio)**: acionado apenas quando o primário não traz
  evidência e há domínio secundário próximo (`multidomain_ratio`); razão registrada.
- **Orquestrador nunca chama todos os agentes**: apenas o(s) necessário(s);
  `agents_invoked` no trace comprova.
- **Isolamento de domínio**: cada agente filtra por `area_rh`, evitando vazamento
  entre domínios.
- **Trace explicável (RF2.7)**: `domain`, `agent`, `routing_confidence`,
  `routing_reason` e `agents_invoked`.

## Métricas (datasets)

Acurácia de roteamento = 100% no `routing_rh.json` (limiar ≥90%); golden dataset
da Fase 1 mantido. Cobertura de testes 96%.

## Agentes Especialistas de RH

### 1. Os seis agentes

| Agente              | Domínio                          | Escopo (resumo)                                                                 |
| ------------------- | -------------------------------- | ------------------------------------------------------------------------------- |
| `BenefitsAgent`     | Benefícios                       | férias, vale-refeição/alimentação, plano de saúde, abonos, auxílio-creche, etc. |
| `LaborPolicyAgent`  | Trabalhista / Políticas Internas | jornada, banco de horas, trabalho remoto, afastamentos, licenças, atestados     |
| `CompensationAgent` | Cargos, Salários e Competências  | remuneração, promoção, níveis, senioridade, plano de carreira                   |
| `LearningAgent`     | Treinamento e Desenvolvimento    | cursos, trilhas, certificações, onboarding, PDI, avaliação de desempenho        |
| `RecruitingAgent`   | Recrutamento e Seleção           | vagas, processo seletivo, indicação, admissão, candidatura interna, entrevistas |
| `ComplianceAgent`   | Compliance e Conduta             | ética, denúncias, assédio, discriminação, conflito de interesses, código        |

### 2. Onde cada agente está implementado

Cada agente tem o seu próprio arquivo em `app/agents/`: `benefits_agent.py`,
`labor_policy_agent.py`, `compensation_agent.py`, `learning_agent.py`,
`recruiting_agent.py` e `compliance_agent.py`. Todos herdam de `SpecialistAgent`
(`app/agents/base_agent.py`) e declaram `AGENT_ID`, `DOMAIN`, `AREA_RH`, `SCOPE`,
`RISK_RULES` e, quando aplicável, sobrescrevem `screen()` (triagem de risco).

### 3. Agent registry

`app/agents/agent_registry.py` mantém o `AGENT_REGISTRY` (mapa
`Domain → fábrica do agente`) e `build_registry(retriever)`, que instancia todos
os agentes. É o único ponto de verdade do conjunto de agentes.

### 4. Agent router

`app/agents/agent_router.py` traduz a saída da Query Intelligence Layer em uma
decisão explicável `RouterDecision(selected_agent, domain, reason,
fallback_required)`. `selected_agent` usa o identificador público do agente
(ex.: `benefits_agent`); em baixa confiança, `fallback_required = true`.

### 5. Como o orquestrador usa os agentes

`Orchestrator` (`app/agents/orchestrator.py`) carrega os agentes via
`build_registry`, classifica a pergunta (`classify`), consulta o `agent_router`
para a seleção/razão e invoca **apenas** o agente do domínio. Em baixa confiança
faz fallback de busca ampla; em multidomínio, aciona um agente auxiliar somente
quando o primário não traz evidência. A triagem (`screen`) do agente é anexada à
decisão para explicabilidade e rastreamento.

### 6. Como criar um novo agente

1. Criar `app/agents/<novo>_agent.py` com uma classe que herda de
   `SpecialistAgent` e declara `AGENT_ID`, `DOMAIN`, `AREA_RH`, `SCOPE` (e
   `screen()` se houver regra de risco).
2. Adicionar o `Domain` correspondente em `query_intelligence.Domain` e seus
   sinais (`_DOMAIN_KEYWORDS`, `DOMAIN_TO_AREA`).
3. Registrar a classe em `AGENT_REGISTRY` (`agent_registry.py`).
4. Adicionar testes em `tests/unit/agents/` e `tests/integration/agents/`.

Nenhuma alteração no orquestrador é necessária — ele consome o registro.

### 7. Testes que protegem a arquitetura multiagente

- `tests/unit/agents/test_agent_registry.py`: 6 agentes, domínios, atributos.
- `tests/unit/agents/test_agent_router.py`: seleção e fallback do roteador.
- `tests/unit/agents/test_agent_behaviors.py`: regras de risco e isolamento.
- `tests/integration/agents/test_agent_routing.py`: roteamento por domínio.
- `tests/integration/agents/test_multidomain_routing.py`: agente auxiliar.
- Regressão: `tests/unit/test_orchestrator.py`, `tests/rag/test_routing.py`,
  `tests/integration/test_multiagent_pipeline.py`.

## Próximos passos (Fase 3)

Harness completo: observabilidade avançada, evaluation harness contínuo, model
router, cache, FinOps e human-in-the-loop.

---

# Fase 3 — Harness Completo

## Fluxo

```text
entrada → guardrail de entrada → orquestrador (domínio + retrieval) →
model router (risco/confiança/custo + fallback) → cache semântico (hit? reuso) →
geração → guardrail de saída → FinOps (custo) → human-in-the-loop → trace observável
```

## Componentes

| Componente          | Arquivo                             | Responsabilidade                                          |
| ------------------- | ----------------------------------- | --------------------------------------------------------- |
| Model Router        | `app/core/model_router.py`          | seleção de modelo por risco/confiança/custo + fallback    |
| FinOps              | `app/finops/cost.py`                | custo por chamada e agregação por agente/modelo/canal     |
| Cache semântico     | `app/cache/semantic_cache.py`       | reuso por similaridade com validação de acesso e versão   |
| Human-in-the-loop   | `app/escalation/human_review.py`    | escalonamento de casos sensíveis / baixa confiança        |
| Prompt Registry     | `app/governance/prompt_registry.py` | prompts versionados + bloqueio de alteração informal      |
| Policy Registry     | `app/governance/policy_registry.py` | políticas de acesso/risco versionadas                     |
| Avaliação estendida | `app/evaluation/evaluator.py`       | custo, tokens, latência P95, fallback e human-review rate |
| Relatório FinOps    | `app/api/routes/finops.py`          | `GET /api/v1/finops/summary`                              |

## Regras de roteamento de modelo (SPEC §4)

| Condição              | Ação                              |
| --------------------- | --------------------------------- |
| simples e baixo risco | modelo econômico (`minimax-m2.5`) |
| risco médio           | intermediário (`gpt-4o-mini`)     |
| alto risco            | robusto (`gpt-4o`)                |
| baixa confiança       | robusto + revisão humana          |
| indisponibilidade     | fallback para tier disponível     |
| custo acima do limite | log de orçamento + uso de cache   |

## Decisões técnicas (ADR resumido)

- **Infra de observabilidade plugável**: traces, custo e métricas são locais e
  determinísticos (sem Langfuse/Phoenix/Redis), mantendo custo zero e CI offline;
  adaptadores externos podem ser plugados sem alterar o pipeline.
- **Cache com governança**: o reuso exige que o perfil tenha acesso a todos os
  níveis de confidencialidade da resposta em cache e que as versões dos documentos
  continuem vigentes (invalidação por versão), evitando vazamento e dado obsoleto.
- **Custo medido mesmo no MVP extrativo**: o router escolhe o modelo e o FinOps
  calcula o custo estimado por tokens, habilitando o dashboard de custo.
- **Prompt registry imutável**: prompts não aprovados são bloqueados e a
  integridade é verificada por checksum (detecção de alteração fora do processo).
- **Trace observável (RF3.1)**: `model`, `model_tier`, `estimated_cost`,
  `input/output_tokens`, `latency_ms`, `cache_hit`, `prompt_version` e
  `escalation_reason`.

## Métricas (golden dataset estendido)

precision@k ≥ 0.85 · citation accuracy ≥ 0.95 · faithfulness ≥ 0.90 ·
acurácia de comportamento ≥ 0.90 · custo/latência/fallback/human-review medidos.
Cobertura de testes 96% (157 testes).
