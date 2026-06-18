# 🌆 UrbanHub - Smart City Platform

⚠️ **DÉVELOPPEMENT UNIQUEMENT**

Collecte données météo NOAA → Les nettoie → Génère indicateurs

---

## 🚀 LANCER (3 étapes)

```bash
pip install -r requirements.txt
python run_pipeline.py
ls data/lake/gold/weather/
```

**Résultat:** 17,850 indicateurs + 3 graphiques  
**Temps:** ~15 minutes

---

## 💡 Comment ça fonctionne

```
    MÉTÉO BRUTE NOAA
            ↓
      PYTHON TÉLÉCHARGE
            ↓
    PANDAS NETTOIE
    (Requests + Pandas + PyArrow)
            ↓
        RÉSULTATS
      (Parquet compressé)
            ↓
    data/lake/gold/weather/
```

---

## 3️⃣ TROIS FAÇONS D'UTILISER

### 1. 🔵 Code Local (5 min)
Juste Python qui nettoie les données

```bash
python run_pipeline.py
```

**Technos:**
- Python (langage)
- Pandas (nettoyage)
- PyArrow (format Parquet)
- Requests (téléchargement)

---

### 2. 🟢 + Services (20 min)
Ajoute stockage cloud (MinIO) + base données (PostgreSQL)

```bash
docker-compose up -d minio postgres
python run_pipeline.py --use-minio --use-postgres
```

**Technos supplémentaires:**
- MinIO (S3 storage)
- PostgreSQL (database)
- SQLAlchemy (ORM)
- boto3 (S3 client)
- Docker (containers)

---

### 3. 🟠 + Automatisation (30 min)
Tout dans Docker + cron automatique avec n8n

```bash
docker-compose up -d
# Aller à http://localhost:5678
# Configurer le workflow
```

**Technos supplémentaires:**
- n8n (workflow automation)
- Docker compose (orchestration)

---

## 🛠️ 5 Technos Requises

| Tech | Rôle |
|------|------|
| Python + Pandas + PyArrow | Nettoyage données |
| MinIO | Stockage S3 |
| n8n | Automatisation cron |
| Docker | Conteneurs |
| PostgreSQL | Base données |

👉 **[Voir comment elles fonctionnent](HOW_5_TECHNOLOGIES_WORK.md)**

---

## 📊 Ce que vous obtenez

✨ **weather_daily.parquet** = 17,850 lignes (indicateurs quotidiens)
✨ **weather_extreme_days.parquet** = 1,200 événements extrêmes
✨ **3 graphiques PNG** = Visualisations

---

## 📖 Pour plus d'infos

👉 **Lire [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md)** pour les 3 options en détail

---

**Status:** ✅ Prêt à l'emploi
