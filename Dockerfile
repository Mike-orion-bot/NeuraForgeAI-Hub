FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usar la variable de entorno PORT suministrada por Render, por defecto 10000
ENV PORT=10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Ejecutar con uvicorn apuntando a main:app
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
