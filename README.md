# UrbanHub – Smart City Data Platform

Plateforme de données urbaines centralisant météo, mobilité et qualité de l'air dans un Data Lake Bronze/Silver/Gold. Elle expose les indicateurs via un backend FastAPI, un dashboard React et Grafana.

---

## Sommaire

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture globale](#2-architecture-globale)
3. [Stack technique](#3-stack-technique)
4. [Structure du projet](#4-structure-du-projet)
5. [Partie 1 – Météo NOAA (Batch)](#5-partie-1--météo-noaa-batch)
6. [Partie 2 – Mobilité CityBikes (Streaming)](#6-partie-2--mobilité-citybikes-streaming)
7. [Partie 3 – Pollution IoT (OpenAQ)](#7-partie-3--pollution-iot-openaq)
8. [Partie 4 – Analyse croisée & Frontend](#8-partie-4--analyse-croisée--frontend)
9. [Lancer le projet](#9-lancer-le-projet)
10. [Accès aux services](#10-accès-aux-services)
11. [Dataset analytique](#11-dataset-analytique)

---

## 1. Vue d'ensemble

UrbanHub simule un **jumeau numérique urbain** en agrégeant trois types de flux de données :

| Flux | Source | Fréquence | Technologies |
|---|---|---|---|
| **Batch** | NOAA (données météo historiques) | Périodique | Python, Pandas, PyArrow, MinIO |
| **Streaming** | CityBikes API (vélos en libre-service) | Toutes les 60 s | Kafka, MQTT, PostgreSQL, MinIO |
| **IoT** | OpenAQ API (qualité de l'air) | Toutes les 5 min | Python, n8n, PostgreSQL |

Les données passent par trois couches dans **MinIO (Data Lake)** puis **PostgreSQL** :

| Couche | Support | Contenu |
|---|---|---|
| **Bronze** | MinIO `urbanhub/bronze/` | Données brutes : CSV NOAA, payloads JSON CityBikes, JSONL OpenAQ |
| **Silver** | MinIO `urbanhub/silver/` + PostgreSQL | Données nettoyées, typées, dédupliquées |
| **Gold** | MinIO `urbanhub/gold/` + PostgreSQL | Agrégats analytiques horaires, journaliers, corrélations |

Le tout est exposé via :
- Un **backend FastAPI** (15 endpoints REST)
- Un **frontend React** avec 6 tableaux de bord
- **Grafana** avec dashboards CityBikes et IoT

---

## 2. Architecture globale

```
┌──────────────────────────────────────────────────────────────────────┐
│  SOURCES DE DONNÉES                                                   │
│  NOAA (météo)     CityBikes API (vélos)     OpenAQ API (pollution)   │
└────────┬───────────────────┬────────────────────────┬────────────────┘
         │ Batch             │ Streaming               │ IoT (5 min)
         ▼                   ▼                         ▼
┌────────────────┐  ┌────────────────────┐  ┌──────────────────────┐
│ run_pipeline.py│  │citybikes_ingest.py │  │collect_openaq_       │
│ (Python +      │  │(Python)            │  │realtime.py (Python)  │
│  Pandas)       │  │                    │  │                      │
└────────┬───────┘  └────────┬───────────┘  └──────────┬───────────┘
         │                   │ Kafka / MQTT             │
         ▼                   ▼                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  BRONZE                                                               │
│  data/lake/bronze/weather/   citybikes-raw (MinIO)   bronze_iot/     │
│  (CSV NOAA bruts)            (payloads JSON)          (JSONL)        │
└────────┬───────────────────┬────────────────────────┬────────────────┘
         │ silver_processor  │ n8n workflow            │ n8n IoT_Clean_Silver
         ▼                   ▼                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  SILVER  – PostgreSQL                                                 │
│  data/lake/silver/weather/   citybikes_station_events   silver_iot_clean │
└────────┬───────────────────┬────────────────────────┬────────────────┘
         │ gold_aggregator   │ n8n Analytics Workflow  │ n8n IoT_Gold_Aggregates
         ▼                   ▼                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  GOLD  – PostgreSQL                                                   │
│  data/lake/gold/weather/     citybikes analytics      gold_pollution_hourly  │
│  urbanhub_analytics.csv      (requêtes SQL)           gold_pollution_daily_city │
└────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐    ┌───────────────────────┐
│  Backend FastAPI (port 8000)        │    │  Grafana (port 3000)  │
│  15 endpoints REST                  │    │  Dashboards CityBikes │
└────────────────┬────────────────────┘    │  + IoT Pollution      │
                 ▼                         └───────────────────────┘
┌────────────────────────────────────┐
│  Frontend React (port 80)          │
│  Overview · Météo · Mobilité       │
│  Pollution · Analytics · Archi     │
└────────────────────────────────────┘
```

---

## 3. Stack technique

| Composant | Outil | Rôle |
|---|---|---|
| **Orchestration** | n8n | Workflows Batch/Streaming/IoT, webhooks |
| **Message broker** | Apache Kafka + Zookeeper | Bus d'événements CityBikes |
| **IoT messaging** | MQTT (Eclipse Mosquitto) | Diffusion temps réel des capteurs |
| **Object storage** | MinIO | Data Lake S3-compatible (Bronze/Silver/Gold) |
| **Base de données** | PostgreSQL 15 | Tables Silver et Gold, backend n8n |
| **Traitement données** | Python 3.12 + Pandas + PyArrow | Pipelines Batch et IoT |
| **Backend API** | FastAPI + asyncpg | 15 endpoints REST |
| **Frontend** | React 19 + Tailwind + Recharts | 6 tableaux de bord |
| **Visualisation** | Grafana 10 | Dashboards CityBikes et pollution |
| **Administration DB** | pgAdmin | Interface web PostgreSQL |
| **Conteneurisation** | Docker + Docker Compose | Déploiement local complet |

---

## 4. Structure du projet

```
UrbanHub/
│
├── docker-compose.yml              # 12 services (infra + app + observabilité)
├── Dockerfile                      # Image ingester CityBikes
├── Dockerfile.backend              # Image backend FastAPI
├── nginx.conf                      # Proxy frontend
├── mosquitto.conf                  # Config MQTT
├── requirements.txt                # Dépendances Python communes
├── .env.example                    # Variables d'environnement à copier
│
├── citybikes_ingest.py             # [Partie 2] Ingestion CityBikes temps réel
├── citybikes_analytics_queries.sql # [Partie 2] Requêtes analytiques SQL
├── UrbanHub_CityBikes_Analytics_Workflow.json # [Partie 2] Workflow n8n
│
├── run_pipeline.py                 # [Partie 1] Orchestrateur pipeline météo
├── src/                            # [Partie 1] Modules pipeline météo
│   ├── config.py                   # Stations NOAA françaises
│   ├── downloader.py               # Téléchargement parallèle NOAA
│   ├── silver_processor.py         # Bronze → Silver (Pandas + Parquet)
│   ├── gold_aggregator.py          # Silver → Gold (indicateurs météo)
│   ├── visualizer.py               # Graphiques matplotlib
│   ├── storage.py                  # Abstraction MinIO / local
│   ├── postgres_export.py          # Export Gold vers PostgreSQL
│   ├── utils.py                    # Helpers communs
│   └── setup_datalake.py           # Initialisation des répertoires
│
├── iot_pollution/                  # [Partie 3] Pipeline IoT pollution
│   ├── README.md                   # Documentation complète Partie 3
│   ├── scripts/
│   │   ├── discover_sensors.py     # Initialisation référentiel capteurs FR
│   │   └── collect_openaq_realtime.py # Collecte OpenAQ → Bronze JSONL
│   ├── sql/
│   │   └── schema.sql              # DDL Silver + Gold IoT
│   ├── workflows_n8n/
│   │   ├── IoT_Clean_Silver.json   # Workflow Bronze → Silver (5 min)
│   │   └── IoT_Gold_Aggregates.json # Workflow Silver → Gold (1h)
│   └── docs/
│       ├── iot_pollution_schema.md # Modèle de données IoT
│       ├── structure_data_lake_iot.md
│       └── questions_metier_iot.md
│
├── backend/                        # [Partie 4] API REST
│   ├── server.py                   # FastAPI – 15 endpoints
│   └── requirements.txt
│
├── frontend/                       # [Partie 4] Interface React
│   ├── src/
│   │   ├── App.js                  # Router (6 routes dashboard)
│   │   ├── pages/
│   │   │   ├── Landing.jsx         # Page d'accueil
│   │   │   ├── Overview.jsx        # Vue d'ensemble (KPIs + carte France)
│   │   │   ├── Weather.jsx         # Météo NOAA
│   │   │   ├── Mobility.jsx        # CityBikes temps réel
│   │   │   ├── Pollution.jsx       # Qualité de l'air IoT
│   │   │   ├── Analytics.jsx       # Corrélations croisées
│   │   │   ├── Architecture.jsx    # Schéma de la plateforme
│   │   │   └── Settings.jsx
│   │   └── components/
│   └── package.json
│
├── grafana/                        # [Partie 4] Dashboards Grafana
│   ├── dashboard.json              # Dashboard CityBikes (10 panneaux)
│   ├── dashboards/
│   │   ├── urbanhub-dashboard.json # Dashboard principal
│   │   └── iot_pollution_dashboard.json # Dashboard IoT (7 panneaux)
│   └── provisioning/
│
├── urbanhub_partie4.ipynb          # [Partie 4] Notebook analyse croisée
├── urbanhub_analytics.csv          # Dataset analytique (480 lignes)
└── urbanhub_timeseries_interactive.html # Graphique Plotly interactif
```

---

## 5. Partie 1 – Météo NOAA (Batch)

**Responsable :** pipeline météo historique depuis les stations NOAA françaises.

### Ce que ça fait

Le script `run_pipeline.py` exécute 7 étapes séquentielles :

```
1. Initialisation du Data Lake (répertoires)
2. Téléchargement parallèle NOAA (stations FR : LFPG, LFPO, LFML…)
3. Bronze → Silver  (Pandas : nettoyage, typage, Parquet Snappy)
4. Silver → Gold    (agrégats : indicateurs quotidiens, jours extrêmes)
5. Génération de graphiques (matplotlib)
6. Synchronisation MinIO (optionnel)
7. Export PostgreSQL (optionnel)
```

### Lancer

```bash
# Minimal (local seulement)
pip install -r requirements.txt
python run_pipeline.py

# Avec MinIO + PostgreSQL
python run_pipeline.py --use-minio --use-postgres

# Options
python run_pipeline.py --skip-download --workers 8
```

### Sorties

| Fichier | Contenu |
|---|---|
| `data/lake/silver/weather/` | Parquet partitionné par année/mois/ville |
| `data/lake/gold/weather/weather_daily.parquet` | 17 850 indicateurs quotidiens |
| `data/lake/gold/weather/weather_extreme_days.parquet` | Événements météo extrêmes |

---

## 6. Partie 2 – Mobilité CityBikes (Streaming)

**Responsable :** ingestion temps réel des stations de vélos en libre-service françaises.

### Ce que ça fait

`citybikes_ingest.py` tourne en boucle toutes les **60 secondes** et :
1. Appelle l'API CityBikes (réseaux français)
2. Publie chaque événement dans **Kafka** (topic `urbanhub.citybikes.stations`)
3. Insère dans **PostgreSQL** (`citybikes_station_events` + `citybikes_station_last_status`)
4. Archive le payload brut dans **MinIO** (bucket `citybikes-raw`)
5. Diffuse en **MQTT** (topic `urbanhub/citybikes/<network>/<station_id>`)

### Tables PostgreSQL

| Table | Description |
|---|---|
| `citybikes_station_events` | Historique complet des événements (bikes_available, free_slots, timestamp) |
| `citybikes_station_last_status` | Statut courant de chaque station (upsert) |

### Workflow n8n

Importer `UrbanHub_CityBikes_Analytics_Workflow.json` dans n8n.  
Webhook disponible : `http://localhost:5678/webhook/citybikes-report`

### Requêtes analytiques

Voir `citybikes_analytics_queries.sql` :
- Stations au plus fort taux d'utilisation
- Zones avec pénurie de vélos
- Pics d'utilisation par heure
- Déséquilibres géographiques
- Stations critiques (0 vélo ou 0 place)

---

## 7. Partie 3 – Pollution IoT (OpenAQ)

**Responsable :** collecte temps réel de la qualité de l'air depuis les capteurs français OpenAQ.

> Documentation complète : [`iot_pollution/README.md`](iot_pollution/README.md)

### Pipeline en résumé

```
OpenAQ API → collect_openaq_realtime.py → Bronze JSONL
           → n8n IoT_Clean_Silver       → silver_iot_clean (PostgreSQL)
           → n8n IoT_Gold_Aggregates    → gold_pollution_hourly + gold_pollution_daily_city
```

### Polluants suivis

PM2.5, PM10, NO₂, O₃, CO, SO₂ — unités normalisées (µg/m³ / mg/m³)

### Démarrage rapide

```bash
# 1. Initialiser les capteurs (une fois)
python iot_pollution/scripts/discover_sensors.py

# 2. Lancer la collecte
python iot_pollution/scripts/collect_openaq_realtime.py

# 3. Initialiser le schéma SQL
psql -U urbanhub -d urbanhub -f iot_pollution/sql/schema.sql

# 4. Importer les workflows dans n8n (http://localhost:5678)
#    IoT_Clean_Silver.json + IoT_Gold_Aggregates.json
```

---

## 8. Partie 4 – Analyse croisée & Frontend

**Responsable :** croisement des trois sources de données et exposition via API + interface web.

### Backend FastAPI

Fichier : `backend/server.py` — démarre sur le port **8000**.

| Domaine | Endpoints |
|---|---|
| Météo | `GET /weather/timeseries` · `/weather/cities` · `/weather/alerts` |
| Mobilité | `GET /mobility/stations` · `/mobility/timeline` · `/mobility/critical` · `/mobility/networks` · `/mobility/history/{id}` |
| Pollution | `GET /pollution/sensors` · `/pollution/timeline` · `/pollution/comparison` |
| Analytics | `GET /analytics/kpis` · `/analytics/correlation` · `/analytics/insights` |
| Architecture | `GET /architecture/flows` |
| Santé | `GET /` |

### Frontend React

6 tableaux de bord accessibles depuis `http://localhost:80` :

| Page | Contenu |
|---|---|
| **Overview** | KPIs globaux, carte France temps réel, insights automatiques |
| **Météo** | Séries temporelles NOAA, carte météo, alertes |
| **Mobilité** | Stations CityBikes, timeline 24h, stations critiques |
| **Pollution** | Carte IoT, timeline 48h PM2.5/NO₂, comparaison villes, alertes pics |
| **Analytics** | Corrélations météo↔pollution et météo↔mobilité, scatter plots |
| **Architecture** | Schéma du pipeline de données |

### Notebook analytique

`urbanhub_partie4.ipynb` croise les trois sources Gold et calcule :

- **Score favorabilité vélo** — composite température/pluie/vent [0-100]
- **Corrélations** météo → pollution, météo → mobilité
- **Score d'atypie journalière** — détection d'anomalies multi-sources via z-scores
- Graphiques interactifs Plotly

---

## 9. Lancer le projet

### Prérequis

- Docker Desktop
- Python 3.12+
- Clé API OpenAQ gratuite : [register.openaq.org](https://register.openaq.org)

### Configuration

```bash
cp .env.example .env
# Renseigner OPENAQ_API_KEY dans .env
```

### Démarrage complet

```bash
# 1. Démarrer toute l'infrastructure
docker compose up -d

# 2. Initialiser le schéma IoT (première fois)
docker exec -i postgres psql -U urbanhub -d urbanhub < iot_pollution/sql/schema.sql

# 3. Pipeline météo NOAA
pip install -r requirements.txt
python run_pipeline.py --use-postgres

# 4. Découverte des capteurs pollution (première fois)
python iot_pollution/scripts/discover_sensors.py

# 5. Collecte pollution en continu
python iot_pollution/scripts/collect_openaq_realtime.py &

# 6. Build et lancer le frontend (optionnel, nginx le sert sinon)
cd frontend && yarn install && yarn build && cd ..
```

### Importer les workflows n8n

1. Ouvrir `http://localhost:5678` → admin / admin
2. Créer une credential PostgreSQL nommée **`UrbanHub Postgres`** :
   - Host : `postgres`, Port : `5432`, DB : `urbanhub`, User : `urbanhub`, Password : `urbanhub`
3. Importer dans cet ordre :
   - `iot_pollution/workflows_n8n/IoT_Clean_Silver.json` (Bronze → Silver, CRON 5 min)
   - `iot_pollution/workflows_n8n/IoT_Gold_Aggregates.json` (Silver → Gold, CRON 1h)
   - `UrbanHub_CityBikes_Analytics_Workflow.json` (webhook analytique CityBikes)
   - `workflows/urbanhub_daily_pipeline.json` (météo NOAA, CRON 2h)
   - **`workflows/urbanhub_master_orchestrator.json`** (orchestrateur principal)
4. Activer tous les workflows

#### Workflows disponibles

| Fichier | Rôle | Déclencheur |
|---|---|---|
| `urbanhub_master_orchestrator.json` | **Orchestrateur principal** – lance tout le pipeline en séquence | Manuel + CRON 2h |
| `urbanhub_daily_pipeline.json` | Pipeline météo NOAA seul (avec MinIO + PostgreSQL) | CRON 2h + Manuel |
| `IoT_Clean_Silver.json` | Bronze IoT → Silver PostgreSQL | CRON 5 min |
| `IoT_Gold_Aggregates.json` | Silver → Gold horaire + journalier | CRON 1h |
| `UrbanHub_CityBikes_Analytics_Workflow.json` | Rapport analytique CityBikes à la demande | Webhook GET |

#### Architecture du workflow maître

```
[Manuel] ──┐
[CRON 2h] ─┴──► [1. Init MinIO buckets]
                        │
           ┌────────────┼────────────────────────┐
           ▼            ▼                        ▼
  [2. Météo NOAA]  [3. Bronze IoT→MinIO]  [4. IoT Silver]
  run_pipeline.py  upload_bronze_to_minio      │
  --use-minio           │               [4b→4e : Read/Parse/
  --use-postgres         └──────────────  Upsert/Cursor]
           │                                    │
           └────────────────────────────────────┤
                                                ▼
                                     [5. IoT Gold horaire]
                                                │
                                     [5b. IoT Gold ville/jour]
                                                │
                                     [6. Log run PostgreSQL]
```

---

## 10. Accès aux services

| Service | URL | Identifiants |
|---|---|---|
| **Frontend React** | http://localhost:80 | — |
| **Backend API** | http://localhost:8000/docs | — |
| **Grafana** | http://localhost:3000 | admin / admin |
| **n8n** | http://localhost:5678 | admin / admin |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin |
| **pgAdmin** | http://localhost:5050 | admin@urbanhub.fr / admin |
| **Kafka** | localhost:9092 | — |
| **PostgreSQL** | localhost:5432 | urbanhub / urbanhub |
| **MQTT** | localhost:1883 | — |

### Dashboards Grafana

Les dashboards sont **chargés automatiquement** au démarrage de Grafana (provisioning).

| Dashboard | Contenu | Panneaux |
|---|---|---|
| `grafana/dashboards/urbanhub-dashboard.json` | CityBikes – KPIs, timeline, stations critiques | 10 |
| `grafana/dashboards/iot_pollution_dashboard.json` | IoT Pollution – par polluant, par ville, alertes | 7 |

### Structure MinIO Data Lake

```
urbanhub/               ← bucket principal
├── bronze/
│   ├── weather/        ← CSV NOAA bruts (run_pipeline.py)
│   ├── citybikes/      ← Payloads JSON CityBikes (citybikes_ingest.py)
│   └── iot/
│       └── YYYY-MM-DD/ ← JSONL OpenAQ (upload_bronze_to_minio.py)
├── silver/
│   └── weather/        ← Parquet Snappy (run_pipeline.py)
└── gold/
    └── weather/        ← Parquet agrégats (run_pipeline.py)

citybikes-raw/          ← bucket dédié CityBikes (legacy)
```

---

## 11. Dataset analytique

`urbanhub_analytics.csv` — **480 lignes** (4 villes × 120 jours)

Colonnes principales :

| Colonne | Description |
|---|---|
| `date`, `city` | Clés de granularité (Paris, Lyon, Marseille, Lille) |
| `temperature_avg_c`, `precipitation_mm`, `wind_speed_kmh` | Météo NOAA |
| `avg_bikes_available`, `occupancy_rate`, `nb_trajets_estimes` | Mobilité CityBikes |
| `pm25`, `pm10`, `no2`, `o3`, `co`, `pollution_index` | Pollution IoT [0-100] |
| `score_meteo_favorable_velo` | Score favorabilité mobilité douce [0-100] |
| `atypie_score` | Score anomalie journalière (z-scores) |

---

## Auteurs

Projet réalisé par une équipe de 4 étudiants en 5ème année IPSSI Paris dans le cadre du module Big Data / Smart City.

| Partie | Périmètre |
|---|---|
| Partie 1 | Pipeline météo NOAA Batch |
| Partie 2 | Streaming mobilité CityBikes |
| Partie 3 | IoT pollution OpenAQ |
| Partie 4 | Analyse croisée, Frontend React, Backend FastAPI |
