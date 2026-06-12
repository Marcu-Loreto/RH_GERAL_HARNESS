# SPEC Fase 0 — Fundação, Arquitetura e Governança

## 1. Objetivo da fase

Criar a base técnica e organizacional do projeto, preparando o ambiente para desenvolvimento seguro, rastreável e testável.

## 2. Escopo

- estrutura inicial do repositório;
- padrões de código;
- configuração de ambientes;
- estrutura de documentação;
- autenticação básica;
- logging inicial;
- rastreamento com trace ID;
- definição dos metadados documentais;
- definição dos agentes previstos;
- definição de critérios de teste e code review.

## 3. Entregáveis

- repositório inicial;
- estrutura de pastas;
- arquivo `.env.example`;
- configuração de lint e formatação;
- pipeline básico de CI;
- documentação de arquitetura inicial;
- modelo inicial de metadados;
- checklist de code review;
- estratégia inicial de testes.

## 4. Estrutura sugerida do repositório

```text
project/
  app/
    api/
    agents/
    retrieval/
    guardrails/
    ingestion/
    observability/
    evaluation/
    core/
  tests/
    unit/
    integration/
    rag/
    security/
  docs/
  prompts/
  policies/
  datasets/
  scripts/
  infra/
```

## 5. Requisitos funcionais

### RF0.1 — Criar base do projeto
O sistema deve ter estrutura organizada para API, agentes, retrieval, guardrails, ingestão, observabilidade e avaliação.

### RF0.2 — Criar configuração de ambiente
O sistema deve usar variáveis de ambiente e arquivo `.env.example`, sem credenciais reais versionadas.

### RF0.3 — Criar logging estruturado
Cada requisição deve gerar `trace_id`, `session_id` e logs rastreáveis.

### RF0.4 — Criar padrão de metadados
Definir campos mínimos para documentos, chunks, usuários, permissões e respostas.

### RF0.5 — Criar pipeline mínimo de CI
Cada pull request deve executar lint, testes unitários e verificação de segurança básica.

## 6. Requisitos não funcionais

- código modular;
- baixo acoplamento;
- configuração por ambiente;
- documentação mínima por módulo;
- sem secrets no repositório;
- logs sem dados sensíveis.

## 7. Critérios de aceite

- projeto executa localmente;
- testes unitários de exemplo passam;
- lint executa com sucesso;
- `.env.example` disponível;
- documentação inicial criada;
- trace ID gerado por requisição;
- code review checklist disponível.

## 8. Testes obrigatórios

### Unitários
- geração de trace ID;
- carregamento de configuração;
- validação de metadados;
- sanitização básica de entrada.

### Integração
- health check da API;
- conexão com banco de metadados;
- execução do pipeline mínimo de CI.

## 9. Code review obrigatório

Cada PR desta fase deve verificar:

- ausência de credenciais;
- organização da estrutura;
- clareza dos nomes;
- tratamento de erro;
- cobertura mínima dos testes;
- aderência à arquitetura definida.

## 10. Evidências de conclusão

- print/log do CI passando;
- relatório de testes;
- checklist de code review preenchido;
- documentação atualizada.
