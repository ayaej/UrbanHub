import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# ----- Config & .env -----

# Racine du projet : D:\Cours\5ème Année IPSSI - Paris\UrbanHub
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
LIMIT = 50  # à ajuster si besoin
OUTPUT_PATH = ROOT_DIR / "iot_pollution" / "data" / "openaq_sensors_fr.json"


# ----- Fonctions API -----

def get_country_id(iso_code: str) -> int:
    """
    Récupère l'ID numérique d’un pays à partir de son code ISO (ex: 'FR').
    Utilise l’endpoint /v3/countries d’OpenAQ. [web:198][web:200]
    """
    params = {"limit": 300}
    resp = requests.get(COUNTRIES_URL, params=params, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    for c in data.get("results", []):
        if c.get("code") == iso_code:
            return c["id"]
    raise RuntimeError(f"Pays {iso_code} introuvable dans /v3/countries")


def fetch_locations(country_id: int):
    """
    Récupère les locations pour un pays donné (ID numérique).
    Utilise /v3/locations avec le paramètre countries_id attendu par l’API. [web:198]
    """
    params = {
        "countries_id": country_id,
        "limit": LIMIT,
        "page": 1,
    }
    resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=20)
    print("Status locations:", resp.status_code, resp.text[:200])
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", [])


# ----- Transformation / Sauvegarde -----

def transform_locations_to_sensors(locations: list) -> list:
    """
    Exemple de transformation : adapte selon la structure que tu veux.
    On extrait quelques champs clés de chaque location. [web:201]
    """
    sensors = []
    for loc in locations:
        # Les champs exacts dépendent du schéma OpenAQ v3, typiquement :
        # id, name, coordinates, country, etc. [web:201]
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


def save_sensors_to_file(sensors: list, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(sensors, f, ensure_ascii=False, indent=2)
    print(f"{len(sensors)} capteurs sauvegardés dans {path}")


# ----- main -----

def main():
    # 1. Récupérer l’ID du pays (France)
    country_id = get_country_id(COUNTRY_ISO)
    print(f"ID de {COUNTRY_ISO} = {country_id}")

    # 2. Récupérer les locations pour ce pays
    locations = fetch_locations(country_id)
    print(f"Nombre de locations récupérées : {len(locations)}")

    # 3. Transformer en objets capteurs
    sensors = transform_locations_to_sensors(locations)

    # 4. Sauvegarder dans un fichier JSON
    save_sensors_to_file(sensors, OUTPUT_PATH)


if __name__ == "__main__":
    main()