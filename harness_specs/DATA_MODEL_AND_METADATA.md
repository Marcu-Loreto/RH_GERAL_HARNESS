# Modelo de Dados e Metadados

## 1. Documento

```json
{
  "source_id": "",
  "title": "",
  "owner": "",
  "area_rh": "",
  "document_type": "",
  "version": "",
  "status": "draft|approved|deprecated|archived",
  "valid_from": "",
  "valid_until": "",
  "confidentiality": "publico|interno|restrito|confidencial",
  "language": "pt-BR",
  "created_at": "",
  "updated_at": "",
  "hash": ""
}
```

## 2. Chunk

```json
{
  "chunk_id": "",
  "source_id": "",
  "title": "",
  "section": "",
  "text": "",
  "token_count": 0,
  "embedding_model": "",
  "area_rh": "",
  "document_type": "",
  "version": "",
  "valid_from": "",
  "valid_until": "",
  "confidentiality": "",
  "status": "approved",
  "hash": ""
}
```

## 3. Usuário

```json
{
  "user_id": "",
  "role": "colaborador|gestor|rh|juridico|admin",
  "department": "",
  "access_level": "",
  "location": "",
  "tenant_id": ""
}
```

## 4. Permissão

```json
{
  "role": "",
  "allowed_confidentiality": [],
  "allowed_domains": [],
  "denied_domains": [],
  "requires_human_review": false
}
```

## 5. Trace

```json
{
  "trace_id": "",
  "session_id": "",
  "user_id": "",
  "channel": "",
  "original_query": "",
  "canonical_query": "",
  "domain": "",
  "agent": "",
  "model": "",
  "input_tokens": 0,
  "output_tokens": 0,
  "estimated_cost": 0,
  "latency_ms": 0,
  "retrieved_chunks": [],
  "guardrails_triggered": [],
  "final_confidence": "",
  "requires_human_review": false,
  "created_at": ""
}
```

## 6. Resposta

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

## 7. Campos obrigatórios para indexação

Um documento só pode ser indexado se possuir:

- source_id;
- title;
- owner;
- area_rh;
- document_type;
- version;
- status approved;
- valid_from;
- confidentiality;
- language;
- hash.
