#!/bin/bash
# Script para iniciar a API e Interface Streamlit

set -e

echo "Iniciando o projeto Kiro - Assistente de RH..."

# Ativa o virtualenv
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "ERRO: virtualenv não encontrado em .venv/bin/activate"
    echo "Crie com: python -m venv .venv && pip install -r requirements.txt"
    exit 1
fi

# Função para matar processos filhos ao sair (Ctrl+C)
cleanup() {
    echo ""
    echo "Encerrando serviços..."
    kill $API_PID $UI_PID 2>/dev/null
    wait $API_PID $UI_PID 2>/dev/null
    echo "Serviços encerrados."
    exit 0
}
trap cleanup SIGINT SIGTERM

# Inicia API FastAPI em background
echo ">>> Iniciando API em http://127.0.0.1:8000"
uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000 &
API_PID=$!

# Aguarda um pouco para a API subir antes do Streamlit
sleep 2

# Inicia Interface Streamlit em background
echo ">>> Iniciando Interface em http://localhost:8501"
streamlit run ui/streamlit/app.py --server.port 8501 --server.headless true &
UI_PID=$!

echo ""
echo "========================================="
echo "  Serviços rodando:"
echo "  API:       http://127.0.0.1:8000"
echo "  API Docs:  http://127.0.0.1:8000/docs"
echo "  Streamlit: http://localhost:8501"
echo "========================================="
echo "  Pressione Ctrl+C para encerrar tudo"
echo "========================================="
echo ""

# Mantém o script vivo aguardando os processos filhos
wait $API_PID $UI_PID
