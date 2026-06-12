# Assistente de RH — Kiro

Sistema de inteligência artificial para atendimento a colaboradores sobre documentos de RH. Utiliza arquitetura RAG (Retrieval Augmented Generation) com múltiplos agentes especializados para responder perguntas com base em documentos oficiais da empresa.

## Problema que Resolve

Organizações de médio e grande porte enfrentam desafios recorrentes no atendimento de dúvidas trabalhistas e de políticas internas:

- **Volume excessivo de demandas** no setor de RH — perguntas repetitivas sobre férias, benefícios, folha de pagamento
- **Tempo de resposta elevado** — colaboradores aguardando dias por informações disponíveis em documentos oficiales
- **Inconsistência nas respostas** — diferentes pessoas informando regras de formas distintas
- **Dificuldade de localização** — documentos tersebar em diferentes sistemas e pastas

O Kiro resolve essas questões oferecendo um assistente disponível 24/7 que responde perguntas com base em documentos oficiais, citando as fontes e com níveis de confiança透明的.

## Como a Solução é Usada

### Fluxo Principal

1. **Usuário faz uma pergunta** — O colaborador acessa a interface e faz uma pergunta sobre RH (ex: "Quantos dias de férias tenho direito?")
2. **Sistema classifica e roteia** — O orquestrador identifica o domínio (benefícios, políticas, recrutamento, etc.) e seleciona o agente especializado
3. **Recupera evidências** — O sistema busca nos documentos indexados trechos relevantes para a pergunta
4. **Gera resposta fundamentada** — O agente gera uma resposta usando apenas as evidências recuperadas
5. **Aplicação de guardrails** — Verifica se a resposta é segura, não contém PII e possui evidências
6. **Retorna resposta** — O usuário recebe a resposta com as fontes consultadas

### Perfis de Usuário

| Perfil         | Acesso                                                   |
| -------------- | -------------------------------------------------------- |
| **Usuário**    | Tela de conversa para perguntas e respostas              |
| **Suporte RH** | Conversa + ingestion de documentos + métricas do sistema |
| **Admin**      | Todas as funcionalidades + custos e tokens usados        |

### Interface

A interface principal é uma aplicação Streamlit que permite:

- Chat conversational com o assistente
- Upload de documentos para a base de conhecimento
- Dashboard de métricas (perguntas, respostas, transbordos)
- Relatório de custos de uso de modelos de IA

## Arquitetura

```
gerador_relatorio_kiro/
├── app/
│   ├── agents/           # Agentes especializados e orquestrador
│   │   ├── orchestrator.py       # Roteamento de perguntas
│   │   ├── query_intelligence.py # Classificação de domínio
│   │   ├── reception_agent.py    # Tratamento de saudações
│   │   ├── benefits_agent.py     # Agente de benefícios
│   │   ├── labor_policy_agent.py # Agente de políticas trabalhistas
│   │   ├── recruiting_agent.py   # Agente de recrutamento
│   │   ├── compliance_agent.py   # Agente de compliance
│   │   └── ...
│   ├── api/              # API FastAPI
│   │   ├── routes/
│   │   │   ├── ask.py           # Endpoint de perguntas
│   │   │   ├── documents.py     # Endpoint de ingestion
│   │   │   ├── metrics.py       # Endpoint de métricas
│   │   │   └── finops.py        # Endpoint de custos
│   │   └── main.py
│   ├── core/             # Configurações e utilitários
│   │   ├── config.py           # Configurações (pydantic-settings)
│   │   ├── model_router.py     # Seleção de modelo LLM
│   │   ├── auth.py             # Autenticação e autorização
│   │   └── models.py           # Modelos de dados
│   ├── rag/              # Pipeline RAG
│   │   └── pipeline.py         # Orquestração completa
│   ├── retrieval/        # Recuperação de documentos
│   │   ├── retriever.py        # Busca em vetores
│   │   └── vector_store.py     # Armazenamento de embeddings
│   ├── guardrails/       # Segurança de entrada/saída
│   │   ├── input_guardrail.py  # Verificação de entrada
│   │   ├── output_guardrail.py # Verificação de saída
│   │   └── pii.py              # Detecção de PII
│   ├── finops/           # Controle de custos
│   │   └── cost.py            # Cálculo e rastreamento
│   ├── observability/    # Logging e tracing
│   │   └── trace.py          # Geração de traces
│   └── evaluation/       # Avaliação de qualidade
├── streamlit/
│   └── app.py            # Interface Streamlit
├── tests/                # Testes automatizados
└── docs/                 # Documentação
```

## Stack Tecnológica

### Backend

- **Python 3.13+** — Linguagem principal
- **FastAPI** — Framework web de alta performance
- **LangChain/LangGraph** — Orquestração de agentes
- **SQLAlchemy 2.0** — ORM para banco de dados
- **Pydantic v2** — Validação de dados
- **structlog** — Logging estruturado

### IA

- **GPT-4o** — Modelo para tarefas complexas
- **MiniMax M2.5** — Modelo econômico para tarefas simples
- **Model Router** — Seleção automática por risco/custo

### Interface

- **Streamlit** — Interface de teste e demonstração
- **React + TypeScript** — Interface web (opcional)

## Modelos de LLM

O sistema seleciona automaticamente o modelo adequado:

| Situação                      | Modelo       | Custo          |
| ----------------------------- | ------------ | -------------- |
| Baixo risco + alta confiança  | MiniMax M2.5 | Gratuito       |
| Médio risco                   | GPT-4o-mini  | $0.00015/1k in |
| Alto risco ou baixa confiança | GPT-4o       | $0.0025/1k in  |

## Configuração

### Variáveis de Ambiente

Copie `.env.example` para `.env`:

```bash
# Obrigatório
OPENAI_API_KEY=sua_chave_aqui

# Opcional
MINIMAX_API_KEY=chave_minimax  # Habilita modelo gratuito
MODEL_SELECTION_STRATEGY=auto   # auto | simple | complex
DATABASE_URL=sqlite:///dev.db
```

### Instalação

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Instalar dependências
uv sync

# ou com extras de desenvolvimento
uv sync --extra dev
```

### Executar

```bash
# Terminal 1: API
uv run uvicorn app.api.main:app --reload

# Terminal 2: Interface
streamlit run streamlit/app.py
```

## Endpoints da API

| Método | Endpoint                  | Descrição           |
| ------ | ------------------------- | ------------------- |
| POST   | `/api/v1/ask`             | Fazer uma pergunta  |
| POST   | `/api/v1/documents`       | Ingerir documento   |
| GET    | `/api/v1/metrics/summary` | Métricas do sistema |
| GET    | `/api/v1/finops/summary`  | Custos e tokens     |
| GET    | `/api/v1/health`          | Health check        |

## Segurança

- **Guardrails de entrada**: Bloqueia requests maliciosos ou proibidos
- **Guardrails de saída**: Verifica se respostas têm evidências
- **Detecção de PII**: Identifica dados pessoais sensíveis
- **Controle de orçamento**: Limita custos por interação
- **RBAC**: Perfis com acesso diferenciado

## Métricas e Observabilidade

O sistema rastreia:

- Total de perguntas respondidas
- Total de respostas geradas
- Taxa de transbordo (revisão humana)
- Custos por modelo e agente
- Latência das respostas
- Cache hits/misses

## Roadmap

- [ ] Autenticação real (JWT/OIDC)
- [ ] Vector store persistente (pgvector/Qdrant)
- [ ] Cache distribuído (Redis)
- [ ] Interface React completa
- [ ] Integração com sistemas de RH

## Licença

MIT License
