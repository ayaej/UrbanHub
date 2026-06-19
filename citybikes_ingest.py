import json
import logging
import os
import time
from datetime import datetime, timezone

import boto3
import paho.mqtt.publish as publish
import psycopg2
import requests
from kafka import KafkaProducer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

CITYBIKES_API = "https://api.citybik.es/v2/networks"
TOPIC = "urbanhub.citybikes.stations"
MINIO_BUCKET = "citybikes-raw"

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_DB = os.getenv("POSTGRES_DB", "urbanhub")
POSTGRES_USER = os.getenv("POSTGRES_USER", "urbanhub")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "urbanhub")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

NETWORK_FILTER = ["FR"]

# Délai de base entre les requêtes par réseau (secondes)
REQUEST_DELAY = 2
# Délai du cycle principal (secondes)
CYCLE_DELAY = 60
# Backoff max en cas de 429 (secondes)
MAX_BACKOFF = 300


def json_serializer(obj):
    """Convert datetime objects to ISO format strings for JSON serialization."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def get_with_retry(url, timeout=20, max_retries=5):
    """
    GET avec gestion des erreurs 429 (Too Many Requests).
    Respecte le header Retry-After si présent, sinon backoff exponentiel.
    """
    delay = 10
    for attempt in range(1, max_retries + 1):
        response = requests.get(url, timeout=timeout)
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            wait = int(retry_after) if retry_after and retry_after.isdigit() else delay
            wait = min(wait, MAX_BACKOFF)
            logging.warning(
                "429 Too Many Requests sur %s — attente %ds (tentative %d/%d)",
                url, wait, attempt, max_retries,
            )
            time.sleep(wait)
            delay = min(delay * 2, MAX_BACKOFF)  # backoff exponentiel
            continue
        response.raise_for_status()
        return response
    # Dernière tentative après le dernier sleep
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response


def get_france_network_ids():
    response = get_with_retry(CITYBIKES_API)
    data = response.json().get("networks", [])

    networks = []
    for network in data:
        location = network.get("location", {})
        if location.get("country") in NETWORK_FILTER:
            networks.append({
                "id": network.get("id"),
                "name": network.get("name"),
                "city": location.get("city"),
            })
    logging.info("Found %d French CityBikes networks", len(networks))
    return networks


def fetch_network_stations(network_id):
    url = f"{CITYBIKES_API}/{network_id}"
    response = get_with_retry(url)
    network = response.json().get("network", {})
    stations = network.get("stations", [])
    logging.info("Loaded %d stations for network %s", len(stations), network_id)
    return network.get("name", network_id), stations


def create_postgres_tables(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS citybikes_station_events (
                event_id SERIAL PRIMARY KEY,
                station_id TEXT NOT NULL,
                network TEXT NOT NULL,
                station_name TEXT,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                bikes_available INTEGER,
                free_slots INTEGER,
                event_timestamp TIMESTAMPTZ,
                received_at TIMESTAMPTZ DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_citybikes_station_time
                ON citybikes_station_events (station_id, event_timestamp);
            CREATE TABLE IF NOT EXISTS citybikes_station_last_status (
                station_id TEXT PRIMARY KEY,
                network TEXT NOT NULL,
                station_name TEXT,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                bikes_available INTEGER,
                free_slots INTEGER,
                event_timestamp TIMESTAMPTZ,
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )
    conn.commit()


def archive_raw_payload(s3_client, network_name, payload):
    key = f"{network_name}/{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    s3_client.put_object(Bucket=MINIO_BUCKET, Key=key, Body=json.dumps(payload).encode("utf-8"))
    logging.debug("Archived raw payload to MinIO: %s", key)


def send_to_postgres(conn, station_data):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO citybikes_station_events (
                station_id, network, station_name, latitude, longitude,
                bikes_available, free_slots, event_timestamp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                station_data["station_id"],
                station_data["network"],
                station_data["station_name"],
                station_data["latitude"],
                station_data["longitude"],
                station_data["bikes_available"],
                station_data["free_slots"],
                station_data["timestamp"],
            ),
        )
        cur.execute(
            """
            INSERT INTO citybikes_station_last_status (
                station_id, network, station_name, latitude, longitude,
                bikes_available, free_slots, event_timestamp, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (station_id) DO UPDATE SET
                network = EXCLUDED.network,
                station_name = EXCLUDED.station_name,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                bikes_available = EXCLUDED.bikes_available,
                free_slots = EXCLUDED.free_slots,
                event_timestamp = EXCLUDED.event_timestamp,
                updated_at = NOW();
            """,
            (
                station_data["station_id"],
                station_data["network"],
                station_data["station_name"],
                station_data["latitude"],
                station_data["longitude"],
                station_data["bikes_available"],
                station_data["free_slots"],
                station_data["timestamp"],
            ),
        )
    conn.commit()


def send_to_kafka(producer, station_data):
    payload = json.dumps(station_data, default=json_serializer).encode("utf-8")
    producer.send(TOPIC, payload)


def publish_mqtt(station_data):
    try:
        topic = f"urbanhub/citybikes/{station_data['network']}/{station_data['station_id']}"
        publish.single(
            topic,
            payload=json.dumps(station_data, default=json_serializer),
            hostname=MQTT_HOST,
            port=MQTT_PORT,
        )
    except Exception as e:
        logging.warning("MQTT publish failed (non-critical): %s", e)


def build_station_record(network_name, station):
    timestamp = station.get("timestamp")
    if timestamp:
        try:
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            timestamp = datetime.now(timezone.utc)
    else:
        timestamp = datetime.now(timezone.utc)

    return {
        "station_id": station.get("id"),
        "station_name": station.get("name"),
        "latitude": station.get("latitude"),
        "longitude": station.get("longitude"),
        "bikes_available": station.get("free_bikes", 0),
        "free_slots": station.get("empty_slots", 0),
        "timestamp": timestamp,
        "network": network_name,
    }


def main():
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    create_postgres_tables(conn)

    s3_client = boto3.client(
        "s3",
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=boto3.session.Config(signature_version="s3v4"),
    )
    try:
        s3_client.create_bucket(Bucket=MINIO_BUCKET)
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        pass
    except Exception:
        logging.info("Bucket %s already exists or cannot be created", MINIO_BUCKET)

    # FIX : récupération de la liste des réseaux UNE SEULE FOIS au démarrage.
    # L'appel répété toutes les 60s dans la boucle causait le rate-limiting (429).
    networks = get_france_network_ids()

    while True:
        try:
            for network in networks:
                network_name, stations = fetch_network_stations(network["id"])
                archive_raw_payload(s3_client, network_name, {"network": network, "stations": stations})
                for station in stations:
                    station_data = build_station_record(network_name, station)
                    send_to_kafka(producer, station_data)
                    send_to_postgres(conn, station_data)
                    publish_mqtt(station_data)
                # Petit délai entre chaque réseau pour éviter le rate-limiting
                time.sleep(REQUEST_DELAY)
            logging.info("Cycle complete. Waiting %d seconds.", CYCLE_DELAY)
        except Exception as exc:
            logging.exception("Erreur pendant l'ingestion CityBikes: %s", exc)
        time.sleep(CYCLE_DELAY)


if __name__ == "__main__":
    main()