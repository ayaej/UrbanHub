FROM python:3.12-slim

LABEL maintainer="UrbanHub Team"
LABEL description="UrbanHub – Ingester CityBikes (streaming temps réel)"

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code source
COPY citybikes_ingest.py .

# Répertoires de données
RUN mkdir -p data/bronze_iot logs

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV LOG_LEVEL=INFO

# Healthcheck : vérifie que le process Python tourne
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD pgrep -f citybikes_ingest.py || exit 1

CMD ["python", "citybikes_ingest.py"]
