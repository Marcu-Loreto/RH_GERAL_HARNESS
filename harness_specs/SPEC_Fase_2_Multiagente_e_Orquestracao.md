# SPEC Fase 2 — Multiagente e Orquestração

## 1. Objetivo da fase

Expandir o MVP para uma arquitetura multiagente com orquestrador capaz de selecionar o agente correto para cada área de RH.

## 2. Escopo

- criação dos agentes especialistas;
- orquestrador multiagente;
- Query Intelligence Layer;
- classificação de domínio;
- query canônica;
- filtros por agente/domínio;
- controle de ferramentas;
- roteamento com confiança;
- fallback para busca ampla;
- observabilidade por agente.

## 3. Agentes previstos

1. Benefícios
2. Trabalhista / Políticas Internas
3. Cargos, Salários e Competências
4. Treinamento e Desenvolvimento
5. Recrutamento e Seleção
6. Compliance e Conduta

## 4. Requisitos funcionais

### RF2.1 — Classificar domínio
O sistema deve classificar a pergunta em um domínio de RH.

### RF2.2 — Gerar query canônica
O sistema deve gerar versão otimizada da pergunta para retrieval.

### RF2.3 — Selecionar agente
O orquestrador deve acionar apenas o agente necessário.

### RF2.4 — Controlar confiança
Se a confiança da classificação for baixa, o sistema deve usar fallback ou pedir esclarecimento.

### RF2.5 — Acionar segundo agente quando necessário
Perguntas multidomínio podem acionar agente auxiliar, com registro explícito da razão.

### RF2.6 — Aplicar filtros por domínio
Cada agente deve consultar somente documentos compatíveis com seu domínio.

### RF2.7 — Registrar decisão do orquestrador
O trace deve registrar domínio, agente escolhido, confiança e motivo da decisão.

## 5. Saída da Query Intelligence Layer

```json
{
  "domain": "",
  "agent": "",
  "canonical_query": "",
  "must_terms": [],
  "metadata_filters": {},
  "risk_level": "baixo|medio|alto",
  "confidence": 0.0,
  "fallback_required": false
}
```

## 6. Critérios de aceite

- cada agente responde apenas seu domínio;
- orquestrador seleciona agente correto em pelo menos 90% dos casos do golden dataset;
- perguntas multidomínio são tratadas corretamente;
- baixa confiança aciona fallback;
- todas as decisões ficam rastreadas;
- testes unitários e de integração passam;
- code review concluído.

## 7. Testes obrigatórios

### Unitários
- classificação de domínio;
- geração de query canônica;
- extração de termos obrigatórios;
- seleção de agente;
- regra de fallback;
- bloqueio de agente fora do escopo.

### Integração
- pergunta de benefícios → agente de benefícios;
- pergunta trabalhista → agente trabalhista;
- pergunta de compliance → agente de compliance;
- pergunta ambígua → fallback;
- pergunta multidomínio → agente principal + auxiliar.

### Testes RAG
- precision@k por agente;
- comparação query original vs query canônica;
- validação de filtros por domínio;
- validação de não vazamento entre domínios.

## 8. Code review obrigatório

Verificar:

- se o orquestrador não chama todos os agentes por padrão;
- se decisões são explicáveis;
- se filtros por domínio são aplicados;
- se existe fallback para baixa confiança;
- se agentes não acessam ferramentas proibidas;
- se traces incluem agente e domínio.

## 9. Métricas da fase

- acurácia de roteamento;
- custo por agente;
- latência por agente;
- taxa de fallback;
- taxa de consultas multidomínio;
- taxa de respostas com evidência.

## 10. Evidências de conclusão

- relatório de acurácia do roteador;
- traces por agente;
- exemplos de perguntas por domínio;
- relatório de testes;
- checklist de code review.
