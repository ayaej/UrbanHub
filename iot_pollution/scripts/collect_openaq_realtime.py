import json
import os
import signal
import sys
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

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

# Unités standardisées par polluant (3.3 – uniformisation des unités)
UNIT_MAP: Dict[str, str] = {
    "pm25": "µg/m³",
    "pm10": "µg/m³",
    "no2":  "µg/m³",
    "o3":   "µg/m³",
    "co":   "mg/m³",
    "so2":  "µg/m³",
}

# -----------------------
# Logging
# -----------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# -----------------------
# Graceful shutdown
# -----------------------

_running = True


def _handle_stop(sig, frame):  # noqa: ANN001
    global _running
    logging.info("Signal %s reçu – arrêt gracieux en cours...", sig)
    _running = False


signal.signal(signal.SIGTERM, _handle_stop)
signal.signal(signal.SIGINT, _handle_stop)

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
    logging.info("%d capteurs chargés depuis %s", len(sensors), file_path)
    return sensors


def is_value_valid(value: float) -> bool:
    if value is None:
        return False
    return MIN_VALUE <= value <= MAX_VALUE


def normalize_unit(pollutant: str, raw_unit: Optional[str]) -> str:
    """Retourne l'unité standardisée pour le polluant, ou conserve l'unité brute."""
    return UNIT_MAP.get(pollutant.lower(), raw_unit or "unknown")


def build_headers() -> Dict[str, str]:
    return {
        "X-API-Key": OPENAQ_API_KEY,
        "Accept": "application/json",
    }


def fetch_latest_for_sensor(sensor: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    location_id = sensor.get("location_id") or sensor.get("id")
    if not location_id:
        logging.warning("Capteur sans location_id/id : %s", sensor.get("name"))
        return None

    url = f"{OPENAQ_BASE_URL}/locations/{location_id}/latest"

    try:
        resp = requests.get(url, headers=build_headers(), timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logging.error("Erreur OpenAQ pour capteur %s : %s", location_id, e)
        return None

    results = data.get("results") or []
    if not results:
        return None

    return results[0]


def build_event(sensor: Dict[str, Any], latest: Dict[str, Any]) -> Dict[str, Any]:
    datetime_info = latest.get("datetime") or {}
    coords = latest.get("coordinates") or {}
    parameter = latest.get("parameter") or {}

    pollutant = (
        parameter.get("name") if isinstance(parameter, dict) else parameter
    ) or "unknown"

    raw_unit = latest.get("unit")
    unit = normalize_unit(pollutant, raw_unit)

    # sensor_id stable : location_id + polluant
    location_id = sensor.get("location_id") or sensor.get("id")
    sensor_id = f"{location_id}_{pollutant}" if location_id else "unknown"

    return {
        "sensor_id": sensor_id,
        "location_id": location_id,
        "sensor_name": sensor.get("name") or latest.get("location"),
        "city": sensor.get("city"),
        "latitude": coords.get("latitude"),
        "longitude": coords.get("longitude"),
        "pollutant": pollutant,
        "value": latest.get("value"),
        "unit": unit,
        "datetime_utc": datetime_info.get("utc"),
        "datetime_local": datetime_info.get("local"),
        "source": "OpenAQ",
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }


# -----------------------
# Boucle principale
# -----------------------

def main():
    sensors = load_sensors(SENSORS_FILE)
    ensure_bronze_dir()

    cycle = 0
    total_messages = 0
    total_bytes = 0

    while _running:
        cycle += 1
        cycle_messages = 0
        cycle_start = datetime.now(timezone.utc)

        for sensor in sensors:
            if not _running:
                break

            location_id = sensor.get("location_id") or sensor.get("id") or "unknown"

            latest = fetch_latest_for_sensor(sensor)
            if not latest:
                logging.debug("Aucune mesure pour capteur %s", location_id)
                continue

            value = latest.get("value")
            if value is None or not is_value_valid(value):
                logging.debug("Valeur invalide pour capteur %s : %s", location_id, value)
                continue

            event = build_event(sensor, latest)
            line = json.dumps(event, ensure_ascii=False) + "\n"
            append_to_bronze_file(event)

            cycle_messages += 1
            total_messages += 1
            total_bytes += len(line.encode("utf-8"))

        elapsed = (datetime.now(timezone.utc) - cycle_start).total_seconds()

        # Stats de volume (3.2 – documentation)
        logging.info(
            "Cycle %d terminé : %d messages en %.1fs | "
            "Total cumulé : %d messages, %.1f Ko",
            cycle, cycle_messages, elapsed,
            total_messages, total_bytes / 1024,
        )

        if _running:
            time.sleep(CYCLE_SLEEP_SECONDS)

    logging.info(
        "Arrêt propre – %d cycles, %d messages, %.1f Ko écrits dans Bronze.",
        cycle, total_messages, total_bytes / 1024,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
