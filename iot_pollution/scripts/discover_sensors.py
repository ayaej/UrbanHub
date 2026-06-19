import json
import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# ----- Config & .env -----

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

BASE_URL = "https://api.openaq.org/v3/locations"
COUNTRIES_URL = "https://api.openaq.org/v3/countries"

API_KEY = os.getenv("OPENAQ_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENAQ_API_KEY non définie (voir fichier .env)")

HEADERS = {
    "X-API-Key": API_KEY,
    "Accept": "application/json",
}

COUNTRY_ISO = "FR"
PAGE_SIZE = 100
OUTPUT_PATH = ROOT_DIR / "iot_pollution" / "data" / "openaq_sensors_fr.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


# ----- Fonctions API -----

def get_country_id(iso_code: str) -> int:
    params = {"limit": 300}
    resp = requests.get(COUNTRIES_URL, params=params, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    for c in data.get("results", []):
        if c.get("code") == iso_code:
            logging.info("Pays %s trouvé : id=%s", iso_code, c["id"])
            return c["id"]
    raise RuntimeError(f"Pays {iso_code} introuvable dans /v3/countries")


def fetch_all_locations(country_id: int) -> list:
    """Récupère TOUTES les locations en paginant jusqu'à épuisement des résultats."""
    all_locations = []
    page = 1

    while True:
        params = {
            "countries_id": country_id,
            "limit": PAGE_SIZE,
            "page": page,
        }
        resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if not results:
            break

        all_locations.extend(results)
        logging.info(
            "Page %d : %d locations récupérées (total: %d)",
            page, len(results), len(all_locations),
        )

        if len(results) < PAGE_SIZE:
            break

        page += 1

    return all_locations


# ----- Transformation / Sauvegarde -----

def transform_locations_to_sensors(locations: list) -> list:
    sensors = []
    for loc in locations:
        sensor = {
            "location_id": loc.get("id"),
            "name": loc.get("name"),
            "country": loc.get("country"),
            "city": loc.get("city"),
            "coordinates": loc.get("coordinates"),
            "provider": loc.get("provider"),
            "parameters": loc.get("parameters"),
        }
        sensors.append(sensor)
    return sensors


def save_sensors_to_file(sensors: list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(sensors, f, ensure_ascii=False, indent=2)
    logging.info("%d capteurs sauvegardés dans %s", len(sensors), path)


# ----- main -----

def main():
    country_id = get_country_id(COUNTRY_ISO)
    locations = fetch_all_locations(country_id)
    logging.info("Total locations récupérées pour %s : %d", COUNTRY_ISO, len(locations))
    sensors = transform_locations_to_sensors(locations)
    save_sensors_to_file(sensors, OUTPUT_PATH)


if __name__ == "__main__":
    main()
