---
id: input_guardrails
version: 1
owner: time-ia-rh
description: Guardrails de segurança de entrada para o assistente de RH
status: approved
---

# Guardrails de Segurança de Entrada

Este documento define as regras de validação e sanitização de entrada para proteger o assistente de RH contra conteúdo malicioso, manipulação e vazamento de informações.

## 1. Validação de Entrada

### 1.1 Comprimento Máximo

- **Máximo de caracteres**: 5.000 por pergunta
- **Rationale**: Previne ataques de denial of service e prompts excessivamente longos

### 1.2 Encoding e Sanitização

- Remover caracteres nulos e control
- Normalizar unicode (NFC)
- Remover whitespaces excessivos

## 2. Detecção de Conteúdo Proibido

### 2.1 Padrões Bloqueados Imediatamente

| Categoria         | Padrão                         | Ação     |
| ----------------- | ------------------------------ | -------- |
| Prompt Injection  | "ignore previous instructions" | BLOQUEAR |
| Prompt Injection  | "you are now"                  | BLOQUEAR |
| Prompt Injection  | "system prompt"                | BLOQUEAR |
| Prompt Injection  | "disregard all"                | BLOQUEAR |
| Jailbreak         | " DAN ("                       | BLOQUEAR |
| Jailbreak         | "developer mode"               | BLOQUEAR |
| PII Request       | "cpf de"                       | BLOQUEAR |
| PII Request       | "salário do"                   | BLOQUEAR |
| PII Request       | "dados do colaborador"         | BLOQUEAR |
| Dados Financeiros | "contracheque"                 | BLOQUEAR |
| Dados Financeiros | "folha de pagamento"           | BLOQUEAR |

### 2.2 Padrões com Alerta

| Categoria             | Padrão                  | Ação                             |
| --------------------- | ----------------------- | -------------------------------- |
| Information Gathering | "quem ganha mais"       | ALERTA + REVIEW                  |
| Information Gathering | "salário médio"         | ALERTA + REVIEW                  |
| Sensitive Inquiry     | "demitir"               | ALERTA + REVIEW                  |
| Sensitive Inquiry     | "processo trabalhista"  | ALERTA + REVIEW                  |
| Legal Advice          | "posso processar"       | ALERTA + DIRECIONAR JURÍDICO     |
| Legal Advice          | "direitos trabalhistas" | ALERTA + RESPONDER GENERICAMENTE |

## 3. Detecção de PII (Dados Pessoais)

### 3.1 PII Brasileiro Detectado

- **CPF**: padrão `\d{3}\.?\d{3}\.?\d{3}-?\d{2}`
- **Telefone**: padrões brasileiros (celular/fixo)
- **E-mail**: padrão padrão de e-mail
- **RG**: padrões de RG brasileiro

### 3.2 Ação ao Detectar PII

1. **Máscara automática** do PII detectado
2. **Registrar** em log para auditoria
3. **Alertar** que dados sensíveis não devem ser compartilhados

## 4. Limites de Requisições

### 4.1 Rate Limiting

- **Por IP**: 60 requisições por minuto
- **Por sessão**: 20 perguntas por minuto
- ** burst**: máximo de 10 requisições simultâneas

### 4.2 Resposta ao Rate Limit

- HTTP 429 Too Many Requests
- Mensagem: "Muitas solicitações. Por favor, aguarde um momento."

## 5. Categorização de Risco

### 5.1 Níveis de Risco

| Nível     | Critérios                         | Ação                     |
| --------- | --------------------------------- | ------------------------ |
| **BAIXO** | Pergunta normal de RH             | Processar normalmente    |
| **MÉDIO** | Pergunta sobre dados de terceiros | Adicionar revisão humana |
| **ALTO**  | PII detectado ou prompt injection | Bloquear e registrar     |

### 5.2 Fatores de Risco

- Comprimento da entrada (muito longo = suspeito)
- Presença de caracteres especiais anômalos
- Repetição de padrões (possível fuzzing)
- Presença de código ou scripts

## 6. Logging e Auditoria

### 6.1 Eventos Registrados

- Todas as tentativas de BLOQUEIO
- Detecções de PII
- Tentativas de prompt injection
- Rate limits ativados

### 6.2 Dados em Log

- Timestamp
- Hash da entrada (não entrada original)
- Ação tomada (bloqueado/alertado/permitido)
- Endereço IP (se aplicável)
- Session ID

## 7. Respostas de Erro

### 7.1 Mensagens Amigáveis

- **Bloqueio por PII**: "Para proteger seus dados pessoais, não inclua informações sensíveis na pergunta. Posso ajudar com outra dúvida?"
- **Bloqueio por conteúdo**: "Não consegui processar sua solicitação. Poderia reformular a pergunta?"
- **Rate limit**: "Muitas solicitações. Por favor, aguarde um momento e tente novamente."

### 7.2 Mensagens Técnicas (apenas para logs)

- Código de erro interno
- Categoria do bloqueio
- Timestamp

## 8. Lista de Palavras Bloqueadas

### Palavras-Chave de Manipulação

```
ignore, disregard, forget, override, bypass, jailbreak, exploit
developer, system, admin, root, sudo, hack, crack, password
```

### Palavras de Conteúdo Illegal

```
drogue, weapon, bomb, illegal, fraud, scam, phishing
```

## 9. Configuração

### Variáveis de Ambiente

```bash
# Guardrails de entrada
ENABLE_INPUT_GUARDRAILS=true
MAX_INPUT_LENGTH=5000
BLOCK_PII=true
BLOCK_PROMPT_INJECTION=true
ENABLE_RATE_LIMITING=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

## 10. Atualização

Este documento deve ser revisado e atualizado:

- Mensalmente: revisar padrões de ataque conhecidos
- Após incidentes: adicionar novos padrões detectados
- Trimestralmente: revisar limiares e configurações
