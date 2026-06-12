# SPEC Fase 4 — Produção, Escala e Governança

## 1. Objetivo da fase

Preparar a solução para produção controlada, com segurança, escala, operação, governança, auditoria e melhoria contínua.

## 2. Escopo

- CI/CD completo;
- ambientes dev, staging e produção;
- monitoramento operacional;
- rollback;
- backup;
- auditoria;
- SLA;
- hardening de segurança;
- gestão de incidentes;
- operação assistida;
- plano de melhoria contínua.

## 3. Requisitos funcionais

### RF4.1 — Ambientes separados
O sistema deve ter ambientes separados para desenvolvimento, homologação e produção.

### RF4.2 — CI/CD com gates
Publicações devem passar por testes, avaliação RAG, revisão e aprovação.

### RF4.3 — Rollback
Toda alteração de prompt, política, embedding, chunking ou documento deve permitir rollback.

### RF4.4 — Auditoria
Toda resposta deve ser auditável.

### RF4.5 — Monitoramento
O sistema deve monitorar disponibilidade, latência, custo, qualidade e segurança.

### RF4.6 — Gestão de incidentes
Deve haver processo para incidentes de segurança, qualidade ou custo.

### RF4.7 — Backup e recuperação
Documentos, metadados, prompts, políticas e traces críticos devem ter estratégia de backup.

## 4. Gates de release

Antes de produção, cada release deve passar por:

- testes unitários;
- testes de integração;
- testes de segurança;
- evaluation harness;
- validação de custo;
- code review;
- aprovação de owner;
- plano de rollback.

## 5. Critérios de aceite

- CI/CD funcional;
- staging separado de produção;
- rollback testado;
- dashboard operacional disponível;
- alertas configurados;
- política de incidentes documentada;
- backup validado;
- logs auditáveis;
- code review obrigatório ativo.

## 6. Testes obrigatórios

### Unitários
- regras de configuração;
- validação de feature flags;
- versionamento;
- rollback lógico.

### Integração
- deploy em staging;
- promoção para produção;
- rollback;
- backup/restore;
- alertas;
- autenticação/autorização.

### Performance
- carga de consultas;
- latência P95/P99;
- consumo de tokens;
- custo sob volume;
- cache sob carga.

### Segurança
- prompt injection suite;
- PII leakage;
- acesso indevido;
- rate limit;
- logs sem dados sensíveis.

## 7. Code review obrigatório

Verificar:

- evidência de testes;
- plano de rollback;
- impacto de custo;
- impacto de latência;
- segurança;
- documentação operacional;
- owners e aprovações;
- compatibilidade com produção.

## 8. Métricas de produção

- disponibilidade;
- latência P50/P95/P99;
- custo diário/mensal;
- incidentes;
- taxa de respostas com fonte;
- taxa de human-in-the-loop;
- feedback positivo;
- regressões detectadas;
- uso por canal.

## 9. Evidências de conclusão

- release notes;
- relatório de testes;
- aprovação de produção;
- dashboard operacional;
- plano de rollback;
- documentação de suporte;
- checklist de go-live.
