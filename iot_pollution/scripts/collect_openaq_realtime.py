# fichier: collect_openaq_realtime.py

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone

# -----------------------
# Configuration
# -----------------------

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

OPENAQ_BASE_URL = "https://api.openaq.org/v3"

OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY")
if not OPENAQ_API_KEY:
    raise RuntimeError("OPENAQ_API_KEY non définie dans .env")

SENSORS_FILE = ROOT_DIR / "iot_pollution" / "data" / "openaq_sensors_fr.json"

BRONZE_DIR = ROOT_DIR / "data" / "bronze_iot"
BRONZE_FILE = BRONZE_DIR / "bronze_iot_openaq.log"

CYCLE_SLEEP_SECONDS = 300  # 5 minutes

MIN_VALUE = 0.0
MAX_VALUE = 500.0

# -----------------------
# Logging
# -----------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# -----------------------
# Fonctions utilitaires
# -----------------------

def ensure_bronze_dir() -> None:
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)


def append_to_bronze_file(event: Dict[str, Any]) -> None:
    ensure_bronze_dir()
    with BRONZE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def load_sensors(file_path: Path) -> List[Dict[str, Any]]:
    with file_path.open("r", encoding="utf-8") as f:
        sensors = json.load(f)
    if not isinstance(sensors, list):
        raise ValueError("Le fichier JSON des capteurs doit contenir une liste")
    logging.info("%s capteurs chargés depuis %s", len(sensors), file_path)
    return sensors


def is_value_valid(value: float) -> bool:
    if value is None:
        return False
    return MIN_VALUE <= value <= MAX_VALUE


def build_headers() -> Dict[str, str]:
    return {
        "X-API-Key": OPENAQ_API_KEY,
        "Accept": "application/json",
    }


def fetch_latest_for_sensor(sensor: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    location_id = sensor.get("location_id") or sensor.get("id")
    if not location_id:
        logging.warning("Capteur sans location_id/id : %s", sensor)
        return None

    url = f"{OPENAQ_BASE_URL}/locations/{location_id}/latest"
    params = {"limit": 1, "page": 1}

    try:
        resp = requests.get(url, params=params, headers=build_headers(), timeout=10)
        logging.info(
            "Status latest (%s): %s %s",
            location_id,
            resp.status_code,
            resp.text[:200],
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logging.error(
            "Erreur lors de l'appel OpenAQ v3 pour le capteur %s : %s", sensor, e
        )
        return None

    results = data.get("results") or []
    if not results:
        return None

    latest = results[0]
    return latest


def build_event(sensor: Dict[str, Any], latest: Dict[str, Any]) -> Dict[str, Any]:
    datetime_info = latest.get("datetime") or {}
    coords = latest.get("coordinates") or {}
    parameter = latest.get("parameter") or {}

    event = {
        "sensor_id": sensor.get("location_id") or sensor.get("id"),
        "sensor_name": sensor.get("name") or latest.get("location"),
        "pollutant": (
            parameter.get("name")
            if isinstance(parameter, dict)
            else parameter
        ) or "unknown",
        "value": latest.get("value"),
        "unit": latest.get("unit"),
        "datetime_utc": datetime_info.get("utc"),
        "datetime_local": datetime_info.get("local"),
        "latitude": coords.get("latitude"),
        "longitude": coords.get("longitude"),
        "raw": {
            "sensor": sensor,
            "latest": latest,
        },
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }

    return event

# -----------------------
# Boucle principale
# -----------------------

def main():
    sensors = load_sensors(SENSORS_FILE)

    logging.info("%s capteurs chargés depuis %s", len(sensors), SENSORS_FILE)
    ensure_bronze_dir()

    while True:
        for sensor in sensors:
            sensor_id = str(
                sensor.get("location_id")
                or sensor.get("id")
                or sensor.get("name")
                or "unknown"
            )

            latest = fetch_latest_for_sensor(sensor)
            if not latest:
                logging.info(
                    "Aucune mesure exploitable pour capteur %s, on passe.", sensor_id
                )
                continue

            value = latest.get("value")
            if value is None or not is_value_valid(value):
                logging.info(
                    "Valeur invalide pour capteur %s : %s, ignorée.",
                    sensor_id,
                    value,
                )
                continue

            event = build_event(sensor, latest)
            append_to_bronze_file(event)
            logging.info(
                "Mesure écrite dans Bronze pour capteur %s (value=%s)",
                sensor_id,
                value,
            )

        logging.info("Cycle terminé, pause de %s s...", CYCLE_SLEEP_SECONDS)
        time.sleep(CYCLE_SLEEP_SECONDS)


if __name__ == "__main__":
    main()