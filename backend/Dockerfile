# ===================================
# AutoPromo Backend + Worker
# ===================================
# Usa imagem oficial do Playwright com Python
# Resolve NotImplementedError no Windows
# Unifica desenvolvimento e produção

FROM mcr.microsoft.com/playwright/python:v1.56.0-jammy

# Metadados
LABEL maintainer="AutoPromo"
LABEL description="Backend FastAPI + Worker WhatsApp com Playwright"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (cache otimizado)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Garantir que browsers Playwright estão instalados
# (imagem base já tem, mas garantindo)
RUN playwright install --with-deps chromium

# Copiar código do backend
COPY . .

# Criar diretórios necessários
RUN mkdir -p /app/whatsapp_sessions /app/logs

# Porta padrão (FastAPI)
EXPOSE 8000

# Comando padrão: FastAPI
# (worker vai override no docker-compose.yml)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
