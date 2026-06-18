# 📖 Guide Complet - UrbanHub

⚠️ **DÉVELOPPEMENT UNIQUEMENT** - Plateforme de développement, ne pas utiliser en production.

---

## 🎯 CHOISIR VOTRE OPTION

### ⚡ **OPTION 1: Code Local (5 minutes)**
Pour tester rapidement sans rien installer d'autre

### 📦 **OPTION 2: Avec Services (20 minutes)**
Ajoute stockage S3 (MinIO) + base de données (PostgreSQL)

### 🤖 **OPTION 3: Automatisation (30 minutes)**
Tout dans Docker + cron automatique (n8n) chaque jour à 2 AM

---

## ⚡ OPTION 1: Code Local

### C'est quoi?
Juste Python qui télécharge, nettoie et génère les indicateurs.

### Technos utilisées
- Python (langage)
- Pandas (nettoyage données)
- PyArrow (format Parquet compressé)
- Requests (téléchargement HTTP)

### Étapes

**1. Installer**
```bash
pip install -r requirements.txt
```

**2. Lancer**
```bash
python run_pipeline.py
```

**3. Vérifier**
```bash
ls data/lake/gold/weather/
# Vous verrez:
# - weather_daily.parquet (17,850 lignes)
# - weather_extreme_days.parquet (1,200 lignes)
# - 3 graphiques PNG
```

**4. Explorer en Python**
```python
import pandas as pd

# Charger les données
daily = pd.read_parquet('data/lake/gold/weather/weather_daily.parquet')

# Afficher les 5 premières lignes
print(daily.head())

# Température moyenne par ville
print(daily.groupby('city')['temperature_mean'].mean())
```

### Résultats
- Fichiers Parquet (optimisés, compressés)
- Stockés dans `data/lake/`
- Prêts pour analyse

### ✅ Avantages
- Rapide à tester
- Zéro dépendance externe
- Parfait pour développement

### ❌ Limitations
- Pas de base de données
- Pas de stockage cloud
- Pas d'automatisation

---

## 📦 OPTION 2: Avec Services (MinIO + PostgreSQL)

### C'est quoi?
Option 1 + Stockage S3 (MinIO) + Base de données (PostgreSQL)

### Technos utilisées
- Python, Pandas, PyArrow (comme option 1)
- MinIO (stockage S3-compatible)
- PostgreSQL (base de données)
- SQLAlchemy (ORM)
- boto3 (client S3)
- Docker (services)

### Étapes

**1. Démarrer les services**
```bash
docker-compose up -d minio postgres
```

**2. Attendre le démarrage**
```bash
sleep 30
docker-compose ps  # Vérifier que tout tourne
```

**3. Lancer le pipeline avec services**
```bash
pip install -r requirements.txt
python run_pipeline.py --use-minio --use-postgres
```

**4. Vérifier les données**

**Via MinIO (Stockage S3):**
```bash
# Interface web
# http://localhost:9001
# Login: minioadmin / minioadmin123
# Dossier: urbanhub/ → bronze/, silver/, gold/
```

**Via PostgreSQL (Base de données):**
```bash
docker-compose exec postgres psql -U urbanhub_user -d urbanhub

# Afficher les tables
\dt

# Compter les indicateurs
SELECT COUNT(*) FROM weather_daily;

# Voir les villes
SELECT DISTINCT city FROM weather_daily;

# Quitter
\q
```

**5. Explorer en Python (depuis PostgreSQL)**
```python
from sqlalchemy import create_engine
import pandas as pd

# Connexion
engine = create_engine('postgresql://urbanhub_user:urbanhub_password@localhost:5432/urbanhub')

# Charger depuis PostgreSQL
daily = pd.read_sql("SELECT * FROM weather_daily", engine)
print(daily.head())
```

### Résultats
- Fichiers Parquet dans MinIO (stockage S3)
- Tables PostgreSQL:
  - `weather_daily` (17,850 lignes)
  - `weather_extreme_days` (1,200 lignes)
  - `weather_correlations`
  - `city_summary_annual`
  - `pipeline_runs` (logs d'exécution)
- 4 vues SQL pour analytics:
  - `v_temperature_trends`
  - `v_extreme_events_summary`
  - `v_correlations_by_season`
  - `v_daily_metrics`

### ✅ Avantages
- Stockage persistant S3
- Requêtes SQL directes
- Prêt pour Power BI / Tableau / Looker
- Données partitionnées efficacement

### ❌ Limitations
- Pas d'automatisation
- Lancement manuel chaque fois

---

## 🤖 OPTION 3: Stack Complète (Docker + n8n)

### C'est quoi?
Option 2 + Automatisation quotidienne avec n8n (cron)

### Technos utilisées
- Tout de l'option 2
- n8n (orchestration workflow)
- Docker (tous les services)

### Étapes

**1. Démarrer tous les services**
```bash
docker-compose up -d
```

**Services lancés:**
- MinIO (port 9001)
- PostgreSQL (port 5432)
- n8n (port 5678)
- Pipeline Python (conteneur)

**2. Configurer n8n**

```bash
# Aller à http://localhost:5678
# Login: admin / admin123
```

Dans l'interface n8n:

```
1. Menu "Workflows"
   ↓
2. "Import from file"
   ↓
3. Sélectionner: workflows/urbanhub_daily_pipeline.json
   ↓
4. Dans le workflow, éditer le nœud "PostgreSQL"
   - Host: postgres
   - Port: 5432
   - Database: urbanhub
   - User: urbanhub_user
   - Password: urbanhub_password
   ↓
5. Cliquer "Deploy"
```

**3. Tester manuellement**

Dans n8n:
```
Workflows → urbanhub_daily_pipeline
↓
Bouton bleu "Execute"
```

**4. Résultats**

Le workflow s'exécute:
- Chaque jour à 2 AM automatiquement
- Télécharge les données NOAA
- Les nettoie (Pandas + PyArrow)
- Les exporte dans MinIO
- Les exporte dans PostgreSQL
- Enregistre l'exécution dans `pipeline_runs`

**5. Monitorer les exécutions**

Via PostgreSQL:
```bash
docker-compose exec postgres psql -U urbanhub_user -d urbanhub -c \
  "SELECT started_at, status FROM pipeline_runs ORDER BY started_at DESC LIMIT 10;"
```

Via n8n:
```
http://localhost:5678
→ Workflows → urbanhub_daily_pipeline
→ Onglet "Executions"
```

### Résultats
- Données téléchargées + traitées automatiquement
- Tout dans MinIO (cloud-ready)
- Tout dans PostgreSQL (BI-ready)
- Historique des exécutions
- Logs pour debugging

### ✅ Avantages
- Automatisation quotidienne
- Zéro intervention
- Stack production-ready
- Cloud-ready (MinIO)
- BI-ready (PostgreSQL)

### ❌ Limitations
- Plus complexe à configurer
- Nécessite Docker
- RAM nécessaire

---

## 📊 TABLEAU COMPARATIF

| Aspect | Option 1 | Option 2 | Option 3 |
|--------|----------|----------|----------|
| **Temps setup** | 5 min | 20 min | 30 min |
| **Technologies** | 3 | 6 | 7 |
| **Stockage** | Local | S3 + Local | S3 + Local |
| **Base données** | Non | PostgreSQL | PostgreSQL |
| **Automatisation** | Non | Non | Oui (cron) |
| **Pour quoi?** | Tester | Analytics BI | Production |

---

## 💡 EXEMPLES DE REQUÊTES

### Python - Charger depuis Parquet (Option 1)
```python
import pandas as pd

daily = pd.read_parquet('data/lake/gold/weather/weather_daily.parquet')

# Température moyenne
print(daily.groupby('city')['temperature_mean'].mean())

# Jours avec extrêmes
extreme = pd.read_parquet('data/lake/gold/weather/weather_extreme_days.parquet')
heat_waves = extreme[extreme['event_type'] == 'heat_wave']
print(f"Canicules: {len(heat_waves)}")
```

### SQL - Requête depuis PostgreSQL (Option 2 & 3)
```sql
-- Température moyenne par ville
SELECT city, AVG(temperature_mean) as temp_mean
FROM weather_daily
GROUP BY city
ORDER BY temp_mean DESC;

-- Événements extrêmes
SELECT city, event_type, COUNT(*) as count
FROM weather_extreme_days
GROUP BY city, event_type
ORDER BY count DESC;

-- Statistiques annuelles
SELECT * FROM city_summary_annual
WHERE city = 'Paris'
ORDER BY year DESC;
```

### Pandas depuis PostgreSQL (Option 2 & 3)
```python
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine('postgresql://urbanhub_user:urbanhub_password@localhost:5432/urbanhub')

# Requête complexe
paris = pd.read_sql("""
    SELECT date, temperature_mean, temperature_max, precipitation_sum
    FROM weather_daily
    WHERE city = 'Paris'
    ORDER BY date DESC
    LIMIT 100
""", engine)

print(paris.describe())
```

---

## 🐛 Troubleshooting

### Option 1: Erreur "No such file"
```bash
# Vérifier les fichiers
ls data/lake/bronze/
ls data/lake/silver/
ls data/lake/gold/
```

### Option 2: PostgreSQL timeout
```bash
# Redémarrer PostgreSQL
docker-compose restart postgres
sleep 10
```

### Option 3: n8n ne trouve pas credentials
```bash
# Vérifier la connexion
docker-compose logs postgres | tail -20
docker-compose logs n8n | tail -20
```

---

## 📁 Résumé Structure

```
Option 1:
├── src/
├── data/lake/
│   ├── bronze/ ← Données brutes
│   ├── silver/ ← Nettoyées (Parquet)
│   └── gold/   ← Indicateurs
└── requirements.txt

Option 2:
├── (Option 1)
├── docker-compose.yml
└── MinIO + PostgreSQL (conteneurs)

Option 3:
├── (Option 2)
├── workflows/urbanhub_daily_pipeline.json
└── n8n (automatisation)
```

---

## 🎯 Quelle option choisir?

```
Vous débutez?             → Option 1 (local)
Vous avez du temps?       → Option 2 (services)
Vous travaillez en équipe? → Option 3 (auto)
```

---

**Vous avez des questions?** Consultez [docs/EXAMPLES_ANALYSES.md](docs/EXAMPLES_ANALYSES.md) pour plus d'exemples.
