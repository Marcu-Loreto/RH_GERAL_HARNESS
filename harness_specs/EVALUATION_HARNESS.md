# Evaluation Harness

## 1. Objetivo

Medir continuamente se o sistema está recuperando os documentos corretos, respondendo com fidelidade e mantendo custo e latência dentro dos limites esperados.

## 2. Avaliações principais

### Retrieval

- precision@k;
- recall@k;
- MRR;
- nDCG;
- cobertura por domínio;
- fonte esperada recuperada.

### Resposta

- faithfulness;
- answer relevancy;
- citation accuracy;
- completude;
- clareza;
- limitação explícita quando necessário.

### Segurança

- prompt injection block rate;
- jailbreak block rate;
- PII leakage rate;
- acesso indevido bloqueado;
- resposta sem fonte bloqueada.

### Eficiência

- custo médio por resposta;
- tokens médios por resposta;
- latência P50/P95/P99;
- cache hit rate;
- custo por agente.

## 3. Golden dataset

O golden dataset deve conter exemplos representativos por domínio e risco.

Campos:

```json
{
  "id": "",
  "question": "",
  "expected_domain": "",
  "expected_agent": "",
  "expected_sources": [],
  "risk_level": "",
  "expected_behavior": "answer|refuse|human_review|clarify",
  "must_include": [],
  "must_not_include": []
}
```

## 4. Execução obrigatória

Executar evaluation harness quando houver alteração em:

- prompt;
- política;
- modelo;
- embedding;
- chunking;
- reranking;
- documentos;
- guardrails;
- código de retrieval;
- orquestrador.

## 5. Limiares iniciais sugeridos

- acurácia de roteamento: >= 90%;
- precision@5: >= 85%;
- citation accuracy: >= 95%;
- faithfulness: >= 90%;
- PII leakage: 0;
- prompt injection crítico bloqueado: >= 95%;
- latência P95 para perguntas comuns: <= 10 segundos.

## 6. Relatório de avaliação

Cada execução deve gerar:

- data;
- versão do código;
- versão dos prompts;
- versão dos documentos;
- modelo usado;
- resultados por métrica;
- regressões detectadas;
- aprovação ou bloqueio da release.
