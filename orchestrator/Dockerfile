# Imagem base
FROM python:3.12-slim

# Working directory inside the container
WORKDIR /app

# Useful environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies required to compile lru-dict (used by web3)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Orchestrator startup command
# Pay attention to who the entrypoint is, otherwise I'll need to change
CMD ["python", "-m", "app.main"]
