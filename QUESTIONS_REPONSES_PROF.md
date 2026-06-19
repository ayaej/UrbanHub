# ❓ Questions / Réponses - UrbanHub

*Questions simples, courtes et compréhensibles pour la présentation du projet*

---

## 🎯 QUESTIONS GÉNÉRALES

### Q1: Qu'est-ce que c'est UrbanHub?
**R:** C'est une plateforme qui collecte les données météo NOAA (2020-2025), les nettoie avec Python/Pandas, et génère 17,850 indicateurs pour analyser les conditions météo urbaines.

---

### Q2: À quoi ça sert?
**R:** À comprendre les tendances météoriques dans les villes pour aider les décideurs urbains. Par exemple: identifier les jours extrêmes, comparer les saisons, détecter les anomalies.

---

### Q3: Combien de données est-ce qu'il traite?
**R:** ~2,5 millions d'observations météo (observations horaires) provenant de 14 stations sur 6 ans (2020-2025).

---

## 🏗️ QUESTIONS ARCHITECTURE

### Q4: Expliquez les 3 couches (bronze, silver, gold)?
**R:**
- **Bronze**: Données brutes NOAA (CSV) - pas modifiées
- **Silver**: Données nettoyées et normalisées (Parquet) - prêtes pour l'analyse
- **Gold**: Données agrégées et insights (tableaux/graphiques) - pour la décision

---

### Q5: Pourquoi 3 couches et pas juste 1?
**R:** Pour la maintenabilité et la traçabilité. Si une erreur est détectée, on peut identifier à quel stage elle s'est produite et la corriger sans tout recommencer.

---

### Q6: Pourquoi Parquet au lieu de CSV?
**R:** Parquet est compressé (60% d'économie d'espace), plus rapide à lire en colonnes, et gère mieux les types de données numériques.

---

## 🔧 QUESTIONS TECHNOLOGIE

### Q7: Pourquoi Python + Pandas?
**R:** 
- Python: populaire, simple à apprendre
- Pandas: spécialisé dans le nettoyage et transformation de données tabulaires

---

### Q8: Pourquoi MinIO?
**R:** C'est un stockage S3-compatible open-source. Permet de simuler le cloud (AWS) sans coût, et le code reste compatible avec AWS si on migre.

---

### Q9: Pourquoi PostgreSQL?
**R:** Base de données relationnelle robuste pour stocker les données structurées et les requêtes SQL complexes (agrégations, joins).

---

### Q10: Pourquoi Docker?
**R:** Conteneurs légers pour garantir que le code fonctionne partout (Windows, Mac, Linux) sans dépendre de l'installation locale.

---

### Q11: Pourquoi n8n pour l'automatisation?
**R:** Workflow automation avec interface visuelle. Permet de déclencher le pipeline automatiquement chaque jour à 2h du matin sans écrire de cron complexe.

---

## 📊 QUESTIONS DONNÉES

### Q12: D'où viennent les données NOAA?
**R:** Du service Global Hourly d'NOAA (National Oceanic and Atmospheric Administration, USA). API gratuite avec données météo horaires depuis 1950.

---

### Q13: Comment gérez-vous les données manquantes?
**R:** Dans silver_processor.py, on remplace par des valeurs "NA" ou on interpole selon le contexte (température souvent interpolée, précipitation souvent mise à 0).

---

### Q14: Quels indicateurs générez-vous?
**R:**
- **Quotidiens**: min/max/moyenne de température, précipitation totale, vitesse du vent
- **Extrêmes**: jours > 30°C, vitesses de vent > 10m/s
- **Corrélations**: température vs humidité, vent vs précipitation
- **Annuels**: résumés par ville et saison

---

### Q15: Comment partitionnez-vous les données?
**R:** Partitionnement par `year/month/city` au niveau Silver, ce qui permet de charger rapidement un mois ou une ville spécifique sans scanner 6 ans.

---

## ⚙️ QUESTIONS PIPELINE

### Q16: Expliquez le flux du pipeline?
**R:**
1. Télécharger (downloader.py) → NOAA API
2. Nettoyer (silver_processor.py) → conversion unités, normalisation timestamps
3. Agréger (gold_aggregator.py) → indicateurs quotidiens/extrêmes
4. Visualiser (visualizer.py) → graphiques PNG
5. Exporter (postgres_export.py) → optionnel PostgreSQL

---

### Q17: Combien de temps prend un pipeline complet?
**R:** ~15 minutes pour télécharger + traiter 6 ans de données (2020-2025).

---

### Q18: Peut-on lancer le pipeline partiellement?
**R:** Oui! `python run_pipeline.py --skip-download` utilise les données déjà téléchargées. Ou `--use-minio --use-postgres` pour ajouter le stockage cloud et la base de données.

---

## 💾 QUESTIONS STOCKAGE

### Q19: Où sont stockées les données?
**R:**
- **Local**: `data/lake/bronze/`, `silver/`, `gold/`
- **MinIO**: `urbanhub/bronze/`, `silver/`, `gold/` (interface: localhost:9001)
- **PostgreSQL**: table `weather_daily` (si `--use-postgres`)

---

### Q20: Quelle est la taille totale des données?
**R:**
- Bronze (brutes): ~200 MB
- Silver (nettoyées): ~150 MB (compressées)
- Gold (agrégées): ~5 MB + graphiques

---

## 🎨 QUESTIONS VISUALISATION

### Q21: Quels graphiques générez-vous?
**R:** 
- Courbes de température saisonnière par ville
- Distribution des jours extrêmes (températures, vents)
- Heatmap des précipitations annuelles

---

### Q22: Pourquoi PNG au lieu d'interactive?
**R:** PNG facile à partager par email, imprimer, utiliser dans des rapports. Les données brutes (Parquet, CSV) sont disponibles pour analyses interactives.

---

## 🚀 QUESTIONS UTILISATION

### Q23: Quelles sont les 3 façons de lancer le projet?
**R:**
1. **Local** (5 min): `python run_pipeline.py` - juste Python
2. **Avec services** (20 min): Docker MinIO + PostgreSQL
3. **Automatisé** (30 min): Docker + n8n pour cron automatique

---

### Q24: Quelle option choisir?
**R:**
- Option 1 (Local) pour tester rapidement
- Option 2 (Services) pour proche du cloud production
- Option 3 (Automatisé) pour déploiement réel

---

### Q25: Comment accéder aux données après?
**R:**
```python
# Python local
import pandas as pd
df = pd.read_parquet('data/lake/gold/weather/weather_daily.parquet')

# Ou SQL PostgreSQL
SELECT * FROM weather_daily WHERE city='Paris' AND year=2025;

# Ou interface MinIO
# http://localhost:9001
```

---

## 🛡️ QUESTIONS ROBUSTESSE

### Q26: Comment gérez-vous les erreurs de téléchargement?
**R:** Retry logic avec exponential backoff dans downloader.py. Si un téléchargement échoue, on réessaie jusqu'à 3 fois avant de passer.

---

### Q27: Que faire si le pipeline s'arrête?
**R:** Il y a des checkpoints. Si ça échoue au Silver, les données Bronze restent. On peut relancer juste la Silver/Gold sans re-télécharger.

---

### Q28: Pourquoi lancer en mode développement et pas production?
**R:** Le header du README dit "DÉVELOPPEMENT UNIQUEMENT" car:
- Pas de validation complète des données
- Pas de monitoring/alertes
- Pas de chiffrement des connexions
- À améliorer avant utilisation réelle

---

## 📈 QUESTIONS AMÉLIORATIONS

### Q29: Quels sont les limites actuelles?
**R:**
- Juste météo (pas IoT sensors, traffic, events)
- 14 stations (petit réseau)
- Pas de ML/prédictions
- Pas d'API web pour accès temps réel

---

### Q30: Comment l'améliorer?
**R:**
- Ajouter capteurs IoT en temps réel
- Machine learning pour prédictions météo
- API FastAPI pour accès web
- Dashboard Streamlit/Grafana
- Alertes alerting automatiques

---

## 🔗 QUESTIONS INTÉGRATION

### Q31: Comment intégrer avec d'autres systèmes?
**R:** Grâce à PostgreSQL ou MinIO S3. N'importe quel système peut requêter PostgreSQL (SQL) ou accéder à MinIO (S3 API).

---

### Q32: Pouvez-vous ajouter d'autres sources de données?
**R:** Oui! Il suffit d'ajouter un nouveau downloader (downloader_iot.py) qui populate Bronze, puis réutiliser Silver/Gold.

---

## 📝 QUESTIONS CODE

### Q33: Combien de fichiers Python?
**R:** 
- **downloader.py**: télécharge NOAA (parallelisation HTTP)
- **silver_processor.py**: nettoie + normalise
- **gold_aggregator.py**: agrégations + statistiques
- **visualizer.py**: graphiques
- **postgres_export.py**: export PostgreSQL
- **storage.py**: abstraction stockage (local/MinIO)
- **utils.py**: utilitaires
- **config.py**: configuration

---

### Q34: Comment gérez-vous les configurations?
**R:** Fichier [config/datalake_config.json](../config/datalake_config.json) avec:
- Stations NOAA à télécharger
- Années à traiter
- Paramètres MinIO/PostgreSQL

---

### Q35: Qui peut utiliser ce code?
**R:** Ingénieurs données, data scientists, étudiants. Documentation fournie pour les 3 options d'utilisation.

---

## 🎓 QUESTIONS APPRENTISSAGE

### Q36: Qu'apprend-on avec ce projet?
**R:**
1. Pipeline ETL (Extract-Transform-Load)
2. Nettoyage données (Pandas)
3. Formats optimisés (Parquet)
4. Docker et conteneurs
5. Base de données (PostgreSQL)
6. Stockage cloud (MinIO/S3)
7. Automatisation workflows (n8n)
8. Visualisation (Matplotlib/Seaborn)

---

### Q37: C'est difficile à apprendre?
**R:** Non! Code commenté, README clair, 3 options simples. Peut démarrer avec juste Python (Option 1) et ajouter complexité progressivement.

---

### Q38: Combien de temps pour maîtriser le projet?
**R:**
- Comprendre pipeline: 1-2h
- Lancer Option 1: 5 min
- Maîtriser Docker: 1 jour
- Déployer en prod: 2-3 jours

---

## 🌍 QUESTIONS BUSINESS

### Q39: Quel est le cas d'usage réel?
**R:** Données pour planification urbaine: identifier quartiers à risque météo, planifier ressources (déneigeuses, pompes eau), alertes canicule/tempête.

---

### Q40: Pourquoi 6 ans de données (2020-2025)?
**R:** Pour avoir assez d'historique pour détecter tendances et anomalies. 1 an pas suffisant (cycle saisonnier).

---

## 📞 QUESTIONS SUPPORT

### Q41: Comment signaler un bug?
**R:** Documenter le problème (logs, configuration), l'environment (OS, Python version), puis GitHub issue avec reproduction step.

---

### Q42: Où trouver l'aide?
**R:**
- [README.md](../README.md) - vue d'ensemble
- [COMPLETE_GUIDE.md](../COMPLETE_GUIDE.md) - étapes détaillées
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) - architecture
- Commentaires dans le code

---

## 🎬 BON À SAVOIR

**Résumé rapide (si le prof demande):**
> UrbanHub télécharge 6 ans de météo NOAA, les nettoie en 3 couches (bronze/silver/gold) avec Python/Pandas, stocke les 17,850 indicateurs en Parquet ou PostgreSQL, et génère des graphiques pour l'analyse urbaine. Peut tourner localement (5 min), avec cloud MinIO (20 min), ou s'automatiser avec Docker (30 min).

**Technos clés:** Python, Pandas, Parquet, MinIO, PostgreSQL, Docker, n8n

**Temps**: ~15 min pour pipeline complet | ~5 min option simple | ~30 min option complète

---

*Dernière mise à jour: 2026-06-19*
