# Visão Geral — Harness de IA para RH (RH_GERAL_HARNESS)

Documento de apresentação funcional: o problema que a aplicação resolve, como ela
funciona por dentro e como o usuário deve utilizá-la. Para a arquitetura técnica
detalhada, ver [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## 1. O problema que resolve

Áreas de RH recebem, todos os dias, o mesmo tipo de pergunta de colaboradores e
gestores: "quantos dias de férias eu tenho?", "como funciona o banco de horas?",
"posso pedir reembolso de curso?", "como denuncio um caso de assédio?". As
respostas existem — estão em políticas, normas e documentos oficiais — mas:

- estão espalhadas em vários documentos e versões;
- mudam com o tempo (uma política nova substitui a antiga);
- têm níveis de confidencialidade diferentes (nem todo mundo pode ver tudo);
- exigem cuidado em temas sensíveis (demissão, assédio, salário individual).

Responder isso manualmente é lento e inconsistente. Um chatbot genérico, por
outro lado, é arriscado: pode **inventar** respostas (alucinar), vazar informação
restrita ou tratar um tema sensível sem o devido cuidado.

**Este harness resolve isso sendo um assistente de RH que só responde com base em
documentos oficiais aprovados**, sempre citando a evidência, respeitando o perfil
de acesso de quem pergunta, e encaminhando para revisão humana os casos que
exigem cautela. Cada resposta é rastreável e tem custo controlado.

> "Harness" aqui significa um arcabouço de produção: além de responder, o sistema
> mede qualidade, custo e segurança de cada interação.

---

## 2. O que a aplicação faz (em uma frase)

Recebe uma pergunta de RH, encontra os trechos relevantes nos documentos oficiais
da empresa, monta uma resposta fundamentada com as fontes citadas, aplica
guardrails de segurança e governança, e devolve a resposta junto com um registro
rastreável (trace) — ou recusa/encaminha para um humano quando não é seguro
responder.

---

## 3. Princípios de funcionamento

1. **Resposta sempre com evidência.** A resposta é montada a partir dos trechos
   recuperados dos documentos. Se não há documento que sustente a resposta, o
   sistema **não inventa**: devolve uma mensagem segura de "sem evidência" e
   sugere procurar o RH.
2. **Respeito ao perfil de acesso.** O nível de confidencialidade dos documentos
   que cada perfil pode ver é controlado (um colaborador não enxerga conteúdo
   confidencial restrito ao RH/Jurídico).
3. **Apenas documentos vigentes e aprovados.** Documentos em rascunho, expirados
   ou substituídos não entram na resposta.
4. **Cautela em temas sensíveis.** Assédio, discriminação, demissão, salário
   individual etc. acionam revisão humana ou bloqueio, conforme o caso.
5. **Tudo é rastreável e medido.** Cada interação gera um trace (modelo usado,
   custo, latência, fontes, guardrails acionados) e alimenta um relatório de
   custo (FinOps).

> O harness agora utiliza LLM (MiniMax M2.5 para avaliação, GPT-4o para geração
> de respostas complexas) com avaliação semântica LLM-as-judge para medir
> qualidade das respostas. A arquitetura mantém guardrails contra alucinação
> (evidência obrigatória, citação de fontes) e custo controlado via model router.

---

## 4. Como funciona por dentro (o caminho de uma pergunta)

```
Pergunta do usuário
   │
   ▼
1. Guardrail de entrada      → bloqueia prompt injection e pedidos de dado pessoal de terceiros
   │
   ▼
2. Query Intelligence Layer  → classifica o domínio (benefícios, trabalhista, ...), avalia risco e confiança
   │
   ▼
3. Orquestrador + Agente     → escolhe o agente especialista do domínio e recupera evidências (só da área correta)
   │                            (triagem do agente: bloqueio ou recomendação de revisão humana)
   ▼
4. Model Router              → escolhe o modelo por risco/confiança/custo/latência (com fallback)
   │
   ▼
5. Enforcement de orçamento  → se o custo estimado estoura o orçamento, reduz contexto e usa modelo econômico
   │
   ▼
6. Cache semântico seguro    → reutiliza resposta de pergunta equivalente (mesmo domínio, mesma permissão, versão vigente)
   │
   ▼
7. Geração com LLM           → gera resposta fundamentada nos trechos + lista de fontes (evidência obrigatória)
   │
   ▼
8. Guardrail de saída        → reprova resposta sem fonte/evidência
   │
   ▼
9. Human-in-the-loop         → marca requires_human_review em casos sensíveis / baixa confiança / sem evidência
   │
   ▼
Resposta + Trace (observabilidade) + Registro de custo (FinOps)
```

### Os 6 agentes especialistas

Cada domínio de RH tem um agente que só consulta documentos da sua área:

| Agente                   | Domínio                 | Cobre                                                  |
| ------------------------ | ----------------------- | ------------------------------------------------------ |
| `agente_beneficios`      | Benefícios              | férias, vale, plano de saúde, auxílios, licenças       |
| `agente_trabalhista`     | Trabalhista / Políticas | jornada, banco de horas, home office, ponto, atestados |
| `agente_cargos_salarios` | Cargos e Salários       | promoção, níveis, faixa salarial, plano de carreira    |
| `agente_treinamento`     | Treinamento             | cursos, certificações, trilhas, reembolso educacional  |
| `agente_recrutamento`    | Recrutamento            | vagas, processo seletivo, indicação, admissão          |
| `agente_compliance`      | Compliance e Conduta    | ética, denúncias, assédio, conflito de interesse       |

Regras de governança embutidas, por exemplo:

- **Cargos e Salários** bloqueia pedido de salário individual de terceiros.
- **Compliance** e **Trabalhista** recomendam revisão humana em temas sensíveis.
- Perguntas **multidomínio** acionam um agente auxiliar quando o principal não
  encontra evidência; perguntas ambíguas caem em **fallback** de busca ampla.

---

## 5. Como o usuário usa a aplicação

A aplicação é uma **API HTTP** (FastAPI). Hoje a interação é via requisições HTTP
(há documentação interativa em `/docs`). O perfil do usuário é informado pelo
cabeçalho `X-User-Role` (nunca pelo corpo da requisição), com os valores:
`colaborador`, `gestor`, `rh`, `juridico`, `admin`.

### 5.1 Subir a aplicação

```bash
# instalar dependências (uma das opções)
uv sync --extra dev          # via uv (recomendado pelo projeto)
# ou
pip install -r requirements.txt

# (opcional) criar o .env a partir do exemplo — a app roda sem ele
cp .env.example .env

# rodar a API
uv run uvicorn app.api.main:app --reload
# Swagger:    http://127.0.0.1:8000/docs
# Health:     http://127.0.0.1:8000/api/v1/health
```

### 5.2 Fluxo de uso típico

**Passo 1 — Ingerir documentos oficiais (perfil `rh` ou `admin`).**
Antes de perguntar, a base de conhecimento precisa ter documentos _aprovados_.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents \
  -H 'Content-Type: application/json' -H 'X-User-Role: rh' -d '{
  "document": {
    "source_id":"ferias-001","title":"Política de Férias","owner":"rh@empresa.com",
    "area_rh":"beneficios","document_type":"politica","version":"1.0","status":"approved",
    "valid_from":"2025-01-01T00:00:00Z","confidentiality":"interno",
    "language":"pt-BR","hash":"h1"
  },
  "raw_text":"Todo colaborador tem direito a 30 dias de férias por ano após o período aquisitivo."
}'
```

Regras de ingestão: só documentos `status=approved` e com todos os campos
obrigatórios são indexados. Ao reenviar o mesmo `source_id` com uma `version`
nova, a versão antiga é removida e o cache relacionado é **invalidado**
automaticamente (respostas antigas deixam de ser reutilizadas).

**Passo 2 — Perguntar (qualquer perfil).**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ask \
  -H 'Content-Type: application/json' -H 'X-User-Role: colaborador' \
  -d '{"query":"quantos dias de férias eu tenho?","area_rh":"beneficios"}'
```

O campo `area_rh` é opcional (uma dica de domínio); se omitido, o sistema
classifica sozinho. Se informado com um valor inexistente, retorna **erro
controlado (422)**, não um stacktrace.

**Resposta (exemplo simplificado):**

```json
{
  "answer": {
    "answer": "Com base nos documentos oficiais consultados:\n- Todo colaborador tem direito a 30 dias de férias... (fonte: Política de Férias v1.0)",
    "evidence": [
      {
        "source_id": "ferias-001",
        "title": "Política de Férias",
        "version": "1.0",
        "chunk_id": "ferias-001::chunk-0"
      }
    ],
    "confidence": "alta",
    "requires_human_review": false,
    "screening_decision": null,
    "escalation_reason": null
  },
  "blocked": false,
  "guardrails_triggered": [],
  "trace_id": "dc69...",
  "agent": "agente_beneficios",
  "domain": "beneficios"
}
```

Como ler a resposta:

- **`answer.answer`**: o texto da resposta.
- **`answer.evidence`**: as fontes citadas (documento, versão, trecho). Resposta
  sem evidência = sistema não encontrou base e não vai inventar.
- **`confidence`**: `alta` / `media` / `baixa`.
- **`requires_human_review`**: `true` indica que o caso deve ser revisado por uma
  pessoa antes de ser considerado final.
- **`blocked`**: `true` quando a pergunta foi recusada por guardrail/governança.
- **`screening_decision` / `escalation_reason`**: explicam a decisão de risco.
- **`trace_id`**: identificador para rastrear a interação nos logs.

**Passo 3 — Acompanhar custo (perfil `admin`).**

```bash
curl http://127.0.0.1:8000/api/v1/finops/summary -H 'X-User-Role: admin'
```

Retorna custo total, custo por agente/modelo/canal, total de tokens e custo médio
por resposta.

### 5.3 Comportamentos que o usuário vai observar

| Situação                                 | O que acontece                                              |
| ---------------------------------------- | ----------------------------------------------------------- |
| Pergunta normal com documento na base    | Resposta com evidência e confiança                          |
| Pergunta sem documento que sustente      | Mensagem segura "sem evidência" + sugestão de procurar o RH |
| Tentativa de prompt injection            | Bloqueada no guardrail de entrada                           |
| Pedido de salário individual de terceiro | Bloqueado pela triagem do agente                            |
| Tema sensível (assédio, demissão)        | Responde, mas marca `requires_human_review=true`            |
| Pergunta ambígua / fora de escopo        | Fallback de busca ampla; se nada for achado, revisão humana |
| `area_rh` inexistente                    | Erro controlado 422                                         |

---

## 6. Endpoints disponíveis

| Método | Rota                     | Perfil        | Função                               |
| ------ | ------------------------ | ------------- | ------------------------------------ |
| GET    | `/api/v1/health`         | público       | Liveness (app no ar)                 |
| GET    | `/api/v1/ready`          | público       | Readiness (dependências, ex.: banco) |
| POST   | `/api/v1/documents`      | `rh`, `admin` | Ingerir documento aprovado           |
| POST   | `/api/v1/ask`            | qualquer      | Perguntar (resposta com evidência)   |
| GET    | `/api/v1/finops/summary` | `admin`       | Relatório de custo agregado          |

---

## 7. Limites e estágio atual

- **LLM em uso.** O sistema utiliza MiniMax M2.5 (avaliação semântica, tarefas simples)
  e GPT-4o (geração de respostas complexas) com routing automático por
  risco/confiança/custo. Avaliação de qualidade via LLM-as-judge.
- **Armazenamento em memória.** Vector store e cache vivem em memória — os dados
  ingeridos se perdem ao reiniciar a aplicação. Em produção, serão substituídos
  por Vector DB persistente e cache distribuído (Redis).
- **Autenticação mock.** O perfil vem do cabeçalho `X-User-Role`. Em produção,
  será substituído por autenticação real (JWT/OIDC) sem mudar as rotas.

Estado por fase: Fases 0, 1, 2, 3 e 4 (LLM) implementadas; Fase 5 (escala,
produção com Redis e vectorDB persistentes) pendente. Detalhes no
[`README.md`](../README.md).

---

## 8. Resumo rápido

- **Para quem:** colaboradores, gestores e times de RH/Jurídico.
- **O que faz:** responde dúvidas de RH com base em documentos oficiais, citando
  fontes, respeitando acesso e escalando casos sensíveis.
- **Como usar:** ingerir documentos aprovados (RH) → perguntar (`/ask`) →
  acompanhar custo (`/finops/summary`).
- **Diferencial:** segurança e governança de ponta a ponta (evidência obrigatória,
  guardrails, revisão humana, rastreabilidade e controle de custo).
