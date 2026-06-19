# Modèle de données des capteurs IoT – Flux pollution urbaine (OpenAQ)

## 1. Objectif

L’objectif de cette partie est de définir précisément :

- les **mesures de pollution** que nous allons collecter à partir de l’API OpenAQ,  
- la **structure des messages IoT** que nous utiliserons dans UrbanHub (simulant des capteurs),  
- le **référentiel des capteurs** (identifiants, localisation),  
- les règles de **mappage** entre les champs OpenAQ et notre modèle interne.

Ce modèle sera utilisé à la fois :

- par les scripts Python qui appellent l’API OpenAQ,  
- par les workflows n8n qui reçoivent les messages “IoT”,  
- par les pipelines de traitement (Silver/Gold) pour produire les indicateurs de pollution.

---

## 2. Polluants et indicateurs de bruit mesurés

### 2.1 Source OpenAQ

Nous utilisons la **REST API OpenAQ** (`https://api.openaq.org/`) qui fournit des mesures de qualité de l’air issues de capteurs installés dans plusieurs pays, dont la France.

L’API expose notamment le polluant mesuré (`parameter`), la valeur (`value`), l’unité (`unit`), la localisation et un timestamp de mesure.

### 2.2 Polluants principaux retenus

Pour UrbanHub, nous retenons les polluants suivants (liste alignée sur le sujet) :

- **PM2.5** – particules fines de diamètre inférieur à 2,5 µm (`pm25`)  
- **PM10** – particules de diamètre inférieur à 10 µm (`pm10`)  
- **NO₂** – dioxyde d’azote (`no2`)  
- **O₃** – ozone (`o3`)  
- **CO** – monoxyde de carbone (`co`)

Ces paramètres sont directement supportés par OpenAQ et présents dans les données France.

> Remarque : la consigne parle de “bruit”, mais OpenAQ ne fournit pas de niveau sonore. Dans ce projet, nous nous concentrons sur les **polluants atmosphériques** listés ci‑dessus.

---

## 3. Schéma d’une mesure IoT pollution/bruit

### 3.1 Champs de notre message IoT

Pour uniformiser les données venant de différentes API ou capteurs, nous définissons un **message IoT standard** au format JSON avec les champs suivants :

- `sensor_id` : identifiant unique du capteur logique dans UrbanHub  
- `timestamp` : date et heure de la mesure en UTC (format ISO 8601, ex. `2026-06-17T10:15:00Z`)  
- `city` : nom de la ville où se situe le capteur (ex. `Paris`)  
- `zone` : zone ou quartier (facultatif, peut être dérivé plus tard)  
- `latitude` : latitude de la station ou du capteur (float)  
- `longitude` : longitude de la station ou du capteur (float)  
- `pollutant` : code du polluant mesuré (`pm25`, `pm10`, `no2`, `o3`, `co`)  
- `value` : valeur mesurée (float)  
- `unit` : unité de la mesure (par ex. `µg/m³`, `ppm`)  
- `source` : chaîne indiquant la source (`"OpenAQ"`)  
- `raw_location_id` : identifiant original de la localisation côté OpenAQ (facultatif, utile pour le traçage)

### 3.2 Exemple de message JSON

```json
{
  "sensor_id": "FR_PARIS_001_PM25",
  "timestamp": "2026-06-17T10:15:00Z",
  "city": "Paris",
  "zone": "Paris-Centre",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "pollutant": "pm25",
  "value": 18.7,
  "unit": "µg/m³",
  "source": "OpenAQ",
  "raw_location_id": 12345
}
```

Ce format sera celui des messages envoyés par le simulateur IoT ou générés par le workflow n8n à partir des réponses OpenAQ.

---

## 4. Mappage OpenAQ → modèle IoT UrbanHub

### 4.1 Champs OpenAQ pertinents

Dans l’API OpenAQ v2, les mesures sont accessibles via l’endpoint `/v2/measurements` qui renvoie notamment :

- `location`: identifiant de la localisation  
- `locationId`: identifiant numérique de la localisation  
- `coordinates.latitude`, `coordinates.longitude`  
- `country`: code pays (ex. `FR`)  
- `city`: nom de la ville  
- `parameter`: code du polluant (`pm25`, `pm10`, `no2`, `o3`, `co`, etc.)  
- `value`: valeur numérique  
- `unit`: unité (souvent `µg/m³` ou `ppm`)  
- `date.utc`: timestamp en UTC

### 4.2 Table de mappage

| Modèle UrbanHub       | OpenAQ                                                   |
|-----------------------|----------------------------------------------------------|
| `sensor_id`           | Construit comme `FR_<CITY>_<LOCATIONID>_<PARAMETER>`     |
| `timestamp`           | `date.utc`                                              |
| `city`                | `city`                                                  |
| `zone`                | (optionnel) dérivé de `city` ou ajouté plus tard        |
| `latitude`            | `coordinates.latitude`                                  |
| `longitude`           | `coordinates.longitude`                                 |
| `pollutant`           | `parameter` (filtré sur pm25, pm10, no2, o3, co)        |
| `value`               | `value`                                                 |
| `unit`                | `unit`                                                  |
| `source`              | constante `"OpenAQ"`                                     |
| `raw_location_id`     | `locationId`                                            |

Ce mappage permet :

- de **standardiser** les données provenant d’OpenAQ,  
- de garder une **trace de la localisation d’origine** (`raw_location_id`),  
- de définir un `sensor_id` stable qui pourra être utilisé comme clé dans le Data Lake.

---

## 5. Référentiel des capteurs (sensor_id)

Même si OpenAQ fournit ses propres identifiants de stations, il est utile d’avoir un **référentiel interne** de capteurs UrbanHub.

### 5.1 Table de référence des capteurs

Nous définissons un petit référentiel (par exemple un fichier CSV ou une table dans Silver) avec les colonnes suivantes :

- `sensor_id` : identifiant UrbanHub (clé primaire)  
- `city` : ville (ex. Paris, Lyon, Marseille…)  
- `zone` : zone ou quartier (facultatif)  
- `latitude` : latitude  
- `longitude` : longitude  
- `raw_location_id` : identifiant de station OpenAQ  
- `description` : texte libre (facultatif, ex. “Station trafic urbain”, “Station fond urbain”)  

Exemple de lignes (simplifiées) :

```csv
sensor_id,city,zone,latitude,longitude,raw_location_id,description
FR_PARIS_001_PM25,Paris,Paris-Centre,48.8566,2.3522,12345,Station OpenAQ Paris centre - PM2.5
FR_PARIS_001_NO2,Paris,Paris-Centre,48.8566,2.3522,12345,Station OpenAQ Paris centre - NO2
FR_LYON_010_PM10,Lyon,Lyon-Centre,45.7640,4.8357,67890,Station OpenAQ Lyon centre - PM10
```

Dans la première version du projet, ce référentiel pourra être construit à partir des premières réponses de l’API OpenAQ (en listant les `locationId` et leurs coordonnées).

---

## 6. Utilisation du modèle dans la plateforme UrbanHub

Ce modèle de données IoT sera utilisé à plusieurs niveaux :

- **Ingestion**  
  - les scripts Python et workflows n8n transforment les réponses brutes OpenAQ en messages conformes au schéma `sensor_id + timestamp + pollutant + value + unit + location`.

- **Stockage Bronze**  
  - les messages JSON sont stockés tels quels dans MinIO (Bronze), éventuellement par jour et par ville.

- **Stockage Silver**  
  - une table Silver “mesures IoT pollution” reprendra exactement ces champs, nettoyés et typés.

- **Stockage Gold et analyses**  
  - des agrégations par `city`, `zone`, `pollutant`, `date` s’appuieront sur ces champs pour répondre aux questions métier :  
    - zones les plus polluées,  
    - variation journalière,  
    - polluants dominants,  
    - épisodes de pollution anormale.

---

## 7. Prochaines étapes (pour toi)

À partir de ce modèle :

1. Créer le fichier `iot_pollution/docs/iot_pollution_schema.md` avec ce contenu.  
2. Créer un fichier `data_samples/raw_openaq_sample.json` en copiant une vraie réponse d’OpenAQ et en la transformant selon ce schéma.  
3. Dans `scripts/simulate_iot_stream.py`, générer des messages au format défini ci‑dessus et les envoyer à ton webhook n8n.