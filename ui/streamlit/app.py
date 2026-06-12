"""Interface de teste (Streamlit) para o Harness de IA de RH.

Tela de chat para testes de usuário. Conversa com a API FastAPI por HTTP — não
acessa o pipeline diretamente, de modo que reflete exatamente o que um cliente
real veria. Permite escolher o perfil (X-User-Role), ver evidências, confiança,
agente, revisão humana e trace de cada resposta, e ingererir documentos (RH/Admin).

Execução:
    # 1. Suba a API em outro terminal
    uv run uvicorn app.api.main:app --reload
    # 2. Rode esta interface
    streamlit run ui/streamlit/app.py

A URL da API pode ser ajustada na barra lateral ou via variável de ambiente
RH_API_URL (padrão: http://127.0.0.1:8000).
"""

from __future__ import annotations

import io
import os
import re
from typing import Any

import requests
import streamlit as st

DEFAULT_API_URL = os.getenv("RH_API_URL", "http://127.0.0.1:8000")
API_PREFIX = "/api/v1"

# Perfis de usuário: admin, suporte_rh, usuario
ROLES = ["usuario", "suporte_rh", "admin"]
ROLE_LABELS = {
    "usuario": "Usuário (Conversa)",
    "suporte_rh": "Suporte RH (Admin + Métricas)",
    "admin": "Administrador (Completo)",
}

AREAS = [
    "(automático)",
    "beneficios",
    "politicas",
    "cargos_salarios",
    "treinamento",
    "recrutamento",
    "compliance",
]
REQUEST_TIMEOUT = 30


# ─────────────────────────────── Cliente HTTP ────────────────────────────────
def _headers(role: str, user_id: str) -> dict[str, str]:
    # Mapeia roles internos para os perfis do sistema
    role_map = {
        "usuario": "colaborador",
        "suporte_rh": "rh",
        "admin": "admin",
    }
    mapped_role = role_map.get(role, role)
    headers = {"Content-Type": "application/json", "X-User-Role": mapped_role}
    if user_id.strip():
        headers["X-User-Id"] = user_id.strip()
    return headers


def api_health(base_url: str) -> tuple[bool, str]:
    """Verifica se a API está no ar."""
    try:
        resp = requests.get(f"{base_url}{API_PREFIX}/health", timeout=5)
        if resp.status_code == 200:
            return True, resp.json().get("environment", "?")
        return False, f"HTTP {resp.status_code}"
    except requests.RequestException as exc:
        return False, str(exc)


def api_ask(base_url: str, query: str, area: str, role: str, user_id: str) -> dict[str, Any]:
    """Envia uma pergunta para o endpoint /ask."""
    payload: dict[str, Any] = {"query": query}
    if area and area != "(automático)":
        payload["area_rh"] = area
    resp = requests.post(
        f"{base_url}{API_PREFIX}/ask",
        json=payload,
        headers=_headers(role, user_id),
        timeout=REQUEST_TIMEOUT,
    )
    return {"status": resp.status_code, "body": _safe_json(resp)}


def api_ingest(base_url: str, document: dict[str, Any], raw_text: str, role: str) -> dict[str, Any]:
    """Ingere um documento via endpoint /documents."""
    resp = requests.post(
        f"{base_url}{API_PREFIX}/documents",
        json={"document": document, "raw_text": raw_text},
        headers=_headers(role, ""),
        timeout=REQUEST_TIMEOUT,
    )
    return {"status": resp.status_code, "body": _safe_json(resp)}


def api_metrics(base_url: str, role: str) -> dict[str, Any]:
    """Busca métricas do sistema."""
    resp = requests.get(
        f"{base_url}{API_PREFIX}/metrics/summary",
        headers=_headers(role, ""),
        timeout=REQUEST_TIMEOUT,
    )
    return {"status": resp.status_code, "body": _safe_json(resp)}


def api_finops(base_url: str, role: str) -> dict[str, Any]:
    """Busca dados de custos/finops."""
    resp = requests.get(
        f"{base_url}{API_PREFIX}/finops/summary",
        headers=_headers(role, ""),
        timeout=REQUEST_TIMEOUT,
    )
    return {"status": resp.status_code, "body": _safe_json(resp)}


def _safe_json(resp: requests.Response) -> Any:
    try:
        return resp.json()
    except ValueError:
        return {"detail": resp.text}


# ──────────────────────────── Extração de arquivos ───────────────────────────
UPLOAD_TYPES = ["txt", "md", "csv", "pdf", "docx"]


def slugify(name: str) -> str:
    """Gera um source_id a partir do nome do arquivo."""
    base = name.rsplit(".", 1)[0].lower()
    slug = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return slug or "documento"


def extract_text_from_upload(uploaded: Any) -> tuple[str, str | None]:
    """Extrai texto de um arquivo enviado. Retorna (texto, erro_opcional)."""
    name = uploaded.name
    ext = name.lower().rsplit(".", 1)[-1] if "." in name else ""
    data = uploaded.getvalue()

    if ext in ("txt", "md", "csv"):
        return data.decode("utf-8", errors="replace"), None

    if ext == "pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
            return text, None
        except ImportError:
            return "", "Para ler PDF instale: pip install pypdf"
        except Exception as exc:  # noqa: BLE001
            return "", f"Falha ao ler PDF: {exc}"

    if ext == "docx":
        try:
            import docx

            document = docx.Document(io.BytesIO(data))
            text = "\n".join(p.text for p in document.paragraphs)
            return text, None
        except ImportError:
            return "", "Para ler DOCX instale: pip install python-docx"
        except Exception as exc:  # noqa: BLE001
            return "", f"Falha ao ler DOCX: {exc}"

    return data.decode("utf-8", errors="replace"), None


# ─────────────────────────────── Componentes UI ──────────────────────────────
def render_answer_panel(body: dict[str, Any]) -> None:
    """Renderiza o painel lateral de detalhes da última resposta."""
    answer = body.get("answer", {})
    st.subheader("Detalhes da resposta")

    cols = st.columns(2)
    cols[0].metric("Agente", body.get("agent") or "—")
    cols[1].metric("Domínio", body.get("domain") or "—")

    cols = st.columns(2)
    cols[0].metric("Confiança", str(answer.get("confidence", "—")))
    cols[1].metric("Bloqueada", "sim" if body.get("blocked") else "não")

    if answer.get("requires_human_review"):
        st.warning("⚠️ Requer revisão humana")
    if body.get("guardrails_triggered"):
        st.error(f"Guardrails: {', '.join(body['guardrails_triggered'])}")
    if answer.get("screening_decision"):
        st.info(f"Triagem do agente: {answer['screening_decision']}")
    if answer.get("escalation_reason"):
        st.caption(f"Motivo do escalonamento: {answer['escalation_reason']}")

    evidence = answer.get("evidence") or []
    st.markdown(f"**Evidências ({len(evidence)})**")
    for ev in evidence:
        with st.expander(f"{ev.get('title', '?')} v{ev.get('version', '?')}"):
            st.caption(f"source_id: {ev.get('source_id')}")
            st.caption(f"chunk_id: {ev.get('chunk_id')}")
            if ev.get("summary"):
                st.write(ev["summary"])
    if not evidence:
        st.caption("Nenhuma evidência citada nesta resposta.")

    if answer.get("limitations"):
        st.markdown("**Limitações**")
        st.caption(answer["limitations"])

    if body.get("trace_id"):
        st.markdown("**Trace**")
        st.code(body["trace_id"], language="text")


def render_chat_tab(base_url: str, role: str, user_id: str, area: str) -> None:
    """Aba de conversa com os agentes."""
    # Para usuario: apenas conversa simples, sem painel lateral
    if role == "usuario":
        for msg in st.session_state.history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        prompt = st.chat_input("Pergunte sobre RH (ex.: quantos dias de férias eu tenho?)")
        if prompt:
            st.session_state.history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Consultando os agentes..."):
                    try:
                        result = api_ask(base_url, prompt, area, role, user_id)
                    except requests.RequestException as exc:
                        st.error(f"Falha ao chamar a API: {exc}")
                        return

                if result["status"] == 200:
                    body = result["body"]
                    answer_text = body.get("answer", {}).get("answer", "(sem texto)")
                    st.markdown(answer_text)
                    st.session_state.history.append(
                        {"role": "assistant", "content": answer_text}
                    )
                elif result["status"] == 422:
                    detail = result["body"].get("detail", "Requisição inválida.")
                    st.error(f"Erro controlado (422): {detail}")
                else:
                    st.error(f"HTTP {result['status']}: {result['body']}")
        return

    # Para outros perfis: conversa com painel lateral de detalhes
    chat_col, detail_col = st.columns([3, 2])

    with chat_col:
        for msg in st.session_state.history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        prompt = st.chat_input("Pergunte sobre RH (ex.: quantos dias de férias eu tenho?)")
        if prompt:
            st.session_state.history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Consultando os agentes..."):
                    try:
                        result = api_ask(base_url, prompt, area, role, user_id)
                    except requests.RequestException as exc:
                        st.error(f"Falha ao chamar a API: {exc}")
                        return

                if result["status"] == 200:
                    body = result["body"]
                    answer_text = body.get("answer", {}).get("answer", "(sem texto)")
                    st.markdown(answer_text)
                    st.session_state.history.append(
                        {"role": "assistant", "content": answer_text}
                    )
                    st.session_state.last_response = body
                elif result["status"] == 422:
                    detail = result["body"].get("detail", "Requisição inválida.")
                    st.error(f"Erro controlado (422): {detail}")
                else:
                    st.error(f"HTTP {result['status']}: {result['body']}")

    with detail_col:
        if st.session_state.last_response:
            render_answer_panel(st.session_state.last_response)
        else:
            st.info("Faça uma pergunta para ver evidências, confiança e trace aqui.")


def render_ingest_tab(base_url: str, role: str) -> None:
    """Aba de ingestão de documentos (RH/Admin), com upload de arquivo."""
    st.subheader("Ingerir documento oficial")
    st.caption("Apenas perfis 'suporte_rh' e 'admin'. O documento precisa estar aprovado.")

    # Upload de arquivo: extrai o texto e pré-preenche o formulário.
    uploaded = st.file_uploader(
        "Enviar arquivo (opcional)", type=UPLOAD_TYPES, accept_multiple_files=False
    )
    if uploaded is not None and st.session_state.get("uploaded_name") != uploaded.name:
        text, error = extract_text_from_upload(uploaded)
        if error:
            st.error(error)
        if text.strip():
            st.session_state.extracted_text = text
            st.session_state.suggested_source_id = slugify(uploaded.name)
            st.session_state.suggested_title = uploaded.name.rsplit(".", 1)[0]
            st.session_state.uploaded_name = uploaded.name
            st.success(f"Texto extraído de '{uploaded.name}' ({len(text)} caracteres).")

    default_text = st.session_state.get(
        "extracted_text",
        "Todo colaborador tem direito a 30 dias de férias por ano após o período aquisitivo.",
    )
    default_source_id = st.session_state.get("suggested_source_id", "ferias-001")
    default_title = st.session_state.get("suggested_title", "Política de Férias")

    with st.form("ingest_form"):
        c1, c2 = st.columns(2)
        source_id = c1.text_input("source_id", value=default_source_id)
        title = c2.text_input("Título", value=default_title)
        owner = c1.text_input("Owner (e-mail)", value="rh@empresa.com")
        area_rh = c2.selectbox("Área de RH", AREAS[1:])
        document_type = c1.text_input("Tipo de documento", value="politica")
        version = c2.text_input("Versão", value="1.0")
        confidentiality = c1.selectbox(
            "Confidencialidade", ["publico", "interno", "restrito", "confidencial"], index=1
        )
        valid_from = c2.text_input("Vigente a partir de", value="2025-01-01T00:00:00Z")
        raw_text = st.text_area("Texto do documento", value=default_text, height=180)
        submitted = st.form_submit_button("Ingerir documento")

    if submitted:
        if not raw_text.strip():
            st.error("O texto do documento está vazio.")
            return
        document = {
            "source_id": source_id,
            "title": title,
            "owner": owner,
            "area_rh": area_rh,
            "document_type": document_type,
            "version": version,
            "status": "approved",
            "valid_from": valid_from,
            "confidentiality": confidentiality,
            "language": "pt-BR",
            "hash": f"{source_id}-{version}",
        }
        try:
            result = api_ingest(base_url, document, raw_text, role)
        except requests.RequestException as exc:
            st.error(f"Falha ao chamar a API: {exc}")
            return

        if result["status"] == 201:
            body = result["body"]
            st.success(
                f"Documento '{body.get('source_id')}' indexado "
                f"({body.get('chunks_indexed')} chunk(s))."
            )
            # Limpa o estado do upload para o próximo documento.
            for key in ("extracted_text", "suggested_source_id", "suggested_title", "uploaded_name"):
                st.session_state.pop(key, None)
        elif result["status"] in (401, 403):
            st.error("Perfil sem permissão. Use 'suporte_rh' ou 'admin' na barra lateral.")
        else:
            st.error(f"HTTP {result['status']}: {result['body']}")


def render_metrics_tab(base_url: str, role: str) -> None:
    """Aba de métricas do sistema (suporte_rh e admin)."""
    st.subheader("📊 Métricas do Sistema")

    try:
        result = api_metrics(base_url, role)
    except requests.RequestException as exc:
        st.error(f"Falha ao chamar a API: {exc}")
        return

    if result["status"] == 200:
        body = result["body"]
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Perguntas", body.get("total_questions", 0))
        col2.metric("Total de Respostas IA", body.get("total_answers", 0))
        col3.metric("Total de Transbordos", body.get("total_escalations", 0))

        rate = body.get("escalation_rate", 0) * 100
        st.metric("Taxa de Transbordo", f"{rate:.2f}%")

        st.divider()
        st.caption("Métricas atualizadas em tempo real basedo nas interações do sistema.")
    elif result["status"] in (401, 403):
        st.error("Acesso negado. Apenas suport_rh e admin podem acessar métricas.")
    else:
        st.error(f"HTTP {result['status']}: {result['body']}")


def render_finops_tab(base_url: str, role: str) -> None:
    """Aba de custos e tokens (apenas admin)."""
    st.subheader("💰 Custos e Tokens")

    try:
        result = api_finops(base_url, role)
    except requests.RequestException as exc:
        st.error(f"Falha ao chamar a API: {exc}")
        return

    if result["status"] == 200:
        body = result["body"]

        col1, col2, col3 = st.columns(3)
        col1.metric("Custo Total (USD)", f"${body.get('total_cost', 0):.6f}")
        col2.metric("Total de Tokens", body.get("total_tokens", 0))
        col3.metric("Média por Resposta", f"${body.get('avg_cost_per_answer', 0):.6f}")

        st.divider()

        st.subheader("Custos por Agente")
        cost_by_agent = body.get("cost_by_agent", {})
        if cost_by_agent:
            for agent, cost in cost_by_agent.items():
                st.metric(agent, f"${cost:.6f}")
        else:
            st.caption("Nenhum custo registrado por agente.")

        st.subheader("Custos por Modelo")
        cost_by_model = body.get("cost_by_model", {})
        if cost_by_model:
            for model, cost in cost_by_model.items():
                st.metric(model, f"${cost:.6f}")
        else:
            st.caption("Nenhum custo registrado por modelo.")

        st.divider()
        st.caption("Dados de custos baseados no uso de modelos de IA.")
    elif result["status"] in (401, 403):
        st.error("Acesso negado. Apenas admin pode acessar custos e tokens.")
    else:
        st.error(f"HTTP {result['status']}: {result['body']}")


# ──────────────────────────────────── App ────────────────────────────────────
def main() -> None:
    st.set_page_config(page_title="Assistente de RH — Kiro", page_icon="💬", layout="wide")
    st.title("💬 Assistente de RH — Kiro")
    st.caption("Sistema de perguntas e respostas sobre documentos de RH.")

    if "history" not in st.session_state:
        st.session_state.history = []
    if "last_response" not in st.session_state:
        st.session_state.last_response = None

    with st.sidebar:
        st.header("Configuração")
        base_url = st.text_input("URL da API", value=DEFAULT_API_URL).rstrip("/")

        role = st.selectbox("Perfil do Usuário", ROLES, format_func=lambda x: ROLE_LABELS.get(x, x))
        user_id = st.text_input("User ID (opcional)", value="")
        area = st.selectbox("Área de RH (dica de domínio)", AREAS, index=0)

        ok, info = api_health(base_url)
        if ok:
            st.success(f"API conectada (env: {info})")
        else:
            st.error(f"API indisponível: {info}")
            st.caption("Suba a API: `uv run uvicorn app.api.main:app --reload`")

        if st.button("Limpar conversa"):
            st.session_state.history = []
            st.session_state.last_response = None

        st.divider()
        st.caption(f"Perfil atual: **{ROLE_LABELS.get(role, role)}**")

    # Renderiza as abas berdasarkan perfil do usuário
    if role == "usuario":
        # Usuário comum: apenas conversa
        tab_chat, = st.tabs(["💬 Conversa"])
        with tab_chat:
            render_chat_tab(base_url, role, user_id, area)

    elif role == "suporte_rh":
        # Suporte RH: conversa + ingestion + métricas
        tab_chat, tab_ingest, tab_metrics = st.tabs(["💬 Conversa", "📄 Ingerir Documentos", "📊 Métricas"])
        with tab_chat:
            render_chat_tab(base_url, role, user_id, area)
        with tab_ingest:
            render_ingest_tab(base_url, role)
        with tab_metrics:
            render_metrics_tab(base_url, role)

    elif role == "admin":
        # Admin: conversa + ingestion + métricas + custos
        tab_chat, tab_ingest, tab_metrics, tab_finops = st.tabs(
            ["💬 Conversa", "📄 Ingerir Documentos", "📊 Métricas", "💰 Custos"]
        )
        with tab_chat:
            render_chat_tab(base_url, role, user_id, area)
        with tab_ingest:
            render_ingest_tab(base_url, role)
        with tab_metrics:
            render_metrics_tab(base_url, role)
        with tab_finops:
            render_finops_tab(base_url, role)


if __name__ == "__main__":
    main()