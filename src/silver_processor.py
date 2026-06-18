"""
Nettoyage Bronze → Silver
- Filtre stations françaises
- Harmonise unités, timestamps
- Gère valeurs manquantes
- Partitionne par année/mois/ville
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional

from config import BRONZE_DIR, SILVER_DIR, WEATHER_VARIABLES, FRENCH_STATIONS
from utils import setup_logger, get_season

logger = setup_logger("silver_processor", "logs/silver_processor.log")

# Mapping des stations NOAA aux villes
# Codes: WMO_ID => Ville
STATION_TO_CITY = {
    '07015099999': 'Paris',
    '07149099999': 'Paris',
    '07480099999': 'Lyon',
    '07610099999': 'Toulouse',
    '07650099999': 'Marseille',
    '07761099999': 'Nice',
    '07586099999': 'Strasbourg',
    '07379099999': 'Nantes',
}

def parse_noaa_csv(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Parse un fichier CSV NOAA
    Exporte les variables requises avec nettoyage basique
    """
    try:
        df = pd.read_csv(file_path, sep=',', on_bad_lines='skip')
        
        # Renomme colonnes NOAA vers nos noms standards
        # NOAA utilise : TMP, WND, VIS, PCP, SLP, etc.
        column_mapping = {
            'STATION': 'station_id',
            'DATE': 'timestamp',
            'TMP': 'temperature',
            'WND': 'wind_speed',  # Format: ddd,dddSSS,c (direction, speed, quality)
            'VIS': 'visibility',   # Format: vvvvvvv,c (en décimètre)
            'PCP': 'precipitation', # Format: cc,ccccc,c (in, depth, quality)
            'SLP': 'pressure',     # Format: ppppp,c (en hPa × 10)
        }
        
        logger.debug(f"Colonnes trouvées: {df.columns.tolist()}")
        
        # Extrait et nettoie les colonnes de base
        data = pd.DataFrame()
        data['station_id'] = df.get('STATION', '')
        data['timestamp'] = df.get('DATE', '')
        
        # Traitement des variables (format NOAA complexe)
        if 'TMP' in df.columns:
            data['temperature'] = df['TMP'].apply(lambda x: parse_noaa_value(x, 'TMP'))
        if 'WND' in df.columns:
            data['wind_speed'] = df['WND'].apply(lambda x: parse_noaa_wind_speed(x))
            data['wind_direction'] = df['WND'].apply(lambda x: parse_noaa_wind_direction(x))
        if 'VIS' in df.columns:
            data['visibility'] = df['VIS'].apply(lambda x: parse_noaa_visibility(x))
        if 'PCP' in df.columns:
            data['precipitation'] = df['PCP'].apply(lambda x: parse_noaa_precipitation(x))
        if 'SLP' in df.columns:
            data['pressure'] = df['SLP'].apply(lambda x: parse_noaa_pressure(x))
        
        return data
        
    except Exception as e:
        logger.error(f"Erreur parsing {file_path.name}: {e}")
        return None

def parse_noaa_value(value_str: str, field_type: str) -> Optional[float]:
    """
    Parse une valeur NOAA au format texte
    Format: vvvvvc ou vvvvvvv,c
    v=valeur, c=qualité (0-9)
    """
    if pd.isna(value_str) or value_str == '':
        return None
    
    try:
        # Extrait la valeur avant la qualité
        if isinstance(value_str, str) and ',' in value_str:
            val = float(value_str.split(',')[0])
        else:
            val = float(str(value_str)[:5])
        
        # Conversion d'unité selon le type
        if field_type == 'TMP':
            # NOAA en 1/10 °C, convertir en °C
            return val / 10.0
        elif field_type == 'SLP':
            # NOAA en 1/10 hPa, convertir en hPa
            return val / 10.0
        
        return val
    except (ValueError, IndexError, TypeError):
        return None

def parse_noaa_wind_speed(wind_str: str) -> Optional[float]:
    """Extrait vitesse du vent (m/s)"""
    if pd.isna(wind_str) or wind_str == '':
        return None
    try:
        # Format: ddd,dddSSS,c (direction, speed en m/s × 10, qualité)
        parts = str(wind_str).split(',')
        if len(parts) >= 2:
            speed = float(parts[1][:3]) / 10.0  # m/s
            return speed if 0 <= speed <= 100 else None
    except (ValueError, IndexError):
        pass
    return None

def parse_noaa_wind_direction(wind_str: str) -> Optional[float]:
    """Extrait direction du vent (degrés 0-360)"""
    if pd.isna(wind_str) or wind_str == '':
        return None
    try:
        # Format: ddd,dddSSS,c (direction en degrés)
        parts = str(wind_str).split(',')
        if len(parts) >= 1:
            direction = float(parts[0])
            return direction if 0 <= direction <= 360 else None
    except (ValueError, IndexError):
        pass
    return None

def parse_noaa_visibility(vis_str: str) -> Optional[float]:
    """Extrait visibilité en km"""
    if pd.isna(vis_str) or vis_str == '':
        return None
    try:
        # Format: vvvvvvv,c (en décimètres)
        parts = str(vis_str).split(',')
        if len(parts) >= 1:
            vis_dm = float(parts[0])
            # Décimètres → Km
            vis_km = vis_dm / 100.0
            return vis_km if vis_km >= 0 else None
    except (ValueError, IndexError):
        pass
    return None

def parse_noaa_precipitation(precip_str: str) -> Optional[float]:
    """Extrait précipitations en mm"""
    if pd.isna(precip_str) or precip_str == '':
        return None
    try:
        # Format: cc,ccccc,c (en 1/100 pouces, convertir en mm)
        parts = str(precip_str).split(',')
        if len(parts) >= 2:
            precip_hundredth_inch = float(parts[1][:5]) / 100.0
            # Pouces → mm (1 pouce = 25.4 mm)
            precip_mm = precip_hundredth_inch * 25.4
            return precip_mm if precip_mm >= 0 else None
    except (ValueError, IndexError):
        pass
    return None

def parse_noaa_pressure(slp_str: str) -> Optional[float]:
    """Extrait pression en hPa"""
    return parse_noaa_value(slp_str, 'SLP')

def normalize_timestamp(timestamp_str: str) -> Optional[str]:
    """Normalise timestamp NOAA en ISO 8601 UTC"""
    try:
        # Format NOAA: YYYY-MM-DDTHH:MM:SS
        dt = datetime.fromisoformat(timestamp_str.split('+')[0])
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    except (ValueError, TypeError, AttributeError):
        return None

def clean_and_enrich(df: pd.DataFrame, station_id: str) -> pd.DataFrame:
    """
    Nettoyage et enrichissement :
    - Filtre stations françaises
    - Normalise timestamps
    - Gère valeurs manquantes
    - Ajoute localisation
    """
    if df.empty:
        return df
    
    # Filtre stations françaises
    if station_id not in FRENCH_STATIONS:
        logger.warning(f"Station non française: {station_id}")
        return pd.DataFrame()
    
    # Normalise timestamps
    df['timestamp'] = df['timestamp'].apply(normalize_timestamp)
    df = df[df['timestamp'].notna()]
    
    # Enrichissement localisation
    df['city'] = STATION_TO_CITY.get(station_id, 'Unknown')
    df['station_id'] = station_id
    
    # Ajoute saison et date
    df['datetime'] = pd.to_datetime(df['timestamp'])
    df['year'] = df['datetime'].dt.year
    df['month'] = df['datetime'].dt.month
    df['day'] = df['datetime'].dt.day
    df['hour'] = df['datetime'].dt.hour
    df['season'] = df['month'].apply(get_season)
    
    # Stats valeurs manquantes
    missing = df[['temperature', 'wind_speed', 'pressure', 'precipitation', 'visibility']].isna().sum()
    logger.info(f"{station_id}: Valeurs manquantes: temp={missing['temperature']}, "
                f"wind={missing['wind_speed']}, pressure={missing['pressure']}")
    
    # Imputation simple (forward fill puis valeur médiane par station/mois)
    numeric_cols = ['temperature', 'wind_speed', 'wind_direction', 'pressure', 'precipitation', 'visibility']
    df[numeric_cols] = df[numeric_cols].fillna(method='ffill').fillna(df[numeric_cols].median())
    
    return df

def save_as_parquet(df: pd.DataFrame, year: int, month: int, city: str):
    """Sauvegarde en Parquet partitionné"""
    if df.empty:
        return
    
    output_dir = SILVER_DIR / f"year={year}" / f"month={month:02d}" / f"city={city}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"weather_data_{year}_{month:02d}_{city}.parquet"
    
    # Colonnes à garder
    cols_to_keep = ['station_id', 'timestamp', 'temperature', 'wind_speed', 
                    'wind_direction', 'pressure', 'precipitation', 'visibility',
                    'city', 'year', 'month', 'day', 'hour', 'season']
    
    df_save = df[[c for c in cols_to_keep if c in df.columns]]
    
    df_save.to_parquet(output_file, index=False, compression='snappy')
    logger.info(f"✓ Sauvegardé: {output_file.relative_to(SILVER_DIR)} ({len(df)} enregistrements)")

def process_bronze_to_silver():
    """
    Pipeline complet Bronze → Silver
    """
    logger.info("=" * 60)
    logger.info("Traitement Bronze → Silver (nettoyage)")
    logger.info("=" * 60)
    
    bronze_files = list(BRONZE_DIR.glob("**/*.csv"))
    logger.info(f"Fichiers trouvés: {len(bronze_files)}")
    
    if not bronze_files:
        logger.warning("Aucun fichier Bronze trouvé. Lancez downloader.py d'abord.")
        return
    
    total_records = 0
    
    for i, file_path in enumerate(bronze_files, 1):
        logger.debug(f"[{i}/{len(bronze_files)}] Traitement {file_path.name}...")
        
        # Parse
        df = parse_noaa_csv(file_path)
        if df is None or df.empty:
            continue
        
        # Extrait station depuis le chemin
        station_id = file_path.parent.name.split('=')[1]
        
        # Nettoyage
        df = clean_and_enrich(df, station_id)
        if df.empty:
            continue
        
        # Partitionne par année/mois/ville et sauvegarde
        for (year, month, city), group in df.groupby(['year', 'month', 'city']):
            save_as_parquet(group, year, month, city)
            total_records += len(group)
    
    logger.info("\n" + "=" * 60)
    logger.info(f"✓ Pipeline Silver terminé")
    logger.info(f"  Enregistrements traités: {total_records:,}")
    logger.info(f"  Destination: {SILVER_DIR}")
    logger.info("=" * 60)

if __name__ == "__main__":
    process_bronze_to_silver()
