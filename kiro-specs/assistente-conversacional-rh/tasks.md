# Plano de Implementação: Assistente Conversacional de RH

## Visão Geral

Implementação incremental do assistente conversacional, partindo do backend (classificador de dificuldade, model router adaptado, transbordo, métricas) e finalizando com o frontend React por perfil.

## Tasks

- [x] 1. Implementar o Classificador de Dificuldade por Dicionário
  - [x] 1.1 Criar `app/agents/difficulty_classifier.py` com enum `DifficultyLevel`, dataclass `DifficultyClassification` e função `classify_difficulty(query: str)`
    - Definir dicionários `_EASY_TERMS`, `_MEDIUM_TERMS`, `_HARD_TERMS`
    - Implementar lógica de prioridade: difícil > intermediário > fácil > default intermediário
    - Usar matching por substring (mesma estratégia do `query_intelligence.py`)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x]\* 1.2 Escrever testes de propriedade para o classificador de dificuldade
    - **Property 1: Classificação de dificuldade é total e determinística**
    - **Property 2: Prioridade do classificador de dificuldade**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

  - [x]\* 1.3 Escrever testes unitários para edge cases do classificador
    - Testar string vazia, unicode, múltiplos termos mistos
    - _Requirements: 3.1, 3.5_

- [ ] 2. Adaptar o Model Router para classificação por dificuldade
  - [ ] 2.1 Adicionar `select_model_by_difficulty(difficulty: DifficultyLevel)` em `app/core/model_router.py`
    - Mapear `FACIL→ECONOMICO`, `INTERMEDIARIO→INTERMEDIARIO`, `DIFICIL→ROBUSTO`
    - Manter fallback existente para modelo indisponível
    - Registrar em log: modelo selecionado, dificuldade, custo estimado
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]\* 2.2 Escrever testes de propriedade para o mapeamento dificuldade→modelo
    - **Property 3: Mapeamento dificuldade → modelo**
    - **Property 4: Fallback de modelo indisponível**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [ ] 3. Integrar classificador de dificuldade no pipeline RAG
  - [ ] 3.1 Modificar `app/rag/pipeline.py` para invocar `classify_difficulty` após o orquestrador e usar `select_model_by_difficulty` em vez do `select_model` baseado em risco
    - O classificador de dificuldade substitui a lógica risco→tier
    - Preservar log e trace com o novo campo `difficulty_level`
    - _Requirements: 3.1, 4.1, 4.2, 4.3_

- [ ] 4. Checkpoint — Garantir que classificador e model router funcionam
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implementar mecanismo de Transbordo via JIRA
  - [ ] 5.1 Criar `app/escalation/jira_escalation.py` com `create_escalation()` que gera `EscalationTicket` com URL JIRA
    - URL formatada com query params (summary, description, labels)
    - Adicionar `jira_base_url` em `app/core/config.py` (Settings)
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ] 5.2 Integrar transbordo no pipeline: quando `has_evidence=False` após fallback, chamar `create_escalation` e incluir link na resposta ao usuário
    - Registrar motivo no trace (`escalation_reason`)
    - _Requirements: 6.1, 6.2, 6.3, 2.4_

  - [ ]\* 5.3 Escrever testes de propriedade para o transbordo
    - **Property 8: Transbordo registra motivo e gera link**
    - **Validates: Requirements 6.1, 6.2, 6.3**

- [ ] 6. Implementar API de Métricas e Dashboard
  - [ ] 6.1 Criar `app/api/routes/metrics.py` com rotas: `GET /metrics/summary`, `GET /metrics/tokens`, `GET /metrics/costs`, `GET /metrics/sessions`, `GET /metrics/escalations`
    - Agregar dados do FinOpsTracker e do trace store
    - Rota `/metrics/costs` restrita a perfil admin
    - Demais rotas acessíveis a rh e admin
    - _Requirements: 8.2, 8.3, 8.4, 8.5, 8.6, 9.3, 9.4_

  - [ ] 6.2 Criar modelo de persistência para contadores de métricas (sessões, perguntas, transbordos) em `app/infrastructure/metrics_store.py`
    - Incrementar contadores no pipeline a cada interação
    - _Requirements: 6.4, 8.4, 8.5, 8.6_

  - [ ]\* 6.3 Escrever testes de propriedade para contabilização de transbordos
    - **Property 15: Contabilização de transbordos no dashboard**
    - **Validates: Requirements 6.4**

- [ ] 7. Expandir API de Gestão de Documentos (CRUD completo)
  - [ ] 7.1 Adicionar rotas `PUT /documents/{source_id}` e `DELETE /documents/{source_id}` em `app/api/routes/documents.py`
    - PUT: re-processa documento (re-chunk + re-index)
    - DELETE: remove chunks do vector store + invalida cache
    - Restrito a perfis rh e admin
    - _Requirements: 10.2, 10.3, 9.5_

  - [ ] 7.2 Implementar versionamento de documentos: tabela `document_versions` + rota `GET /documents/{source_id}/versions`
    - Registrar cada operação (created, updated, deleted) com timestamp e user_id
    - _Requirements: 10.4_

  - [ ] 7.3 Adicionar validação de documento na ingestão: rejeitar documentos vazios/inválidos com erro 422
    - _Requirements: 10.5_

  - [ ]\* 7.4 Escrever testes de propriedade para gestão de documentos
    - **Property 10: Ingestão completa de documentos**
    - **Property 11: Remoção de documento invalida chunks e cache**
    - **Property 12: Versionamento de documentos preserva histórico**
    - **Property 13: Documentos inválidos são rejeitados**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

- [ ] 8. Implementar Controle de Acesso por Perfil nas rotas
  - [ ] 8.1 Criar dependency de autorização reutilizável (`require_roles`) em `app/api/dependencies.py` que verifica o perfil do `UserContext`
    - Aplicar nas rotas: `/metrics/costs` → admin; `/documents/*` CRUD → rh, admin; `/metrics/*` → rh, admin
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

  - [ ]\* 8.2 Escrever testes de propriedade para controle de acesso
    - **Property 9: Controle de acesso por perfil**
    - **Validates: Requirements 11.2, 11.3**

- [ ] 9. Checkpoint — Backend completo
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Frontend — Estrutura base e roteamento por perfil
  - [ ] 10.1 Criar projeto React em `frontend/` (se não existir) com Vite + TypeScript + Tailwind + shadcn/ui
    - Configurar React Router com rotas: `/chat`, `/rh`, `/admin`
    - Criar layout base com autenticação (perfil via contexto)
    - _Requirements: 7.1, 8.1, 9.1, 11.1_

  - [ ] 10.2 Criar tipos TypeScript em `frontend/src/types/index.ts`: `Message`, `MetricsSummary`, `Document`, `EscalationTicket`, `UserProfile`
    - _Requirements: 7.1, 8.1_

  - [ ] 10.3 Criar serviço API (`frontend/src/services/api.ts`) com axios para todas as rotas do backend: `/ask`, `/documents`, `/metrics/*`
    - _Requirements: 7.1, 8.1, 9.1_

- [ ] 11. Frontend — Tela do Colaborador (Chat)
  - [ ] 11.1 Implementar componentes: `ChatWindow`, `MessageList`, `MessageBubble`, `InputBar`
    - MessageList exibe histórico em ordem cronológica
    - InputBar com submit por Enter/botão
    - Loading indicator durante a requisição
    - Exibir fontes citadas abaixo de cada resposta
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]\* 11.2 Escrever testes para ordenação cronológica do histórico
    - **Property 14: Histórico de mensagens em ordem cronológica**
    - **Validates: Requirements 7.2**

- [ ] 12. Frontend — Tela do Admin (Dashboard Completo)
  - [ ] 12.1 Implementar `MetricsDashboard` com painéis: tokens, custos, sessões, perguntas, transbordos
    - Usar React Query para buscar dados das rotas `/metrics/*`
    - Painel de custos visível apenas nesta rota
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ] 12.2 Implementar `DocumentManager` com listagem, upload, edição e remoção de documentos
    - Formulário de upload com campos de metadados
    - Visualização de histórico de versões
    - _Requirements: 8.7, 10.1, 10.2, 10.3, 10.4_

- [ ] 13. Frontend — Tela do RH (Dashboard Parcial)
  - [ ] 13.1 Reutilizar `MetricsDashboard` sem o painel de custos e `DocumentManager` completo
    - Ocultar seção de custos via prop/condição de perfil
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 14. Frontend — Agente de Recepção e integração
  - [ ] 14.1 Exibir mensagem de boas-vindas do Agente_Recepção ao abrir o chat (primeira mensagem da sessão)
    - Integrar com endpoint existente (a recepção já funciona no backend)
    - _Requirements: 1.1, 1.2, 1.4_

  - [ ]\* 14.2 Escrever testes para o Agente de Recepção (backend)
    - **Property 5: Recepção não intercepta mensagens de domínio**
    - **Property 6: Recepção intercepta mensagens sociais**
    - **Validates: Requirements 1.2, 1.3**

- [ ] 15. Checkpoint final — Integração completa
  - Ensure all tests pass, ask the user if questions arise.

## Notas

- Tasks marcadas com `*` são opcionais e podem ser ignoradas para um MVP mais rápido
- Cada task referencia requisitos específicos para rastreabilidade
- O backend já possui a maior parte da infraestrutura (orquestrador, agentes, pipeline RAG, FinOps) — as tasks focam nas adaptações necessárias
- O frontend é a maior parte nova do trabalho
- Hypothesis é a biblioteca de property-based testing para Python; Vitest com fast-check para o frontend
