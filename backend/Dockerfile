# ── Backend Dockerfile ────────────────────────────────────────────────────────
# Python 3.11 slim pour garder l'image légère
FROM python:3.11-slim

LABEL maintainer="Jaurès Wilson <jaures-wilson@example.com>"
LABEL description="Assistant IA de Réunion – Backend Flask"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
        build-essential \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads /app/exports /app/logs /app/data/chroma

RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

# start-period augmenté à 90s : le chargement de Whisper + init ChromaDB
# prend plusieurs secondes au premier démarrage, le healthcheck ne doit
# pas déclarer le conteneur "unhealthy" avant que tout soit prêt.
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=5 \
    CMD curl -f http://localhost:5000/api/live || exit 1

# --preload : charge l'app (et donc db.create_all()) UNE SEULE FOIS
# dans le processus maître avant de forker les workers.
# Sans ça, les 4 workers tentent chacun de créer les tables en même
# temps au premier démarrage → race condition SQLite ("table already exists").
CMD ["gunicorn", "app:create_app()", "-b", "0.0.0.0:5000", \
     "--workers", "4", "--threads", "2", "--timeout", "300", "--preload"]

     