---
name: code-review
description: Executa code review completo seguindo pipelines validados pelo mercado (Google, Microsoft, OWASP). Use sempre que o usuário pedir review de código, análise de qualidade, revisão de PR, auditoria de segurança em código, verificação de boas práticas, ou quando quiser avaliar a qualidade de módulos Python/TypeScript. Também se aplica quando alguém mencionar "revisar código", "analisar qualidade", "code review", "pull request review", ou pedir feedback sobre implementação.
---

# Code Review Skill

Skill para realizar code review profissional seguindo pipelines validados pelo mercado, inspirado nas práticas do Google Engineering Practices, Microsoft SDL, e OWASP Code Review Guide — adaptado para execução local sem CI/CD.

## Filosofia

Code review não é apenas encontrar bugs. É sobre manter a saúde do codebase a longo prazo, compartilhar conhecimento, e garantir que o código evolua de forma sustentável. Esta skill opera em camadas progressivas, do mais crítico ao mais cosmético.

## Pipeline de Review

O review segue 7 etapas sequenciais, da mais crítica à menos urgente. Cada etapa produz findings categorizados por severidade.

### Etapa 1: Segurança (OWASP Top 10 + SAST patterns)

Verificar presença de:

- Injeção (SQL, Command, LDAP, XSS)
- Autenticação/autorização quebrada
- Exposição de dados sensíveis (secrets hardcoded, PII em logs)
- Deserialização insegura
- Dependências com vulnerabilidades conhecidas
- Path traversal, SSRF
- Prompt injection (para código com LLM)
- Validação de input ausente ou insuficiente

### Etapa 2: Correção Lógica

- Condições de corrida (race conditions)
- Off-by-one, null/None não tratado
- Tratamento de erros incompleto (bare except, catch genérico)
- Estado mutável compartilhado indevidamente
- Loops infinitos ou recursão sem base case
- Contratos quebrados entre chamador e chamado (tipos, precondições)

### Etapa 3: Arquitetura e Design

- Princípio da responsabilidade única (SRP)
- Acoplamento excessivo entre módulos
- Abstrações desnecessárias ou insuficientes
- Violação de camadas (ex: rota acessando DB diretamente)
- Padrões do projeto sendo ignorados (ver referências do projeto)
- Testabilidade: código difícil de testar por design

### Etapa 4: Performance e Recursos

- Queries N+1 ou sem paginação
- Alocações desnecessárias em hot paths
- Falta de cache onde seria benéfico
- Conexões/handles não fechados
- Complexidade algorítmica inadequada para o volume esperado
- Bloqueio de event loop (async)

### Etapa 5: Manutenibilidade

- Nomes que não comunicam intenção
- Funções com mais de 40 linhas ou muitos parâmetros (>4)
- Duplicação de lógica (DRY violado)
- Comentários que explicam "o quê" em vez de "por quê"
- Magic numbers/strings sem constante nomeada
- Complexidade ciclomática alta

### Etapa 6: Testes

- Cobertura dos caminhos críticos (happy path + error paths)
- Testes frágeis (acoplados a implementação, não a comportamento)
- Fixtures/mocks excessivos que escondem bugs reais
- Ausência de testes para edge cases identificados
- Assertions vagas (apenas "not None" quando deveria validar conteúdo)

### Etapa 7: Estilo e Convenções

- Conformidade com formatter/linter do projeto (black, ruff, eslint)
- Convenções de naming do projeto
- Organização de imports
- Docstrings/type hints ausentes (para Python)
- Consistência com o restante do codebase

## Formato de Saída

Produzir o relatório no seguinte formato:

```markdown
# Code Review: [arquivo ou módulo]

## Resumo Executivo

[1-3 frases sobre o estado geral do código]

## Severidade dos Findings

| Severidade                  | Quantidade |
| --------------------------- | ---------- |
| 🔴 Crítico (bloqueia merge) | N          |
| 🟠 Alto (deve corrigir)     | N          |
| 🟡 Médio (deveria corrigir) | N          |
| 🔵 Baixo (sugestão)         | N          |

## Findings

### 🔴 [Título do finding]

- **Arquivo**: `path/to/file.py:42`
- **Categoria**: Segurança | Lógica | Arquitetura | Performance | Manutenibilidade | Testes | Estilo
- **Descrição**: O que está errado e por quê
- **Impacto**: Qual o risco concreto
- **Sugestão**: Como corrigir (com snippet se aplicável)

[repetir para cada finding]

## Pontos Positivos

[Listar 2-3 coisas bem feitas — review não é só crítica]

## Ações Recomendadas

1. [Ação prioritária 1]
2. [Ação prioritária 2]
3. [...]
```

## Critérios de Severidade

- **🔴 Crítico**: Vulnerabilidade de segurança explorável, perda de dados, crash em produção, violação de compliance. Bloqueia merge.
- **🟠 Alto**: Bug que afeta usuários, degradação significativa de performance, violação arquitetural grave. Deve corrigir antes de merge.
- **🟡 Médio**: Código que funciona mas vai gerar dívida técnica, dificultar manutenção, ou causar problemas em escala.
- **🔵 Baixo**: Melhorias de legibilidade, convenções de estilo, refatorações opcionais.

## Adaptações por Contexto

### Quando revisar um arquivo específico

Focar nas 7 etapas aplicadas ao arquivo. Verificar também como ele se integra com módulos vizinhos.

### Quando revisar um diff/PR

Focar apenas no código alterado, mas considerar o contexto dos arquivos tocados. Não revisar código não-alterado exceto se o diff introduz inconsistência.

### Quando revisar um módulo/diretório inteiro

Começar com visão de alto nível (arquitetura, responsabilidades, dependências entre arquivos) antes de mergulhar em cada arquivo.

### Quando o usuário pedir foco específico

Priorizar a área solicitada mas ainda verificar segurança (etapa 1) — nunca pular segurança.

## Referências do Projeto

Ao revisar código deste projeto, considerar:

- Python: black (line-length=100), ruff, mypy strict, structlog
- Padrões: Settings via get_settings(), logging com keyword args
- Segurança: nunca logar PII, validar inputs com Pydantic
- Testes: pytest, hypothesis para property-based testing
- Imports: from app.X, nunca importar env vars diretamente

Para detalhes completos das convenções, consultar `references/project-conventions.md`.
