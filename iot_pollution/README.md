# UrbanHub – Partie 3 : Flux IoT Pollution Urbaine

Système de collecte, nettoyage et agrégation en temps réel des données de qualité de l'air pour les villes françaises, intégré à la plateforme UrbanHub.

---

## Sommaire

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture des données](#2-architecture-des-données)
3. [Structure du répertoire](#3-structure-du-répertoire)
4. [Polluants suivis](#4-polluants-suivis)
5. [Schéma des données](#5-schéma-des-données)
6. [Scripts Python](#6-scripts-python)
7. [Workflows n8n](#7-workflows-n8n)
8. [Base de données](#8-base-de-données)
9. [Dashboard Grafana](#9-dashboard-grafana)
10. [Lancer le système](#10-lancer-le-système)
11. [Questions métier](#11-questions-métier)
12. [Volumes et performances](#12-volumes-et-performances)

---

## 1. Vue d'ensemble

La Partie 3 d'UrbanHub implémente un pipeline complet de données IoT pour la pollution atmosphérique urbaine :

```
API OpenAQ  ──►  Script Python  ──►  Bronze (JSONL)  ──►  n8n Silver  ──►  n8n Gold  ──►  Grafana
                 (toutes les 5 min)   (fichier log)       (PostgreSQL)     (agrégats)     (dashboard)
```

**Source de données :** [OpenAQ API v3](https://api.openaq.org/) — réseau mondial de capteurs de qualité de l'air, couvrant plusieurs centaines de stations en France.

**Technologies utilisées :**

| Rôle | Outil |
|---|---|
| Collecte temps réel | Python 3.12 + `requests` |
| Couche Bronze | Fichier JSONL (`bronze_iot_openaq.log`) |
| Couche Silver | PostgreSQL via workflow n8n |
| Couche Gold | PostgreSQL (agrégats horaires + journaliers) |
| Orchestration | n8n (workflows automatisés) |
| Visualisation | Grafana 10 |

---

## 2. Architecture des données

Le pipeline suit une architecture **médaillon en trois couches** :

```
┌─────────────────────────────────────────────────────────────────┐
│  BRONZE  – Données brutes                                        │
│  data/bronze_iot/bronze_iot_openaq.log                          │
│  Format : JSONL (une mesure par ligne)                          │
│  Fréquence : toutes les 5 minutes                               │
│  Rétention : fichier cumulatif (append)                         │
└────────────────────────┬────────────────────────────────────────┘
                         │  Workflow n8n "IoT_Clean_Silver"
                         │  (toutes les 5 min – nouvelles lignes seulement)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  SILVER  – Données nettoyées                                     │
│  Table PostgreSQL : silver_iot_clean                            │
│  Nettoyage : valeurs hors plage, timestamps invalides           │
│  Normalisation : unités standardisées par polluant              │
│  Déduplication : UNIQUE (sensor_id, pollutant, datetime_utc)    │
└────────────────────────┬────────────────────────────────────────┘
                         │  Workflow n8n "IoT_Gold_Aggregates"
                         │  (toutes les heures – fenêtre fixe)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  GOLD  – Agrégats analytiques                                    │
│  Table horaire  : gold_pollution_hourly                         │
│  Table journalière : gold_pollution_daily_city                  │
│  Indicateurs : avg, max, min, count par capteur + par ville     │
└─────────────────────────────────────────────────────────────────┘
```

### Idempotence

Le pipeline est conçu pour être rejoué sans créer de doublons :
- **Bronze → Silver** : la table `iot_processing_state` mémorise le numéro de la dernière ligne traitée. Seules les nouvelles lignes sont ingérées à chaque cycle.
- **Silver → Gold** : les insertions utilisent `ON CONFLICT ... DO UPDATE` (UPSERT). Rejouer un cycle recalcule les mêmes valeurs sans créer de doublon.

---

## 3. Structure du répertoire

```
iot_pollution/
├── README.md                          # Ce fichier
├── scripts/
│   ├── discover_sensors.py            # Initialisation du référentiel de capteurs
│   └── collect_openaq_realtime.py     # Boucle de collecte temps réel
├── sql/
│   └── schema.sql                     # DDL complet (tables + index + contraintes)
├── workflows_n8n/
│   ├── IoT_Clean_Silver.json          # Workflow Bronze → Silver
│   └── IoT_Gold_Aggregates.json       # Workflow Silver → Gold
├── docs/
│   ├── iot_pollution_schema.md        # Modèle de données détaillé
│   ├── structure_data_lake_iot.md     # Structure du data lake IoT
│   └── questions_metier_iot.md        # Questions analytiques métier
└── config/
    └── openaq_config.example.yaml     # Exemple de configuration
```

---

## 4. Polluants suivis

| Code | Nom | Unité | Seuil OMS |
|---|---|---|---|
| `pm25` | Particules fines (< 2,5 µm) | µg/m³ | 15 µg/m³ (annuel) |
| `pm10` | Particules (< 10 µm) | µg/m³ | 45 µg/m³ (annuel) |
| `no2` | Dioxyde d'azote | µg/m³ | 40 µg/m³ (annuel) |
| `o3` | Ozone | µg/m³ | 100 µg/m³ (8h) |
| `co` | Monoxyde de carbone | mg/m³ | 4 mg/m³ (24h) |
| `so2` | Dioxyde de soufre | µg/m³ | 40 µg/m³ (24h) |

Les valeurs hors plage `[0 – 500 µg/m³]` sont rejetées dès la couche Bronze.

---

## 5. Schéma des données

### Message Bronze (JSONL)

Chaque ligne du fichier `bronze_iot_openaq.log` est un objet JSON :

```json
{
  "sensor_id": "12345_pm25",
  "location_id": 12345,
  "sensor_name": "Paris 13ème - Station OpenAQ",
  "city": "Paris",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "pollutant": "pm25",
  "value": 18.7,
  "unit": "µg/m³",
  "datetime_utc": "2026-06-19T10:00:00Z",
  "datetime_local": "2026-06-19T12:00:00+02:00",
  "source": "OpenAQ",
  "ingested_at": "2026-06-19T10:01:32.451Z"
}
```

### Table Silver – `silver_iot_clean`

| Colonne | Type | Description |
|---|---|---|
| `id` | BIGSERIAL | Clé primaire auto |
| `sensor_id` | VARCHAR(100) | Identifiant unique `{location_id}_{pollutant}` |
| `location_id` | BIGINT | ID OpenAQ de la station |
| `sensor_name` | TEXT | Nom de la station |
| `city` | VARCHAR(100) | Ville |
| `latitude` | DOUBLE PRECISION | Coordonnée |
| `longitude` | DOUBLE PRECISION | Coordonnée |
| `pollutant` | VARCHAR(20) | Code polluant (`pm25`, `no2`…) |
| `value` | DOUBLE PRECISION | Valeur mesurée |
| `unit` | VARCHAR(20) | Unité normalisée |
| `datetime_utc` | TIMESTAMPTZ | Horodatage UTC de la mesure |
| `source` | VARCHAR(50) | Source (`OpenAQ`) |
| `ingested_at` | TIMESTAMPTZ | Date d'ingestion |

Contrainte d'unicité : `UNIQUE (sensor_id, pollutant, datetime_utc)`

### Table Gold horaire – `gold_pollution_hourly`

| Colonne | Type | Description |
|---|---|---|
| `sensor_id` | VARCHAR(100) | Identifiant capteur |
| `pollutant` | VARCHAR(20) | Code polluant |
| `hour_utc` | TIMESTAMPTZ | Heure arrondie à l'heure (UTC) |
| `city` | VARCHAR(100) | Ville |
| `latitude` / `longitude` | DOUBLE PRECISION | Coordonnées |
| `avg_value` | DOUBLE PRECISION | Moyenne horaire |
| `max_value` | DOUBLE PRECISION | Maximum horaire |
| `min_value` | DOUBLE PRECISION | Minimum horaire |
| `samples_count` | INTEGER | Nombre de mesures |
| `computed_at` | TIMESTAMPTZ | Date de calcul |

Clé primaire : `(sensor_id, pollutant, hour_utc)`

### Table Gold journalière – `gold_pollution_daily_city`

| Colonne | Type | Description |
|---|---|---|
| `city` | VARCHAR(100) | Ville |
| `pollutant` | VARCHAR(20) | Code polluant |
| `day_utc` | DATE | Jour (UTC) |
| `avg_value` | DOUBLE PRECISION | Moyenne journalière |
| `max_value` | DOUBLE PRECISION | Maximum journalier |
| `min_value` | DOUBLE PRECISION | Minimum journalier |
| `samples_count` | INTEGER | Nombre total de mesures |
| `sensors_count` | INTEGER | Nombre de capteurs actifs |

Clé primaire : `(city, pollutant, day_utc)`

---

## 6. Scripts Python

### `discover_sensors.py` – Initialisation du référentiel

À exécuter **une fois** avant de lancer la collecte. Récupère la liste complète des stations de mesure françaises depuis l'API OpenAQ et la sauvegarde en JSON.

```bash
python iot_pollution/scripts/discover_sensors.py
```

**Ce que fait le script :**
1. Récupère l'ID numérique de la France via `/v3/countries`
2. Pagine sur `/v3/locations` (100 résultats par page) jusqu'à épuisement
3. Sauvegarde le résultat dans `iot_pollution/data/openaq_sensors_fr.json`

**Résultat :** fichier JSON listant toutes les stations françaises avec leurs coordonnées, paramètres mesurés, et identifiants OpenAQ.

---

### `collect_openaq_realtime.py` – Collecte temps réel

Boucle principale du pipeline IoT. Interroge chaque capteur toutes les **5 minutes** et écrit les mesures dans le fichier Bronze.

```bash
python iot_pollution/scripts/collect_openaq_realtime.py
```

**Fonctionnalités :**

| Fonctionnalité | Détail |
|---|---|
| Cycle | 300 secondes (5 min) entre chaque tour |
| Validation | Rejette les valeurs hors `[0 – 500]` |
| Normalisation | Unités standardisées via `UNIT_MAP` |
| Arrêt propre | Gère `SIGTERM` et `SIGINT` (Docker, Ctrl+C) |
| Stats de volume | Affiche messages/Ko par cycle et total cumulé |
| Format de sortie | JSONL (append au fichier Bronze) |

**Exemple de logs :**
```
2026-06-19 10:00:01 [INFO] 87 capteurs chargés depuis openaq_sensors_fr.json
2026-06-19 10:05:03 [INFO] Cycle 1 terminé : 62 messages en 187.3s | Total cumulé : 62 messages, 48.2 Ko
2026-06-19 10:10:05 [INFO] Cycle 2 terminé : 59 messages en 193.1s | Total cumulé : 121 messages, 94.1 Ko
```

**Variables d'environnement requises (fichier `.env`) :**

```env
OPENAQ_API_KEY=votre_clé_api_openaq
```

---

## 7. Workflows n8n

Les workflows s'importent depuis l'interface n8n (`http://localhost:5678`) via **Import from file**.

### `IoT_Clean_Silver.json` – Bronze → Silver

**Déclenchement :** toutes les 5 minutes (Cron)

```
[Cron 5min] → [Lire curseur last_line] → [Lire Bronze JSONL]
           → [Parser nouvelles lignes] → [Nettoyer & normaliser]
           → [UPSERT Silver] → [Mettre à jour curseur]
```

**Logique de nettoyage :**
- Rejette les valeurs `NaN` ou hors plage `[0 – 500]`
- Rejette les timestamps invalides
- Normalise les unités par type de polluant
- N'ingère que les lignes nouvelles depuis le dernier cycle (curseur `last_line`)

### `IoT_Gold_Aggregates.json` – Silver → Gold

**Déclenchement :** toutes les heures (Cron)

```
[Cron 1h] → [Sélectionner Silver heure précédente]
          → [Agréger par (sensor_id, pollutant, heure)]
          → [UPSERT Gold horaire]
          → [UPSERT Gold journalier par ville]
```

**Fenêtre temporelle :**
```sql
-- Heure complète précédente (ex : si 14h05 → [13h00, 14h00[)
WHERE datetime_utc >= DATE_TRUNC('hour', NOW()) - INTERVAL '1 hour'
  AND datetime_utc <  DATE_TRUNC('hour', NOW())
```

Cette fenêtre **fixe** évite la dérive des données (contrairement à `NOW() - 1h`).

---

## 8. Base de données

### Initialiser le schéma

```bash
psql -h localhost -U urbanhub -d urbanhub -f iot_pollution/sql/schema.sql
```

Ou depuis Docker :

```bash
docker exec -i postgres psql -U urbanhub -d urbanhub < iot_pollution/sql/schema.sql
```

Le script crée :
- `iot_processing_state` — table de curseur pour l'idempotence
- `silver_iot_clean` — mesures nettoyées avec index
- `gold_pollution_hourly` — agrégats horaires
- `gold_pollution_daily_city` — agrégats journaliers par ville

### Requêtes utiles

**Dernières mesures ingérées :**
```sql
SELECT city, pollutant, ROUND(value::NUMERIC, 1) AS val, unit, datetime_utc
FROM silver_iot_clean
ORDER BY datetime_utc DESC
LIMIT 20;
```

**Niveau moyen PM2.5 par ville (dernières 24h) :**
```sql
SELECT city, ROUND(AVG(avg_value)::NUMERIC, 1) AS moy_pm25
FROM gold_pollution_hourly
WHERE pollutant = 'pm25'
  AND hour_utc >= NOW() - INTERVAL '24 hours'
GROUP BY city
ORDER BY moy_pm25 DESC;
```

**Villes en dépassement OMS (PM2.5 > 15 µg/m³) :**
```sql
SELECT city, pollutant, ROUND(avg_value::NUMERIC, 1) AS moy, day_utc
FROM gold_pollution_daily_city
WHERE avg_value > 15 AND pollutant = 'pm25'
ORDER BY avg_value DESC, day_utc DESC;
```

**Pic de pollution horaire sur 7 jours :**
```sql
SELECT sensor_id, pollutant, hour_utc,
       ROUND(max_value::NUMERIC, 1) AS pic
FROM gold_pollution_hourly
WHERE hour_utc >= NOW() - INTERVAL '7 days'
ORDER BY max_value DESC
LIMIT 10;
```

---

## 9. Dashboard Grafana

Le dashboard IoT est disponible dans `grafana/dashboards/iot_pollution_dashboard.json`.

**URL :** `http://localhost:3000` (admin / admin)

**Panneaux disponibles :**

| Panneau | Type | Description |
|---|---|---|
| Capteurs actifs (24h) | Stat | Nombre de capteurs ayant émis des données |
| Mesures collectées (24h) | Stat | Total des mesures en Silver |
| Polluants suivis | Stat | Nombre de polluants distincts |
| Dernière ingestion | Stat | Délai depuis la dernière mesure reçue |
| Évolution horaire par polluant | Time series | Concentration moyenne par heure |
| Min / Moy / Max horaires | Time series | Plage des valeurs Gold |
| Niveau moyen par ville | Bar gauge | Classement des villes par pollution |
| Répartition par polluant | Pie chart | Part de chaque polluant dans les mesures |
| Tendance journalière par ville | Time series | Évolution sur plusieurs jours |
| Alertes PM2.5 > 50 µg/m³ | Table | Villes en dépassement critique |
| Alertes NO2 > 40 µg/m³ | Table | Villes dépassant le seuil OMS |
| 50 dernières mesures Silver | Table | Données brutes récentes avec coloration |

**Filtres interactifs :** polluant, ville, période temporelle.

**Importer le dashboard :**
1. Aller dans Grafana → Dashboards → Import
2. Charger le fichier `grafana/dashboards/iot_pollution_dashboard.json`
3. Sélectionner la datasource PostgreSQL (`urbanhub`)

---

## 10. Lancer le système

### Prérequis

- Docker & Docker Compose installés
- Clé API OpenAQ gratuite : [register.openaq.org](https://register.openaq.org)

### Étape 1 – Configuration

```bash
cp .env.example .env
# Éditer .env et renseigner :
# OPENAQ_API_KEY=votre_clé
```

### Étape 2 – Démarrer l'infrastructure

```bash
docker compose up -d postgres n8n grafana
```

### Étape 3 – Initialiser le schéma SQL

```bash
docker exec -i postgres psql -U urbanhub -d urbanhub < iot_pollution/sql/schema.sql
```

### Étape 4 – Découvrir les capteurs (une fois)

```bash
pip install -r requirements.txt
python iot_pollution/scripts/discover_sensors.py
```

Vérifie que le fichier `iot_pollution/data/openaq_sensors_fr.json` a bien été créé.

### Étape 5 – Importer les workflows n8n

1. Ouvrir `http://localhost:5678` (admin / admin)
2. Importer `iot_pollution/workflows_n8n/IoT_Clean_Silver.json`
3. Importer `iot_pollution/workflows_n8n/IoT_Gold_Aggregates.json`
4. Configurer la credential PostgreSQL dans n8n :
   - Host : `postgres`, Port : `5432`
   - Database : `urbanhub`, User : `urbanhub`, Password : `urbanhub`
5. Activer les deux workflows

### Étape 6 – Lancer la collecte

```bash
python iot_pollution/scripts/collect_openaq_realtime.py
```

Pour une exécution en arrière-plan (recommandé en prod) :

```bash
# Via Docker
docker compose up -d ingester

# Ou directement
nohup python iot_pollution/scripts/collect_openaq_realtime.py > logs/iot.log 2>&1 &
```

### Étape 7 – Vérifier le pipeline

```bash
# Vérifier le fichier Bronze
wc -l data/bronze_iot/bronze_iot_openaq.log

# Vérifier les données Silver
docker exec postgres psql -U urbanhub -d urbanhub \
  -c "SELECT COUNT(*), MIN(datetime_utc), MAX(datetime_utc) FROM silver_iot_clean;"

# Vérifier les données Gold
docker exec postgres psql -U urbanhub -d urbanhub \
  -c "SELECT COUNT(*) FROM gold_pollution_hourly;"
```

### Arrêt propre

```bash
# Le script Python gère SIGTERM proprement
kill -SIGTERM $(pgrep -f collect_openaq_realtime)

# Ou Ctrl+C dans le terminal
```

---

## 11. Questions métier

Le pipeline permet de répondre aux questions suivantes à partir des tables Gold :

**1. Quelles villes sont les plus polluées en PM2.5 ?**
```sql
SELECT city, ROUND(AVG(avg_value)::NUMERIC, 1) AS moy_pm25
FROM gold_pollution_daily_city
WHERE pollutant = 'pm25' AND day_utc >= CURRENT_DATE - 30
GROUP BY city ORDER BY moy_pm25 DESC LIMIT 10;
```

**2. À quelle heure de la journée la pollution NO2 est-elle la plus élevée ?**
```sql
SELECT EXTRACT(HOUR FROM hour_utc) AS heure,
       ROUND(AVG(avg_value)::NUMERIC, 1) AS moy_no2
FROM gold_pollution_hourly
WHERE pollutant = 'no2' AND hour_utc >= NOW() - INTERVAL '30 days'
GROUP BY heure ORDER BY moy_no2 DESC;
```

**3. Y a-t-il eu des épisodes de pollution anormale ?**
```sql
SELECT sensor_id, city, pollutant, hour_utc,
       ROUND(max_value::NUMERIC, 1) AS pic
FROM gold_pollution_hourly
WHERE max_value > 100
ORDER BY max_value DESC LIMIT 20;
```

**4. Combien de capteurs sont actifs par ville ?**
```sql
SELECT city, COUNT(DISTINCT sensor_id) AS capteurs_actifs
FROM gold_pollution_hourly
WHERE hour_utc >= NOW() - INTERVAL '24 hours'
GROUP BY city ORDER BY capteurs_actifs DESC;
```

**5. Quelle est la tendance sur les 7 derniers jours pour Paris ?**
```sql
SELECT day_utc, pollutant, ROUND(avg_value::NUMERIC, 1) AS moy
FROM gold_pollution_daily_city
WHERE city = 'Paris' AND day_utc >= CURRENT_DATE - 7
ORDER BY day_utc, pollutant;
```

---

## 12. Volumes et performances

### Estimations de volume

| Métrique | Valeur estimée |
|---|---|
| Capteurs France (OpenAQ) | ~100 à 300 stations |
| Mesures par cycle (5 min) | ~60 à 200 messages |
| Taille d'un message Bronze | ~500 à 800 octets |
| Volume Bronze par heure | ~3 à 10 Mo |
| Volume Bronze par jour | ~70 à 240 Mo |
| Lignes Silver par jour | ~17 000 à 57 000 |
| Lignes Gold horaire par jour | ~500 à 2 000 |

### Indicateurs de suivi

Le script de collecte affiche en temps réel :

```
Cycle N terminé : X messages en Y.Zs | Total cumulé : N messages, M Ko
```

Ces métriques permettent de suivre :
- La **disponibilité** de l'API OpenAQ (nombre de capteurs qui répondent)
- Le **débit d'ingestion** (Ko/cycle)
- La **volumétrie cumulée** du Bronze pour dimensionner le stockage

### Index en base

Tous les champs utilisés dans les requêtes d'agrégation et de filtrage sont indexés :

```sql
-- Silver
idx_silver_datetime   ON silver_iot_clean (datetime_utc DESC)
idx_silver_sensor     ON silver_iot_clean (sensor_id)
idx_silver_pollutant  ON silver_iot_clean (pollutant)
idx_silver_city       ON silver_iot_clean (city)

-- Gold horaire
idx_gold_hour         ON gold_pollution_hourly (hour_utc DESC)
idx_gold_pollutant    ON gold_pollution_hourly (pollutant)
idx_gold_city         ON gold_pollution_hourly (city)

-- Gold journalier
idx_gold_daily_day    ON gold_pollution_daily_city (day_utc DESC)
```
