#!/bin/bash
# Script para iniciar a API e Interface Streamlit em terminais separados

echo "Iniciando o projeto Kiro - Assistente de RH..."

# Terminal 1: API FastAPI
echo ">>> Terminal 1: Iniciando API em http://127.0.0.1:8000"
x-terminal-emulator -e "source .venv/bin/activate && uvicorn app.api.main:app --reload" &
# No Linux Mint/MATE use: mate-terminal -e
# No Ubuntu/GNOME use: gnome-terminal --

# Terminal 2: Interface Streamlit
echo ">>> Terminal 2: Iniciando Interface em http://localhost:8501"
x-terminal-emulator -e "source .venv/bin/activate && streamlit run ui/streamlit/app.py" &

echo "Projetos iniciados!"
echo "API: http://127.0.0.1:8000"
echo "API Docs: http://127.0.0.1:8000/docs"
echo "Streamlit: http://localhost:8501"