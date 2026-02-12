# Imagem base
FROM python:3.12-slim

# Diretório de trabalho dentro do container
WORKDIR /app

# Variáveis de ambiente úteis
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instalar dependências de sistema necessárias para compilar lru-dict (usado pelo web3)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Copiar arquivo de dependências Python
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Comando de inicialização do orchestrator
# Ajuste esta linha se o entrypoint do seu projeto for outro arquivo/módulo
CMD ["python", "-m", "app.main"]
