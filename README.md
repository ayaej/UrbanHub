# UrbanHub - Partie 2 : Flux Streaming mobilité urbaine

Ce projet met en place une base de plateforme UrbanHub pour ingérer les flux de données CityBikes, stocker les événements dans PostgreSQL, publier en Kafka, archiver dans MinIO et diffuser en MQTT.

## Architecture proposée

- `n8n` : orchestration, webhook et streaming
- `kafka` + `zookeeper` : bus d'événements
- `postgres` : analytique et stockage des événements
- `minio` : stockage objet pour données brutes
- `mqtt` : broker pour diffusion en temps réel
- `ingester` : service Python de collecte CityBikes toutes les 60 secondes

## Fichiers clés

- `docker-compose.yml` : définition des services
- `Dockerfile` : image Python pour le service d'ingestion
- `requirements.txt` : dépendances Python
- `citybikes_ingest.py` : ingestion CityBikes, Kafka, PostgreSQL, MinIO, MQTT

## Installation

1. Installer Docker Desktop sur Windows.
2. Dans le dossier `UrbanHub`, lancer :

```powershell
docker compose up -d
```

3. Vérifier les services :

- `http://localhost:5678` pour `n8n`
- `http://localhost:9000` pour `MinIO`
- `http://localhost:9001` pour la console MinIO
- `localhost:5432` pour PostgreSQL
- `localhost:9092` pour Kafka
- `localhost:1883` pour MQTT

## Notes de déploiement

- Le service `ingester` démarre automatiquement et récupère les stations françaises CityBikes toutes les minutes.
- Les données sont envoyées vers :
  - Kafka topic `urbanhub.citybikes.stations`
  - PostgreSQL tables `citybikes_station_events` et `citybikes_station_last_status`
  - MinIO bucket `citybikes-raw`
  - MQTT topic `urbanhub/citybikes/<network>/<station_id>`

## Utilisation dans n8n

1. Créer un workflow n8n.
2. Ajouter un noeud `MQTT Trigger` pour écouter `urbanhub/citybikes/#`.
3. Ajouter un noeud `Webhook` si vous souhaitez exposer un endpoint public.
4. Ajouter un noeud `Postgres` ou `HTTP Request` pour analyser les données ou alimenter des dashboards.

## Questions métier couvertes

- Stations avec le plus fort taux d'utilisation : analyser `bikes_available` / (`bikes_available` + `free_slots`).
- Zones insuffisantes : chercher stations avec `free_slots == 0` et faible `bikes_available`.
- Pics d'utilisation journaliers : regrouper `event_timestamp` par heure sur `citybikes_station_events`.
- Déséquilibres géographiques : cartographier `latitude`/`longitude` et disponibilité.
- Stations critiques : identifier stations avec `bikes_available == 0` ou `free_slots == 0` pendant plusieurs cycles.

## Prochaine étape

- Compléter une interface n8n pour analyser les données en temps réel.
- Ajouter un dashboard Postgres / Grafana.
- Ajouter des alertes de rééquilibrage dans n8n ou MQTT.
