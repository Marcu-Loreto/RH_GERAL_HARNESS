# PRD — Harness Completo de IA para RAG Multiagente de RH

## 1. Visão geral

O projeto tem como objetivo construir um assistente corporativo de RH capaz de responder perguntas de colaboradores, gestores e profissionais de Recursos Humanos com base em documentos oficiais, políticas vigentes e fontes autorizadas da organização.

A solução deve funcionar como um canal único de orientação, reduzindo dúvidas repetitivas, melhorando a consistência das respostas, aumentando a rastreabilidade e protegendo dados sensíveis.

## 2. Problema

As informações de RH costumam estar espalhadas em múltiplos documentos, canais e sistemas. Isso gera:

- dificuldade para localizar informações corretas;
- respostas inconsistentes entre áreas;
- sobrecarga do time de RH com dúvidas repetitivas;
- risco de uso de documentos vencidos;
- exposição indevida de dados sensíveis;
- ausência de rastreabilidade sobre a origem da resposta;
- demora para orientar colaboradores e gestores.

## 3. Objetivo do produto

Criar uma solução de IA corporativa que:

- responda perguntas de RH com base em documentos oficiais;
- cite as evidências utilizadas;
- informe limitações e nível de confiança;
- bloqueie perguntas indevidas ou sensíveis;
- encaminhe casos críticos para revisão humana;
- monitore custo, qualidade, latência e segurança;
- permita evolução controlada por fases.

## 4. Usuários-alvo

### Colaborador
Busca respostas sobre benefícios, férias, banco de horas, políticas internas, treinamentos e procedimentos.

### Gestor
Busca orientações sobre políticas, elegibilidade, processos de RH, desenvolvimento de equipe e regras corporativas.

### Profissional de RH
Usa a solução como apoio ao atendimento, triagem, consulta documental e padronização de respostas.

### Jurídico / Compliance
Atua na revisão de casos sensíveis, políticas de risco e validação de respostas em temas críticos.

## 5. Escopo do produto

### Incluído

- assistente conversacional de RH;
- RAG com documentos internos;
- agentes especialistas por domínio;
- orquestrador multiagente;
- guardrails de entrada, retrieval e saída;
- política de acesso por perfil;
- resposta com evidência;
- observabilidade open source;
- avaliação contínua;
- human-in-the-loop;
- controle de custo e tokens;
- pipeline de ingestão documental;
- versionamento de prompts e políticas.

### Fora do escopo inicial

- decisão automática de demissão, promoção ou punição;
- parecer jurídico definitivo;
- acesso irrestrito a dados pessoais;
- fine-tuning no MVP;
- GraphRAG obrigatório na primeira versão;
- integração completa com todos os sistemas de RH no MVP;
- substituição do time de RH.

## 6. Proposta de solução em linguagem simples

O usuário faz uma pergunta. O sistema verifica se ela é segura e se está dentro do escopo. Depois, identifica qual área de RH deve responder. Em seguida, consulta somente documentos oficiais, vigentes e permitidos para aquele usuário. A resposta é criada com base nesses documentos e passa por uma validação antes de ser entregue. Se o sistema não encontrar evidência suficiente ou se a pergunta for sensível, ele informa a limitação e recomenda revisão humana.

## 7. Funcionalidades principais

### 7.1 Entrada segura
O sistema deve analisar perguntas antes de processá-las, bloqueando tentativas de manipulação, pedidos de dados pessoais indevidos ou perguntas fora de escopo.

### 7.2 Interpretação da pergunta
O sistema deve identificar intenção, domínio de RH, termos importantes, risco e filtros de consulta.

### 7.3 Orquestração por agentes
O sistema deve acionar o agente correto, evitando que todos os agentes sejam chamados sem necessidade.

### 7.4 Consulta documental
O sistema deve recuperar trechos relevantes de documentos oficiais usando busca híbrida, filtros por metadados, reranking e compressão de contexto.

### 7.5 Resposta com evidência
A resposta deve conter origem documental, limitações, nível de confiança e indicação de revisão humana quando necessário.

### 7.6 Observabilidade
Toda interação deve ser rastreável: pergunta, agente, modelo, documentos usados, custo, tokens, latência e guardrails acionados.

### 7.7 Avaliação contínua
O produto deve ser testado continuamente com perguntas padrão para evitar regressão de qualidade.

### 7.8 Governança documental
Somente documentos aprovados, vigentes e classificados corretamente devem entrar na base de conhecimento.

## 8. Métricas de sucesso

### Negócio
- redução de chamados repetitivos de RH;
- tempo médio de resposta;
- taxa de resolução sem intervenção humana;
- satisfação do usuário;
- redução de retrabalho;
- adoção por canal.

### Qualidade
- acurácia de roteamento por domínio;
- precision@k do retrieval;
- faithfulness da resposta;
- citation accuracy;
- taxa de respostas sem evidência;
- taxa de revisão humana.

### Segurança
- tentativas de prompt injection bloqueadas;
- incidentes de PII;
- respostas bloqueadas por guardrail;
- acesso negado corretamente por política.

### Custo e performance
- custo médio por resposta;
- tokens por resposta;
- latência P50/P95/P99;
- cache hit rate;
- custo por agente;
- custo por canal.

## 9. Critérios de aceite do produto

O produto será considerado apto para piloto quando:

- responder perguntas simples com evidência documental;
- bloquear solicitações proibidas;
- recuperar documentos corretos e vigentes;
- indicar limitação quando não houver evidência;
- registrar trace completo de cada interação;
- passar no golden dataset inicial;
- possuir testes unitários e de integração;
- passar por code review;
- ter documentação mínima de operação.

## 10. Requisitos obrigatórios de engenharia

Para cada fase e cada feature:

- criar testes unitários;
- criar testes de integração;
- executar code review;
- registrar decisões técnicas;
- atualizar documentação;
- validar critérios de aceite;
- medir impacto em custo e latência quando aplicável;
- não aceitar código sem evidência de teste;
- não aceitar mudança de prompt, política ou chunking sem avaliação de regressão.

## 11. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Resposta sem fonte | citação obrigatória e output guardrails |
| Documento obsoleto | ingestion harness com metadados e vigência |
| Vazamento de dados | PII detection, RBAC/ABAC e guardrails |
| Alto custo | model router, cache e compressão |
| Baixa qualidade | golden dataset e evaluation harness |
| Uso indevido | autenticação, rate limit e input guardrails |
| Regressão | testes automatizados e avaliação offline |

## 12. Roadmap

1. Fase 0 — Fundação e governança
2. Fase 1 — MVP RAG de RH
3. Fase 2 — Multiagente e orquestração
4. Fase 3 — Harness completo
5. Fase 4 — Produção, escala e governança
