# SPEC Fase 1 — MVP RAG de RH

## 1. Objetivo da fase

Construir um MVP funcional de RAG para uma ou duas áreas de RH, preferencialmente Benefícios e Políticas Internas.

## 2. Escopo

- ingestão de documentos aprovados;
- extração e chunking;
- geração de embeddings;
- armazenamento em Vector DB;
- busca por metadados;
- busca híbrida simples;
- resposta com evidência;
- guardrails básicos de entrada e saída;
- observabilidade básica;
- golden dataset inicial.

## 3. Fora de escopo

- seis agentes completos;
- GraphRAG;
- automações avançadas;
- integração completa com sistemas de RH;
- revisão humana operacional completa;
- model router avançado.

## 4. Fluxo esperado

```text
Usuário
→ API
→ Guardrail de entrada
→ Interpretação simples da pergunta
→ Retrieval filtrado
→ Geração de resposta
→ Guardrail de saída
→ Resposta com evidência
→ Registro de trace
```

## 5. Requisitos funcionais

### RF1.1 — Ingerir documentos
O sistema deve permitir ingestão de documentos de RH com metadados obrigatórios.

### RF1.2 — Gerar chunks
O sistema deve dividir documentos em trechos semanticamente úteis.

### RF1.3 — Gerar embeddings
O sistema deve gerar vetores dos chunks e armazená-los no Vector DB.

### RF1.4 — Consultar documentos
O sistema deve buscar trechos relevantes com base na pergunta do usuário.

### RF1.5 — Filtrar por metadados
A busca deve filtrar por área de RH, vigência, status aprovado e confidencialidade.

### RF1.6 — Responder com evidência
A resposta deve indicar fonte, versão e trecho de referência.

### RF1.7 — Bloquear pergunta indevida
O sistema deve bloquear perguntas com tentativa de prompt injection, PII indevida ou fora de escopo.

### RF1.8 — Validar saída
A saída deve ser validada contra grounding, presença de fonte, PII e formato.

### RF1.9 — Registrar observabilidade
Registrar pergunta, documentos recuperados, tokens, latência e resposta.

## 6. Modelo de resposta

```json
{
  "answer": "",
  "evidence": [
    {
      "source_id": "",
      "title": "",
      "version": "",
      "chunk_id": "",
      "summary": ""
    }
  ],
  "confidence": "alta|media|baixa",
  "limitations": "",
  "requires_human_review": false
}
```

## 7. Critérios de aceite

- documentos aprovados são ingeridos com metadados;
- perguntas simples retornam resposta com fonte;
- perguntas sem evidência retornam mensagem de limitação;
- input guardrail bloqueia ataques básicos;
- output guardrail bloqueia resposta sem fonte;
- logs e traces são registrados;
- golden dataset inicial roda com sucesso;
- testes unitários e de integração passam;
- code review concluído.

## 8. Testes obrigatórios

### Unitários
- validação de metadados;
- chunking;
- geração de payload;
- filtro por área;
- detector simples de prompt injection;
- detector simples de PII;
- formatação da resposta.

### Integração
- ingestão → embedding → indexação;
- pergunta → retrieval → resposta;
- guardrail de entrada → bloqueio;
- guardrail de saída → reprovação;
- trace completo por requisição.

### Testes RAG
- precision@5 no golden dataset;
- verificação de fonte esperada;
- verificação de resposta sem alucinação evidente;
- fallback quando não houver documento.

## 9. Code review obrigatório

Verificar:

- se o retrieval usa filtros;
- se a resposta exige evidência;
- se não há segredo em logs;
- se erros são tratados;
- se testes cobrem fluxos positivos e negativos;
- se prompts estão versionados;
- se documentos obsoletos são bloqueados.

## 10. Métricas mínimas da fase

- precision@5 inicial;
- taxa de resposta com fonte;
- latência média;
- tokens por resposta;
- perguntas bloqueadas por guardrail;
- perguntas sem evidência.

## 11. Evidências de conclusão

- relatório do golden dataset;
- relatório de testes;
- print ou export dos traces;
- checklist de code review;
- lista de documentos ingeridos;
- exemplos de respostas corretas e recusas seguras.
