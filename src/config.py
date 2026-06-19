"""
Configuration centralisée pour UrbanHub
"""
import json
from pathlib import Path
from typing import Dict, Any

# Répertoires
PROJECT_ROOT = Path(__file__).parent.parent
DATA_LAKE_ROOT = PROJECT_ROOT / "data" / "lake"
BRONZE_DIR = DATA_LAKE_ROOT / "bronze" / "weather" / "noaa"
SILVER_DIR = DATA_LAKE_ROOT / "silver" / "weather"
GOLD_DIR = DATA_LAKE_ROOT / "gold" / "weather"

# Créer les répertoires s'ils n'existent pas
for dir_path in [BRONZE_DIR, SILVER_DIR, GOLD_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Stations météo France - Codes NOAA réels (WMO IDs)
# Format: WMO_ID => (Ville, ICAO)
FRENCH_STATIONS = {
    '07015099999': ('Paris CDG', 'LFPG'),           # Paris
    '07149099999': ('Paris Orly', 'LFPO'),          # Paris
    '07480099999': ('Lyon', 'LFLY'),                # Lyon
    '07610099999': ('Toulouse', 'LFTH'),            # Toulouse
    '07650099999': ('Marseille', 'LFML'),           # Marseille
    '07761099999': ('Nice', 'LFMN'),                # Nice
    '07586099999': ('Strasbourg', 'LFST'),          # Strasbourg
    '07379099999': ('Nantes', 'LFRJ'),              # Nantes
}

# Période d'analyse
START_YEAR = 2020
END_YEAR = 2025
YEARS = list(range(START_YEAR, END_YEAR + 1))

# URL de base NOAA
NOAA_BASE_URL = "https://www.ncei.noaa.gov/data/global-hourly/access"

# Configuration de traitement
BATCH_SIZE = 100  # Nombre de lignes par batch
WORKERS = 4  # Nombre de workers pour téléchargement parallèle
RETRY_ATTEMPTS = 3
TIMEOUT = 30  # secondes

# Variables météo utilisées
WEATHER_VARIABLES = {
    'station_id': 'str',
    'timestamp': 'str',
    'temperature': 'float64',
    'wind_speed': 'float64',
    'wind_direction': 'float64',
    'pressure': 'float64',
    'precipitation': 'float64',
    'visibility': 'float64',
}

# Thresholds pour événements extrêmes
EXTREME_THRESHOLDS = {
    'heat_wave': 30.0,           # °C
    'cold_wave': 0.0,            # °C
    'strong_wind': 10.0,         # m/s
    'heavy_rain': 10.0,          # mm/jour
    'low_visibility': 1.0,       # km
}

# Saisonnalité (hémisphère Nord)
SEASONS = {
    'winter': [12, 1, 2],
    'spring': [3, 4, 5],
    'summer': [6, 7, 8],
    'autumn': [9, 10, 11],
}

def get_config() -> Dict[str, Any]:
    """Retourne la configuration"""
    return {
        'project_root': str(PROJECT_ROOT),
        'bronze_dir': str(BRONZE_DIR),
        'silver_dir': str(SILVER_DIR),
        'gold_dir': str(GOLD_DIR),
        'french_stations': FRENCH_STATIONS,
        'years': YEARS,
        'noaa_base_url': NOAA_BASE_URL,
        'batch_size': BATCH_SIZE,
        'workers': WORKERS,
        'retry_attempts': RETRY_ATTEMPTS,
        'timeout': TIMEOUT,
    }

if __name__ == "__main__":
    config = get_config()
    print(json.dumps(config, indent=2))
