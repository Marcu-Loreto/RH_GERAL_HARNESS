# Estratégia de Testes — Harness IA RH

## 1. Objetivo

Garantir que cada entrega seja funcional, segura, rastreável, eficiente e compatível com os critérios de qualidade esperados para um sistema RAG corporativo de RH.

## 2. Tipos de teste

### 2.1 Testes unitários
Validam funções isoladas.

Exemplos:

- validação de metadados;
- geração de query canônica;
- classificação de domínio;
- filtros de retrieval;
- cálculo de custo;
- seleção de modelo;
- detecção de PII;
- formatação da resposta.

### 2.2 Testes de integração
Validam o fluxo entre componentes.

Exemplos:

- API → guardrail → retrieval → resposta;
- ingestão → embedding → indexação;
- orquestrador → agente → retriever;
- model router → LLM;
- output guardrail → resposta final;
- observabilidade → trace.

### 2.3 Testes RAG
Validam a qualidade do retrieval e da resposta.

Métricas:

- precision@k;
- recall@k;
- MRR;
- nDCG;
- faithfulness;
- answer relevancy;
- citation accuracy.

### 2.4 Testes de segurança
Validam proteção contra:

- prompt injection;
- jailbreak;
- acesso indevido;
- vazamento de PII;
- consulta a documento proibido;
- revelação de prompt interno;
- resposta sem fonte.

### 2.5 Testes de performance
Validam:

- latência P50/P95/P99;
- tokens por resposta;
- custo por resposta;
- desempenho do Vector DB;
- ganho de cache;
- tempo de ingestão.

### 2.6 Testes de regressão
Executados a cada alteração de:

- prompt;
- política;
- modelo;
- chunking;
- embedding;
- reranking;
- documentos;
- código de retrieval.

## 3. Regra obrigatória por spec

Cada spec criada ou alterada deve conter:

- testes unitários;
- testes de integração;
- critérios de aceite;
- evidências esperadas;
- checklist de code review.

## 4. Cobertura mínima recomendada

- funções críticas: 90%;
- módulos de segurança: 95%;
- retrieval e orquestração: 85%;
- API e integração: 80%.

## 5. Golden dataset

Deve conter perguntas por domínio:

- Benefícios;
- Trabalhista / Políticas;
- Cargos e Salários;
- Treinamento;
- Recrutamento;
- Compliance.

Cada item deve ter:

```json
{
  "question": "",
  "expected_domain": "",
  "expected_agent": "",
  "expected_sources": [],
  "risk_level": "",
  "must_include": [],
  "must_not_include": []
}
```

## 6. Critério de bloqueio de release

Uma release deve ser bloqueada se:

- houver vazamento de PII;
- citation accuracy cair abaixo do limite definido;
- precision@k cair abaixo do limite definido;
- guardrail crítico falhar;
- testes unitários ou integração falharem;
- custo médio aumentar sem justificativa;
- latência P95 exceder SLA;
- code review não for concluído.
