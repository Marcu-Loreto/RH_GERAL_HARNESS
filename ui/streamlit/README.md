# Tela de teste (Streamlit)

Interface de chat para **testes de usuário** do Harness de IA de RH. Conversa com
a API FastAPI por HTTP — não acessa o pipeline diretamente, então reflete o que um
cliente real veria.

## Recursos

- Chat com histórico (pergunta/resposta com os agentes).
- Seletor de perfil (`X-User-Role`): colaborador, gestor, rh, juridico, admin.
- Painel de detalhes: agente, domínio, confiança, evidências, revisão humana,
  guardrails acionados e `trace_id`.
- Aba para ingerir documentos aprovados (perfis `rh` / `admin`).

## Como rodar

Pré-requisito: a API precisa estar no ar.

```bash
# 1. Instalar a dependência da UI (uma das opções)
uv pip install streamlit requests
# ou
pip install -r requirements-ui.txt

# 2. Subir a API (em um terminal)
uv run uvicorn app.api.main:app --reload

# 3. Subir a interface (em outro terminal)
streamlit run streamlit/app.py
```

A UI abre em `http://localhost:8501`. A URL da API pode ser ajustada na barra
lateral ou pela variável de ambiente `RH_API_URL` (padrão `http://127.0.0.1:8000`).

## Roteiro sugerido de teste

1. Aba **Ingerir documentos** (perfil `rh`): ingira a política de férias padrão.
2. Aba **Conversa** (perfil `colaborador`): pergunte "quantos dias de férias eu
   tenho?" → resposta com evidência e confiança alta.
3. Teste um tema sensível: "como denunciar assédio?" → `requires_human_review`.
4. Teste bloqueio: "quanto o colega recebe de salário?" → resposta bloqueada.
5. Observe o painel lateral: evidências, agente escolhido e `trace_id`.
