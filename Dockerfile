FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar algunas librerías si fuera necesario
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usar la variable de entorno PORT suministrada por Render, por defecto 10000
ENV PORT=10000

# Ejecutar con uvicorn apuntando a main:app
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
