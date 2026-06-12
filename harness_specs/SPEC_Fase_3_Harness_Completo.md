# SPEC Fase 3 — Harness Completo

## 1. Objetivo da fase

Adicionar os elementos de Harness completo: observabilidade avançada, evaluation harness, model router, cache, FinOps, policy registry, prompt registry e human-in-the-loop.

## 2. Escopo

- Langfuse self-hosted;
- OpenTelemetry;
- Phoenix opcional;
- evaluation harness;
- golden dataset expandido;
- model router;
- cache semântico;
- FinOps dashboard;
- human-in-the-loop;
- prompt registry;
- policy registry;
- guardrails avançados.

## 3. Requisitos funcionais

### RF3.1 — Observabilidade LLM/RAG
Registrar traces completos com agente, modelo, prompt, documentos, chunks, tokens, custo e latência.

### RF3.2 — Evaluation Harness
Executar testes de qualidade com golden dataset antes de cada release.

### RF3.3 — Model Router
Selecionar modelo conforme risco, complexidade, custo e latência.

### RF3.4 — Cache semântico
Reaproveitar respostas para perguntas equivalentes quando documentos e permissões forem compatíveis.

### RF3.5 — FinOps
Monitorar custo por agente, modelo, canal e pergunta.

### RF3.6 — Human-in-the-loop
Encaminhar casos sensíveis, baixa confiança ou ausência de evidência para revisão humana.

### RF3.7 — Prompt Registry
Versionar prompts por agente e bloquear alteração sem aprovação.

### RF3.8 — Policy Registry
Versionar políticas de acesso, guardrails e regras de risco.

## 4. Regras de roteamento de modelo

| Condição | Ação |
|---|---|
| pergunta simples e baixo risco | modelo econômico |
| pergunta média | modelo intermediário |
| pergunta de alto risco | modelo robusto |
| baixa confiança | modelo robusto + revisão humana |
| indisponibilidade | fallback |
| custo acima do limite | reduzir contexto ou usar cache |

## 5. Critérios de aceite

- traces completos disponíveis;
- golden dataset executado automaticamente;
- custo por resposta calculado;
- model router funcionando;
- cache semântico com validação de permissão;
- casos sensíveis são escalados;
- prompts e políticas versionados;
- testes passam;
- code review concluído.

## 6. Testes obrigatórios

### Unitários
- cálculo de custo;
- seleção de modelo;
- validação de cache;
- invalidação de cache por versão de documento;
- criação de trace;
- validação de prompt versionado;
- regra de human-in-the-loop.

### Integração
- fluxo completo com observabilidade;
- chamada de modelo via router;
- cache hit e cache miss;
- escalonamento humano;
- execução de golden dataset;
- policy registry aplicado.

### Testes de avaliação
- precision@k;
- faithfulness;
- citation accuracy;
- latência;
- custo médio;
- taxa de fallback;
- taxa de revisão humana.

## 7. Code review obrigatório

Verificar:

- se traces não registram PII indevida;
- se cache considera perfil de acesso;
- se model router possui fallback;
- se prompt registry impede alteração informal;
- se custos são medidos corretamente;
- se testes de regressão foram executados;
- se human-in-the-loop não expõe dados sensíveis.

## 8. Métricas da fase

- custo médio por resposta;
- tokens por resposta;
- cache hit rate;
- latência P95;
- taxa de escalonamento humano;
- taxa de bloqueio por guardrail;
- faithfulness;
- citation accuracy;
- regressão por release.

## 9. Evidências de conclusão

- dashboard de observabilidade;
- relatório de avaliação;
- relatório de custo;
- exemplos de cache;
- exemplos de escalonamento humano;
- checklist de code review;
- relatório de testes.
