# 🎯 Comment les 5 Technos Fonctionnent Ensemble

---

## 📊 Flux Visuel Simplifié

```
┌─────────────────────────────────────────────────────────┐
│ NOAA MÉTÉO BRUTE (600 fichiers CSV)                     │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────▼────────┐
        │ PYTHON TÉLÉCHARGE
        │ (Requests)      
        │ Parallélisé ×4  
        │ 45 secondes     
        └────────┬────────┘
                 │
        ┌────────▼────────────┐
        │ PANDAS NETTOIE      │
        │ Nettoyage données   │
        │ Conversion unités   │
        │ 5 minutes           │
        └────────┬────────────┘
                 │
        ┌────────▼────────────┐
        │ PYARROW COMPRESSE   │
        │ Format Parquet      │
        │ Compression Snappy  │
        │ Réduit de 25%       │
        └────────┬────────────┘
                 │
       ┌─────────┴──────────┐
       │                    │
  ┌────▼─────┐      ┌──────▼──────┐
  │ POSTGRESQL       │ MINIO (S3)  │
  │ (optionnel)      │ (optionnel) │
  │                  │             │
  │ 17,850 lignes    │ Fichiers    │
  │ Tables SQL       │ Parquet     │
  │ Vues analytics   │ Sauvegarde  │
  └────────────┘     └─────────────┘
       │                    │
       └────────┬───────────┘
                │
        ┌───────▼────────┐
        │ N8N AUTOMATISE │
        │ (optionnel)    │
        │                │
        │ Cron 2 AM      │
        │ Logs exécution │
        │ Notifications  │
        └───────┬────────┘
                │
        ┌───────▼────────┐
        │ DOCKER         │
        │ Tous services  │
        │ Container      │
        └────────────────┘
```

---

## ✅ OÙ CHAQUE TECHNO INTERVIENT

### 🔵 PYTHON (Toujours)
**Rôle:** Orchestre tout
**Code:** `src/run_pipeline.py`
```python
python run_pipeline.py
```

---

### 🔵 PANDAS (Toujours)
**Rôle:** Nettoie les données brutes
**Transforme:**
```
CSV brut NOAA
    ↓
Supprime colonnes inutiles
Convertit unités (°C, m/s, mm)
Gère valeurs manquantes
Harmonise timestamps UTC ISO 8601
    ↓
Fichiers nettoyés
```

**Exemple:** `src/silver_processor.py`
```python
import pandas as pd

df = pd.read_csv('data.csv')
df['temperature'] = df['TMP'] / 10  # Conversion
df.to_parquet('output.parquet')
```

---

### 🔵 PYARROW (Toujours)
**Rôle:** Compresse les données
**Format:** Parquet avec compression Snappy
```
150 MB (compressé)
vs
200 MB (CSV)
= 25% moins d'espace
```

**Exemple:**
```python
df.to_parquet('file.parquet', compression='snappy')
```

---

### 🟢 MINIO (Optionnel - Option 2 & 3)
**Rôle:** Stockage S3 pour données
**Où:** Conteneur Docker `minio`
**Port:** 9000 (S3), 9001 (Web UI)
**Utilisation:**
```python
import boto3

s3 = boto3.client('s3', endpoint_url='http://localhost:9000')
s3.upload_file('file.parquet', 'urbanhub', 'gold/file.parquet')
```

**Web UI:** http://localhost:9001

---

### 🟢 POSTGRESQL (Optionnel - Option 2 & 3)
**Rôle:** Base de données pour BI tools
**Où:** Conteneur Docker `postgres`
**Port:** 5432
**Tables créées:**
```
weather_daily (17,850 lignes)
weather_extreme_days (1,200 lignes)
weather_correlations
city_summary_annual
pipeline_runs
```

**Utilisation SQL:**
```sql
SELECT city, temperature_mean FROM weather_daily;
```

---

### 🟠 N8N (Optionnel - Option 3)
**Rôle:** Automatisation quotidienne
**Où:** Conteneur Docker `n8n`
**Port:** 5678
**Workflow:** Cron trigger → Python script → PostgreSQL logs

**Configuration:**
```
1. Ouvrir http://localhost:5678
2. Importer workflows/urbanhub_daily_pipeline.json
3. Configurer PostgreSQL credentials
4. Deploy
5. Exécution auto chaque jour à 2 AM
```

---

### 🟠 DOCKER (Optionnel - Option 2 & 3)
**Rôle:** Conteneuriser tous les services
**Fichier:** `docker-compose.yml`
**Services:**
```yaml
services:
  minio:      # Stockage S3
  postgres:   # Base données
  n8n:        # Automatisation
  urbanhub_pipeline:  # Script Python
```

**Lancer tout:**
```bash
docker-compose up -d
```

---

## 📊 TABLEAU SYNTHÉTIQUE

| Techno | Type | Usage | Option 1 | Option 2 | Option 3 |
|--------|------|-------|----------|----------|----------|
| **Python** | Langage | Orchestre | ✅ | ✅ | ✅ |
| **Pandas** | Lib Python | Nettoie | ✅ | ✅ | ✅ |
| **PyArrow** | Lib Python | Compresse Parquet | ✅ | ✅ | ✅ |
| **MinIO** | Service | Stockage S3 | ❌ | ✅ | ✅ |
| **PostgreSQL** | Service | Database | ❌ | ✅ | ✅ |
| **n8n** | Service | Cron auto | ❌ | ❌ | ✅ |
| **Docker** | Plateforme | Conteneurs | ❌ | ✅ | ✅ |

---

## 🎯 RÉSUMÉ

### Option 1 (Local)
```
Python télécharge → Pandas nettoie → PyArrow compresse → Fichiers locaux
```

### Option 2 (Services)
```
(Option 1) → MinIO stocke → PostgreSQL indexe
```

### Option 3 (Auto)
```
(Option 2) → n8n automatise → Docker orchestre
```

---

## ✨ EXEMPLE COMPLET (Option 3)

```
8 AM: Tu regardes les données
     → http://localhost:5678 (n8n)
     → http://localhost:9001 (MinIO)
     → psql localhost:5432 (PostgreSQL)

2 AM: n8n cron trigger
     → Lance Python
     → Télécharge NOAA
     → Pandas nettoie
     → PyArrow compresse
     → Sauve MinIO
     → Sauve PostgreSQL
     → Logs dans pipeline_runs
     → Email notification (optionnel)

9 AM Jour suivant: Données disponibles!
     → Analyse dans Power BI
     → Requête SQL
     → Export Excel
```

---

**Questions?** Voir [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md) pour les instructions étape par étape.
