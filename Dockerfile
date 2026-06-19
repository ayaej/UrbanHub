FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY citybikes_ingest.py .


# Métadonnées
LABEL maintainer="UrbanHub Team"
LABEL description="UrbanHub Smart City Pipeline - NOAA Data Processing"

# Répertoire de travail
WORKDIR /app

# Installe dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copie requirements
COPY requirements.txt .

# Installe dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie code source
COPY src/ ./src/
COPY config/ ./config/
COPY run_pipeline.py .

# Crée répertoires
RUN mkdir -p logs data/lake/{bronze,silver,gold}

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV LOG_LEVEL=INFO

# Port santé check (optionnel)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Entrypoint
ENTRYPOINT ["python"]
CMD ["python", "citybikes_ingest.py","run_pipeline.py"]
