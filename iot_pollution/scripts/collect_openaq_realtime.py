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

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_IOT")
if not N8N_WEBHOOK_URL:
    raise RuntimeError("N8N_WEBHOOK_IOT non définie dans .env")

SENSORS_FILE = ROOT_DIR / "iot_pollution" / "data" / "openaq_sensors_fr.json"
STATE_FILE = ROOT_DIR / "iot_pollution" / "data" / "openaq_last_state.json"

CYCLE_SLEEP_SECONDS = 300  # 5 minutes

MIN_VALUE = 0.0
MAX_VALUE = 500.0
MIN_DELTA_VALUE = 0.1  # actuellement non utilisé, mais gardé si tu veux le réactiver plus tard

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

def load_sensors(file_path: Path) -> List[Dict[str, Any]]:
    with file_path.open("r", encoding="utf-8") as f:
        sensors = json.load(f)
    if not isinstance(sensors, list):
        raise ValueError("Le fichier JSON des capteurs doit contenir une liste")
    logging.info("%s capteurs chargés depuis %s", len(sensors), file_path)
    return sensors


def load_state(file_path: Path) -> Dict[str, Any]:
    if not file_path.exists():
        return {}
    try:
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logging.warning("Impossible de charger le fichier d'état, réinitialisation.")
        return {}


def save_state(file_path: Path, state: Dict[str, Any]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


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
    """
    Appelle l'endpoint v3 /locations/{location_id}/latest pour un capteur.
    """
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
    """
    Construit l'événement final (plat) qui sera écrit en JSONL par n8n.
    """
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


def trigger_n8n(event: Dict[str, Any]) -> bool:
    try:
        resp = requests.post(N8N_WEBHOOK_URL, json=event, timeout=10)
        logging.info("Status n8n: %s %s", resp.status_code, resp.text[:200])
        resp.raise_for_status()
        return True
    except Exception as e:
        logging.error("Erreur lors de l'appel n8n : %s", e)
        return False


def should_send(sensor_id: str, latest: Dict[str, Any], state: Dict[str, Any]) -> bool:
    """
    Version permissive : on filtre uniquement les valeurs nulles ou hors-bornes.
    Tu pourras réintroduire la logique de date/delta plus tard si besoin.
    """
    value = latest.get("value")

    if value is None or not is_value_valid(value):
        logging.info("Valeur invalide pour capteur %s : %s, ignorée.", sensor_id, value)
        return False

    return True

# -----------------------
# Boucle principale
# -----------------------

def main():
    sensors = load_sensors(SENSORS_FILE)
    state = load_state(STATE_FILE)

    logging.info("%s capteurs chargés depuis %s", len(sensors), SENSORS_FILE)

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

            if not should_send(sensor_id, latest, state):
                logging.info(
                    "Mesure non envoyée à n8n pour capteur %s (value=%s)",
                    sensor_id,
                    latest.get("value"),
                )
                continue

            event = build_event(sensor, latest)
            sent = trigger_n8n(event)
            if sent:
                utc = (latest.get("datetime") or {}).get("utc")
                logging.info(
                    "Mesure envoyée à n8n pour capteur %s (value=%s, utc=%s)",
                    sensor_id,
                    latest.get("value"),
                    utc,
                )
                # Tu peux garder un état si tu veux, même si should_send ne l'utilise plus pour l'instant
                state[sensor_id] = {
                    "utc": utc,
                    "value": latest.get("value"),
                }
                save_state(STATE_FILE, state)

        logging.info("Cycle terminé, pause de %s s...", CYCLE_SLEEP_SECONDS)
        time.sleep(CYCLE_SLEEP_SECONDS)


if __name__ == "__main__":
    main()