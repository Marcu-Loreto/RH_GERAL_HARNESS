# Convenções do Projeto — Referência para Code Review

Este documento detalha as convenções específicas que devem ser verificadas durante code review neste projeto.

## Python Backend

### Formatação e Linting

- **black**: line-length=100, target-version py311
- **ruff**: line-length=100, regras padrão + isort
- **mypy**: strict mode (disallow_untyped_defs, no_implicit_optional, etc.)

### Imports

- Usar `from __future__ import annotations` em todo módulo
- Imports absolutos: `from app.core.config import get_settings`
- Nunca importar variáveis de ambiente diretamente — usar `get_settings()`
- Ordem: stdlib → third-party → local (ruff/isort cuida disso)

### Configuração

- Toda config via `get_settings()` (singleton cacheado com lru_cache)
- Nunca `os.environ["X"]` ou `os.getenv("X")` em módulos de negócio
- Secrets nunca hardcoded — sempre via .env / variável de ambiente

### Logging

- Usar `from app.core.logging import get_logger`
- Instanciar: `logger = get_logger(__name__)`
- Logar com keyword args: `logger.info("event_name", key=value, other=value)`
- Nunca logar PII (nomes, emails, CPFs, tokens)
- Nunca usar print() em código de produção

### Modelos e Validação

- Pydantic v2 para todos os modelos de dados
- Usar `model_config = ConfigDict(...)` (não class Config)
- Type hints obrigatórios em todas as funções públicas
- StrEnum para enumerações com valor string

### Tratamento de Erros

- Nunca bare `except:` — sempre especificar o tipo
- `except Exception` apenas com `# noqa: BLE001` e justificativa
- HTTPException com status code e mensagem clara nas rotas
- Erros de negócio retornam modelos estruturados, não strings

### Testes

- Estrutura espelha src/: `tests/unit/`, `tests/integration/`, `tests/security/`
- Markers: `@pytest.mark.unit`, `@pytest.mark.integration`
- Property-based testing com Hypothesis para lógica crítica
- Fixtures em conftest.py, não duplicadas entre arquivos
- Assertions específicas — não apenas `assert result` (verificar conteúdo)

### Segurança

- Input validation via Pydantic em toda rota
- Sanitização com bleach para conteúdo user-generated
- JWT via python-jose, senhas via passlib/bcrypt
- Headers de segurança habilitados (configurável)
- Rate limiting por padrão
- Detecção de prompt injection para inputs de LLM
- Nunca expor stacktrace cru ao cliente (usar HTTPException controlado)

### Padrões Arquiteturais

- Agentes estendem BaseAgent/SpecialistAgent
- Estado compartilhado via TypedDict ou Pydantic model
- Dependency injection via FastAPI Depends()
- Singletons gerenciados por lru_cache (não por variável global)
- Separação clara: routes → dependencies → services → domain

## TypeScript Frontend

### Formatação

- ESLint + Prettier
- TypeScript strict mode
- Sem `any` — usar tipos específicos ou `unknown`

### Estado

- Local: Zustand (useAppStore)
- Servidor: React Query / TanStack Query
- Nunca prop drilling profundo — usar store ou context

### API

- Todas as chamadas via `src/services/api.ts` (axios)
- Tipos compartilhados em `src/types/index.ts`
- Tratar erros de rede com feedback visual ao usuário

### Componentes

- Functional components com hooks
- Props tipadas com interface (não type inline)
- Acessibilidade: aria-labels, roles, keyboard navigation

## Anti-patterns a Flagrar

### Críticos (bloquear)

- Secret/key hardcoded em código
- SQL construído por concatenação de string
- `eval()` ou `exec()` com input do usuário
- Endpoint sem autenticação/autorização
- Dados sensíveis em logs

### Altos (corrigir antes de merge)

- `os.environ` direto em vez de get_settings()
- print() em código de produção
- Bare except sem justificativa
- Função com > 50 linhas sem extração
- Teste que depende de estado externo (rede, filesystem absoluto)

### Médios (corrigir em breve)

- Docstring ausente em função/classe pública
- Type hint ausente
- Duplicação de lógica entre módulos
- Magic number sem constante nomeada
- TODO sem issue/ticket associado

### Baixos (sugestão)

- Naming que poderia ser mais descritivo
- Import não utilizado (ruff pega, mas vale notar)
- Comentário óbvio que repete o código
- Oportunidade de simplificar com list comprehension
