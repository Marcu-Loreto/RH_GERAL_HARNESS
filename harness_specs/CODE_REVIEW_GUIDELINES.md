# Diretrizes de Code Review

## 1. Objetivo

Garantir que todo código, prompt, política, pipeline ou alteração documental passe por revisão antes de entrar no sistema.

## 2. Regra obrigatória

Nenhuma entrega deve ser aceita sem:

- pull request;
- code review;
- testes unitários;
- testes de integração;
- evidência de execução;
- atualização documental;
- verificação de segurança.

## 3. Checklist geral

### Código

- [ ] Código legível e modular.
- [ ] Sem duplicação excessiva.
- [ ] Nomes claros.
- [ ] Erros tratados.
- [ ] Logs estruturados.
- [ ] Sem secrets no código.
- [ ] Sem dados sensíveis em logs.
- [ ] Configuração por ambiente.

### Testes

- [ ] Testes unitários criados/atualizados.
- [ ] Testes de integração criados/atualizados.
- [ ] Testes negativos incluídos.
- [ ] Testes de segurança quando aplicável.
- [ ] Evidência de execução anexada.
- [ ] Golden dataset executado quando aplicável.

### RAG

- [ ] Retrieval usa filtros por metadados.
- [ ] Documentos obsoletos são bloqueados.
- [ ] Resposta exige evidência.
- [ ] Top-k e reranking são controlados.
- [ ] Query original preservada como fallback quando necessário.
- [ ] Não há acesso indevido entre domínios.

### Agentes

- [ ] Agente possui escopo claro.
- [ ] Agente não acessa ferramenta proibida.
- [ ] Orquestrador não chama todos os agentes sem necessidade.
- [ ] Decisão de roteamento é rastreável.
- [ ] Baixa confiança possui fallback.

### Guardrails

- [ ] Input guardrail testado.
- [ ] Retrieval guardrail testado.
- [ ] Output guardrail testado.
- [ ] Prompt injection tratado.
- [ ] PII tratada.
- [ ] Resposta sem fonte é bloqueada.

### Observabilidade

- [ ] Trace ID gerado.
- [ ] Session ID registrado.
- [ ] Modelo registrado.
- [ ] Agente registrado.
- [ ] Tokens registrados.
- [ ] Custo registrado.
- [ ] Latência registrada.
- [ ] Guardrails acionados registrados.

### Custo e performance

- [ ] Impacto de tokens avaliado.
- [ ] Impacto de latência avaliado.
- [ ] Cache considerado quando aplicável.
- [ ] Modelo econômico usado quando possível.
- [ ] Sem chamadas redundantes de LLM.

## 4. Checklist para prompts

- [ ] Prompt versionado.
- [ ] Owner definido.
- [ ] Escopo claro.
- [ ] Regras de não invenção.
- [ ] Regras de evidência.
- [ ] Regras de recusa segura.
- [ ] Proteção contra tentativa de alteração pelo usuário.
- [ ] Testado contra golden dataset.
- [ ] Aprovado pelo responsável.

## 5. Checklist para documentos

- [ ] Documento possui owner.
- [ ] Versão definida.
- [ ] Vigência definida.
- [ ] Status aprovado.
- [ ] Confidencialidade definida.
- [ ] Área de RH definida.
- [ ] Sem PII indevida.
- [ ] Indexado em staging antes da produção.

## 6. Critério de reprovação automática

Reprovar PR se houver:

- segredo exposto;
- ausência de testes;
- ausência de evidência;
- resposta sem fonte;
- bypass de guardrail;
- acesso indevido;
- prompt não versionado;
- documento sem metadados mínimos;
- alteração crítica sem avaliação de regressão.
