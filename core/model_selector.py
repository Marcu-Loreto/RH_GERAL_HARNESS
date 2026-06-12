"""Seleção de modelo LLM baseada em dificuldade da pergunta."""

import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
_dotenv_path = Path(__file__).parent.parent / ".env"
load_dotenv(_dotenv_path)


def _get_env_model(key: str, default: str) -> str:
    """Retorna modelo do ambiente ou valor padrão."""
    return os.getenv(key, default)


@lru_cache(maxsize=1)
def _get_all_models() -> dict:
    """Carrega todos os modelos do ambiente."""
    return {
        "triviais": _get_env_model("MODEL_TRIVIAL", "openrouter/free"),
        "baixa": _get_env_model("MODEL_ECONOMICO", "gpt-4o-mini"),
        "media": _get_env_model("MODEL_INTERMEDIARIO", "gpt-4o-nano"),
        "alta": _get_env_model("MODEL_ROBUSTO", "gpt-4o"),
    }


# ============================================================
# CLASSIFICAÇÃO DE DIFICULDADE POR PALAVRAS-CHAVE
# ============================================================

# Perguntas triviais/simplórias - recepcionista responde
PERGUNTAS_TRIVIAIS = [
    "oi", "olá", "bom dia", "boa tarde", "boa noite", "ola",
    "tudo bem", "como vai", "obrigado", "obrigada", "até logo",
    "quem é você", "o que você faz", "me ajuda", "preciso de ajuda",
    "qual seu nome", "você é bot", "você é humano",
]

# Perguntas de BAIXA complexidade - informação direta
PALAVRAS_BAIXA_DIFICULDADE = [
    # Gerais
    "o que é", "o que são", "como funciona", "onde fica", "qual é",
    # Férias
    "quantos dias de férias", "quando posso tirar férias", "férias kole",
    "direito a férias", "período de férias",
    # Benefícios
    "vale alimentação", "vale refeção", "plano de saúde", "auxílio creche",
    "vale transporte", "benefícios", "o que inclui",
    # Políticas
    "horário de trabalho", "jornada", "banco de horas", "home office",
    "presencial", "trabalho remoto",
    # Recrutamento
    "vagas abertas", "como se candidatar", "processo seletivo",
    "indicar candidato", "indicação",
    # Treinamento
    "cursos", "treinamentos", "certificação", "onde fazer",
]

# Perguntas de MÉDIA complexidade - exigem análise/contextualização
PALAVRAS_MEDIA_DIFICULDADE = [
    # Cálculos e valores
    "quanto", "valor", "cálculo", "como calcular", "quanto recebo",
    # Comparações
    "diferença entre", "qual melhor", "vantagens", "desvantagens",
    # Condições
    "tenho direito", "posso fazer", "é permitido", "preciso",
    "como faço para", "o que preciso para", "quais documentos",
    # Situações específicas
    "se eu", "caso", "quando", "se happen", "e se",
    # Progressão
    "promoção", "aumento", "progressão", "carreira", "nível",
    # Policies
    "política", "regra", "norma", "procedimento",
    # LGPD/Compliance
    "dados pessoais", "privacidade", "lgpd", "consentimento",
]

# Perguntas de ALTA complexidade - exigem análise profunda, múltiplas fontes
PALAVRAS_ALTA_DIFICULDADE = [
    # Situações legais/trabalhistas
    "demissão", "rescisão", "aviso prévio", "justa causa",
    "processo trabalhista", "reclamação trabalhista", "vai processar",
    # Conflitos
    "conflito", "assédio", "denúncia", "canal de ética",
    "reclamação", "problema com", "situation",
    # Cálculos complexos
    "rescisão trabalhista", "cálculo de férias", "FGTS", "INSS",
    "multa rescisória", "hora extra", "adicional noturno",
    # Situações pessoais complexas
    "meu caso", "situação específica", "minha circumstance",
    "problema particular", "caso específico",
    # Múltiplos temas
    "e sobre", "além disso", "também tenho", "outro lado",
]


def _classificar_dificuldade(pergunta: str) -> str:
    """Classifica a dificuldade da pergunta por palavras-chave."""
    
    texto = pergunta.lower()
    
    # 1. Verifica se é trivial (greeting, recepção)
    if any(p in texto for p in PERGUNTAS_TRIVIAIS):
        return "triviais"
    
    # 2. Verifica alta complexidade primeiro (mais específica)
    if any(p in texto for p in PALAVRAS_ALTA_DIFICULDADE):
        return "alta"
    
    # 3. Verifica média complexidade
    if any(p in texto for p in PALAVRAS_MEDIA_DIFICULDADE):
        return "media"
    
    # 4. Verifica baixa complexidade
    if any(p in texto for p in PALAVRAS_BAIXA_DIFICULDADE):
        return "baixa"
    
    # 5. Padrão: se não reconhece, usa modelo intermediário
    return "media"


def escolher_modelo(
    pergunta: str,
    risco_alto: bool = False,
    producao: bool = True
) -> str:
    """Seleciona o modelo LLM baseado na dificuldade da pergunta.
    
    Args:
        pergunta: Texto da pergunta do usuário
        risco_alto: Se True, força modelo mais robusto para perguntas sensíveis
        producao: Se True, está em ambiente de produção
        
    Returns:
        Nome do modelo a ser usado (lido do .env)
    """
    models = _get_all_models()
    
    # Se risco_alto=True, sempre usa modelo robusto
    if risco_alto:
        return models["alta"]
    
    # Classifica a dificuldade da pergunta
    dificuldade = _classificar_dificuldade(pergunta)
    
    # Retorna o modelo conforme a dificuldade
    return models[dificuldade]