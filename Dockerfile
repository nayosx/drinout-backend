FROM python:3.11-slim

# Instalamos dependencias del sistema necesarias para algunas librerías de Python
# (como conectores de base de datos o eventlet)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip wheel \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Exponemos el puerto, aunque Traefik lo manejará internamente
EXPOSE 5000

# Eliminamos el CMD de aquí, ya que el docker-compose.yml 
# tiene el comando definitivo con Gunicorn.