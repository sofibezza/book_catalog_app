# ---------- Builder Stage ----------
FROM python:3.11-slim AS builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Dependencias de compilación
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# CORRECCIÓN IMPORTANTE: La ruta relativa desde la raíz del proyecto
COPY backend/app/requirements.txt .

RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# ---------- Runtime Stage ----------
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Asegura que Python encuentre el módulo 'app'
ENV PYTHONPATH=/app

# Librería para conectarse a Postgres
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN adduser --disabled-password --gecos "" appuser

# Copiar dependencias instaladas
COPY --from=builder /install /usr/local

# Copiar el código fuente (backend/app -> /app/app)
COPY backend/app ./app

# Permisos
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]