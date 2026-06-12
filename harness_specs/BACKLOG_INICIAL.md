# Backlog Inicial

## Épico 1 — Fundação

### História 1.1 — Estrutura do projeto

Como time de desenvolvimento, quero uma estrutura modular para implementar API, agentes, retrieval, guardrails, ingestão e avaliação.

Critérios de aceite:

- estrutura de pastas criada;
- health check funcionando;
- testes unitários básicos;
- code review concluído.

### História 1.2 — Configuração segura

Como operador, quero configurar o sistema por variáveis de ambiente para não expor credenciais.

Critérios de aceite:

- `.env.example`;
- validação de variáveis obrigatórias;
- secrets ausentes do repositório.

## Épico 2 — RAG MVP

### História 2.1 — Ingestão de documentos

Como RH, quero carregar documentos aprovados para que o assistente responda com base em fontes oficiais.

Critérios de aceite:

- documento com metadados;
- chunking executado;
- embedding gerado;
- indexação concluída;
- testes unitários e integração.

### História 2.2 — Consulta com evidência

Como colaborador, quero receber resposta com fonte para confiar na orientação.

Critérios de aceite:

- resposta com evidência;
- resposta sem fonte bloqueada;
- trace registrado.

## Épico 3 — Segurança

### História 3.1 — Guardrail de entrada

Como empresa, quero bloquear perguntas indevidas para reduzir risco.

Critérios de aceite:

- prompt injection bloqueado;
- PII sensível bloqueada;
- fora de escopo tratado.

### História 3.2 — Guardrail de saída

Como empresa, quero validar respostas antes da entrega.

Critérios de aceite:

- grounding validado;
- PII detectada;
- resposta sem citação reprovada.

## Épico 4 — Multiagente

### História 4.1 — Roteamento por domínio

Como usuário, quero que minha pergunta seja enviada ao especialista correto.

Critérios de aceite:

- domínio classificado;
- agente acionado;
- decisão registrada.

### História 4.2 — Agentes especialistas

Como RH, quero agentes por área para respostas mais precisas.

Critérios de aceite:

- agentes criados;
- filtros por domínio;
- testes por agente.

## Épico 5 — Harness completo

### História 5.1 — Observabilidade

Como gestor, quero monitorar custo, tokens, latência e qualidade.

Critérios de aceite:

- traces completos;
- dashboard inicial;
- custo registrado.

### História 5.2 — Evaluation Harness

Como product owner, quero detectar regressão antes de publicar mudanças.

Critérios de aceite:

- golden dataset;
- métricas calculadas;
- release bloqueada em regressão.

### História 5.3 — Human-in-the-loop

Como RH, quero revisar casos sensíveis.

Critérios de aceite:

- baixa confiança escalada;
- caso crítico registrado;
- resposta segura enviada.
