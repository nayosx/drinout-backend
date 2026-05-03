# --- Etapa Base ---
FROM python:3.11-slim AS base

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

# --- Etapa de Desarrollo ---
FROM base AS development
# Aquí podrías instalar dependencias solo de dev si las tuvieras
EXPOSE 5050
CMD ["python3", "main.py"]

# --- Etapa de Producción ---
FROM base AS production
EXPOSE 5000
# El comando se puede quedar aquí o en el compose
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "main:application"]
