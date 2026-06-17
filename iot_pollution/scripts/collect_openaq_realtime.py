import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

# ----- Config & .env -----

# Racine du projet : UrbanHub/
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

API_KEY = os.getenv("OPENAQ_API_KEY")
N8N_WEBHOOK_IOT = os.getenv("N8N_WEBHOOK_IOT")

if not API_KEY:
    raise RuntimeError("OPENAQ_API_KEY non définie (voir fichier .env)")
if not N8N_WEBHOOK_IOT:
    raise RuntimeError("N8N_WEBHOOK_IOT non défini (voir fichier .env)")

HEADERS = {
    "X-API-Key": API_KEY,          # auth OpenAQ v3 [web:171][web:179]
    "Accept": "application/json",
}

# Endpoint Latest par location : /v3/locations/{locations_id}/latest [web:172][web:213]
LATEST_BASE_URL = "https://api.openaq.org/v3/locations"

SENSORS_FILE = ROOT_DIR / "iot_pollution" / "data" / "openaq_sensors_fr.json"
POLL_INTERVAL_SECONDS = 300  # toutes les 5 minutes (ajuste si besoin)


# ----- Fonctions utilitaires -----

def load_sensors(path: Path) -> list:
    if not path.exists():
        raise FileNotFoundError(f"Fichier capteurs introuvable : {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def fetch_latest_for_location(location_id: int):
    """
    Récupère les dernières mesures pour un location_id donné via
    /v3/locations/{locations_id}/latest, comme décrit dans la doc. [web:172][web:213]
    """
    url = f"{LATEST_BASE_URL}/{location_id}/latest"
    params = {
        "limit": 1,
        "page": 1,
    }
    resp = requests.get(url, params=params, headers=HEADERS, timeout=20)
    print(f"Status latest ({location_id}):", resp.status_code, resp.text[:200])
    if resp.status_code == 404:
        # Certaines stations peuvent ne pas avoir de données "latest"
        return None
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    return results[0] if results else None


def build_event(location: dict, latest: dict) -> dict:
    """
    Construit un payload à envoyer à n8n à partir des infos capteur + dernières mesures.
    La structure est volontairement générique, à adapter à ton workflow n8n. [web:172][web:201]
    """
    now = datetime.now(timezone.utc).isoformat()
    return {
        "timestamp": now,
        "location_id": location.get("location_id"),
        "name": location.get("name"),
        "country": location.get("country"),
        "city": location.get("city"),
        "coordinates": location.get("coordinates"),
        "provider": location.get("provider"),
        "parameters": location.get("parameters"),
        "latest": latest,
    }


def send_to_n8n(event: dict):
    resp = requests.post(N8N_WEBHOOK_IOT, json=event, timeout=20)
    print("Status n8n:", resp.status_code, resp.text[:200])
    resp.raise_for_status()


# ----- Boucle principale -----

def main():
    sensors = load_sensors(SENSORS_FILE)
    print(f"{len(sensors)} capteurs chargés depuis {SENSORS_FILE}")

    while True:
        for sensor in sensors:
            location_id = sensor.get("location_id")
            if not location_id:
                continue

            latest = fetch_latest_for_location(location_id)
            if latest is None:
                # Pas de données utilisables pour cette station à ce moment
                continue

            event = build_event(sensor, latest)
            send_to_n8n(event)

        print(f"Cycle terminé, pause de {POLL_INTERVAL_SECONDS} s...")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()