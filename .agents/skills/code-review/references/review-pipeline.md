# Pipeline de Code Review — Referência Detalhada

Este documento expande o pipeline de 7 etapas com checklists concretos e exemplos de findings reais.

## Fontes e Inspiração

O pipeline é uma síntese de:

- **Google Engineering Practices**: https://google.github.io/eng-practices/review/
- **Microsoft Security Development Lifecycle (SDL)**
- **OWASP Code Review Guide v2**
- **Clean Code (Robert C. Martin)**
- **The Pragmatic Programmer (Hunt & Thomas)**

## Checklist Rápido por Etapa

### 1. Segurança

```
□ Inputs validados antes de uso (Pydantic, zod, etc.)
□ Sem secrets hardcoded (grep: password, secret, key, token + valor literal)
□ Queries parametrizadas (nunca f-string em SQL)
□ Sem eval/exec com input externo
□ Autenticação presente em endpoints sensíveis
□ Rate limiting configurado
□ Headers de segurança (CORS, CSP, etc.)
□ Sanitização de output (XSS prevention)
□ Sem log de PII
□ Dependências sem CVEs conhecidas
```

### 2. Correção Lógica

```
□ Null/None handling em todos os caminhos
□ Boundary conditions (empty list, zero, max int)
□ Error paths testados e com recovery adequado
□ Tipos corretos (sem implicit coercion perigosa)
□ Concorrência: sem race conditions em shared state
□ Idempotência onde esperada (retry-safe)
□ Contratos de função respeitados (pre/post conditions)
```

### 3. Arquitetura e Design

```
□ Responsabilidade única por módulo/classe
□ Dependências fluem numa direção (sem ciclos)
□ Camadas respeitadas (route → service → domain → infra)
□ Abstrações justificam sua existência
□ Extensibilidade sem modificação (Open/Closed)
□ Interface segregation (não forçar implementar o desnecessário)
□ Testável por design (injeção de dependência, sem global state)
```

### 4. Performance

```
□ Sem N+1 queries (batch/join quando possível)
□ Paginação em listagens
□ Cache onde leitura >> escrita
□ Índices de DB para queries frequentes
□ Sem blocking I/O em async context
□ Alocações mínimas em loops quentes
□ Lazy loading para dados pesados
□ Connection pooling configurado
```

### 5. Manutenibilidade

```
□ Nomes comunicam intenção (sem abbreviations obscuras)
□ Funções ≤ 40 linhas (exceções justificadas)
□ Parâmetros ≤ 4 (senão: dataclass/config object)
□ DRY: lógica duplicada extraída
□ Complexidade ciclomática ≤ 10
□ Cada módulo cabe na cabeça (cognitive load baixo)
□ Comentários explicam "por quê", não "o quê"
```

### 6. Testes

```
□ Happy path coberto
□ Error paths cobertos (exceções, inputs inválidos)
□ Edge cases identificados e testados
□ Sem mock excessivo (preferir integration tests leves)
□ Assertions verificam conteúdo, não apenas existência
□ Testes independentes entre si (sem ordem obrigatória)
□ Property-based tests para lógica combinatória
□ Sem sleep/wait hardcoded (usar polling/retry)
```

### 7. Estilo e Convenções

```
□ Formatter passou sem alterações (black/prettier)
□ Linter sem warnings não-suprimidos
□ Type checker satisfeito (mypy/tsc)
□ Imports organizados (isort/eslint)
□ Docstrings em interfaces públicas
□ Consistente com o restante do codebase
```

## Exemplo de Finding Bem Escrito

````markdown
### 🔴 SQL Injection via f-string em query de busca

- **Arquivo**: `app/retrieval/vector_store.py:87`
- **Categoria**: Segurança
- **Descrição**: A query de busca é construída com f-string interpolando
  diretamente o input do usuário sem sanitização.
- **Impacto**: Um atacante pode injetar SQL arbitrário, potencialmente
  extraindo dados de todas as tabelas ou executando DDL destrutivo.
- **Sugestão**:

  ```python
  # Antes (vulnerável)
  cursor.execute(f"SELECT * FROM chunks WHERE text LIKE '%{query}%'")

  # Depois (parametrizado)
  cursor.execute("SELECT * FROM chunks WHERE text LIKE ?", (f"%{query}%",))
  ```
````

````

## Exemplo de Finding Mal Escrito (evitar)

```markdown
### Bug no código
- O código tem um problema
- Corrigir
````

Findings devem ser acionáveis: dizer exatamente o quê, onde, por quê, e como corrigir.

## Quando Não Bloquear

Nem todo finding é motivo para bloquear. Usar bom senso:

- Código experimental/POC: relaxar estilo, manter segurança
- Hotfix urgente: aceitar debt temporário com TODO+issue
- Refactoring em andamento: aceitar estado intermediário se o PR é parte de uma série
- Preferência pessoal vs convenção: se não é convenção do projeto, é sugestão (🔵)

## Priorização de Review

Se o código é extenso, priorizar revisão nesta ordem:

1. Código que lida com autenticação/autorização
2. Código que processa input do usuário
3. Código que acessa dados sensíveis
4. Mudanças em interfaces públicas (API contracts)
5. Lógica de negócio core
6. Infraestrutura e configuração
7. Testes
8. Estilo/formatação
