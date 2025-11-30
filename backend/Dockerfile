# ===================================
# AutoPromo Backend + Worker
# ===================================
# Usa Python 3.12 + instala Playwright manualmente
# Resolve NotImplementedError no Windows
# Unifica desenvolvimento e produção

FROM python:3.12-slim-bookworm

# Metadados
LABEL maintainer="AutoPromo"
LABEL description="Backend FastAPI + Worker WhatsApp com Playwright"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Instalar dependências do sistema necessárias para Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (cache otimizado)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Instalar Playwright + browsers
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
