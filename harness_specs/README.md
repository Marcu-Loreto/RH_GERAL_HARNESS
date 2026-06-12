# Harness Completo de IA para RAG Multiagente de RH

Este pacote contém os documentos de produto e engenharia para orientar o desenvolvimento de um assistente corporativo de RH baseado em RAG multiagente, com segurança, governança, observabilidade, avaliação contínua e controle de custo.

## Arquivos incluídos

1. `PRD_Harness_IA_RH.md` — Documento de Produto com problema, objetivo, escopo, personas, funcionalidades, métricas e critérios de sucesso.
2. `SPEC_Fase_0_Fundacao_e_Governanca.md` — Fundação do projeto: arquitetura, repositório, padrões, ambientes, segurança, observabilidade inicial e documentação.
3. `SPEC_Fase_1_MVP_RAG_RH.md` — MVP com RAG para 1 ou 2 áreas de RH, ingestão documental, busca, resposta com evidências e guardrails básicos.
4. `SPEC_Fase_2_Multiagente_e_Orquestracao.md` — Expansão para agentes especialistas, orquestrador, roteamento de consulta e controle por domínio.
5. `SPEC_Fase_3_Harness_Completo.md` — Observabilidade avançada, evaluation harness, model router, cache, FinOps e human-in-the-loop.
6. `SPEC_Fase_4_Producao_Escala_e_Governanca.md` — Prontidão para produção, CI/CD, monitoramento, rollback, segurança, auditoria e operação.
7. `TEST_STRATEGY.md` — Estratégia de testes unitários, integração, RAG, segurança, regressão, performance e aceite.
8. `CODE_REVIEW_GUIDELINES.md` — Checklist obrigatório de code review por pull request e por fase.
9. `EVALUATION_HARNESS.md` — Métricas, golden dataset, critérios de avaliação e monitoramento de qualidade.
10. `BACKLOG_INICIAL.md` — Backlog sugerido em épicos, features e histórias de usuário.
11. `DATA_MODEL_AND_METADATA.md` — Modelo de metadados para documentos, chunks, traces, usuários, permissões e respostas.
12. `PROMPTS_AND_POLICIES.md` — Prompts iniciais, políticas de segurança, regras de resposta e instruções de guardrails.

## Instrução geral para desenvolvimento assistido por IA

Cada spec deve ser tratada como uma unidade de entrega incremental. Para cada entrega gerada por IA ou desenvolvedor, são obrigatórios:

- code review;
- testes unitários;
- testes de integração;
- atualização da documentação;
- validação dos critérios de aceite;
- registro de decisões técnicas;
- validação de segurança básica;
- validação de custo/performance quando aplicável.

Nenhuma fase deve ser considerada concluída sem evidências de teste e revisão.
