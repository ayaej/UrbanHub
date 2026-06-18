"""
Agrégation Silver → Gold
- Agrégation quotidienne (min, max, moyenne)
- Détection jours extrêmes
- Calcul de corrélations
- Tables d'indicateurs
"""
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Tuple
from datetime import datetime

from config import SILVER_DIR, GOLD_DIR, EXTREME_THRESHOLDS
from utils import setup_logger

logger = setup_logger("gold_aggregator", "logs/gold_aggregator.log")

def load_silver_data() -> pd.DataFrame:
    """Charge toutes les données Silver"""
    logger.info("Chargement données Silver...")
    
    parquet_files = list(SILVER_DIR.glob("**/*.parquet"))
    if not parquet_files:
        logger.warning("Aucun fichier Silver trouvé")
        return pd.DataFrame()
    
    dfs = []
    for pf in parquet_files:
        try:
            df = pd.read_parquet(pf)
            dfs.append(df)
        except Exception as e:
            logger.error(f"Erreur lecture {pf}: {e}")
    
    if dfs:
        result = pd.concat(dfs, ignore_index=True)
        logger.info(f"Chargé {len(result):,} enregistrements")
        return result
    return pd.DataFrame()

def aggregate_daily(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrégation quotidienne par ville
    Calcule: min, max, moyenne de température, vent moyen, etc.
    """
    if df.empty:
        return df
    
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    
    agg_dict = {
        'temperature': ['min', 'max', 'mean'],
        'wind_speed': ['max', 'mean'],
        'wind_direction': ['mean'],
        'pressure': ['mean'],
        'precipitation': ['sum'],
        'visibility': ['min', 'mean'],
    }
    
    daily = df.groupby(['date', 'city']).agg(agg_dict)
    daily.columns = ['_'.join(col).strip() for col in daily.columns.values]
    daily = daily.reset_index()
    
    # Ajoute saison
    daily['datetime'] = pd.to_datetime(daily['date'])
    daily['season'] = daily['datetime'].dt.month.apply(
        lambda m: 'winter' if m in [12,1,2] else 
                  'spring' if m in [3,4,5] else 
                  'summer' if m in [6,7,8] else 'autumn'
    )
    
    logger.info(f"Agrégation quotidienne: {len(daily)} jours-villes")
    return daily

def detect_extreme_days(daily_df: pd.DataFrame) -> pd.DataFrame:
    """
    Détecte les jours extrêmes selon les seuils
    Retourne table avec: date, city, event_type
    """
    extreme_records = []
    
    for idx, row in daily_df.iterrows():
        events = []
        
        # Canicule
        if row.get('temperature_max') and row['temperature_max'] >= EXTREME_THRESHOLDS['heat_wave']:
            events.append('heat_wave')
        
        # Vague de froid
        if row.get('temperature_min') and row['temperature_min'] <= EXTREME_THRESHOLDS['cold_wave']:
            events.append('cold_wave')
        
        # Vents forts
        if row.get('wind_speed_max') and row['wind_speed_max'] >= EXTREME_THRESHOLDS['strong_wind']:
            events.append('strong_wind')
        
        # Fortes pluies
        if row.get('precipitation_sum') and row['precipitation_sum'] >= EXTREME_THRESHOLDS['heavy_rain']:
            events.append('heavy_rain')
        
        # Faible visibilité
        if row.get('visibility_min') and row['visibility_min'] <= EXTREME_THRESHOLDS['low_visibility']:
            events.append('low_visibility')
        
        for event in events:
            extreme_records.append({
                'date': row['date'],
                'city': row['city'],
                'event_type': event,
                'temperature_max': row.get('temperature_max'),
                'wind_speed_max': row.get('wind_speed_max'),
                'precipitation_sum': row.get('precipitation_sum'),
                'visibility_min': row.get('visibility_min'),
            })
    
    extreme_df = pd.DataFrame(extreme_records)
    logger.info(f"Détecté {len(extreme_df)} événements extrêmes")
    return extreme_df

def compute_correlations(df: pd.DataFrame) -> Dict[str, Dict]:
    """
    Calcule corrélations entre variables par saison/ville
    Intérêt: lien météo ↔ visibilité
    """
    correlations = {}
    
    # Par saison globalement
    for season in ['winter', 'spring', 'summer', 'autumn']:
        season_data = df[df['season'] == season]
        if len(season_data) > 10:
            # Corrélation température/visibilité
            corr = season_data[['temperature_mean', 'visibility_mean']].corr()
            correlations[f"{season}_temp_vis"] = corr.iloc[0, 1]
            
            # Corrélation pluie/visibilité
            corr = season_data[['precipitation_sum', 'visibility_mean']].corr()
            correlations[f"{season}_precip_vis"] = corr.iloc[0, 1]
    
    logger.info(f"Corrélations calculées: {len(correlations)} paires")
    return correlations

def save_gold_tables(daily_df: pd.DataFrame, extreme_df: pd.DataFrame, correlations: Dict):
    """Sauvegarde les tables Gold"""
    
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Table quotidienne
    daily_file = GOLD_DIR / "weather_daily.parquet"
    daily_df.to_parquet(daily_file, index=False, compression='snappy')
    logger.info(f"✓ Table quotidienne: {daily_file} ({len(daily_df)} lignes)")
    
    # 2. Jours extrêmes
    extreme_file = GOLD_DIR / "weather_extreme_days.parquet"
    extreme_df.to_parquet(extreme_file, index=False, compression='snappy')
    logger.info(f"✓ Jours extrêmes: {extreme_file} ({len(extreme_df)} événements)")
    
    # 3. Corrélations (CSV)
    corr_file = GOLD_DIR / "weather_correlations.csv"
    corr_df = pd.DataFrame(list(correlations.items()), columns=['pair', 'correlation'])
    corr_df.to_csv(corr_file, index=False)
    logger.info(f"✓ Corrélations: {corr_file}")
    
    # 4. Résumé par ville (statistiques annuelles)
    annual_summary = daily_df.groupby('city').agg({
        'temperature_mean': ['min', 'max', 'mean'],
        'precipitation_sum': 'sum',
        'wind_speed_max': 'mean',
    })
    summary_file = GOLD_DIR / "city_summary_annual.csv"
    annual_summary.to_csv(summary_file)
    logger.info(f"✓ Résumé annuel: {summary_file}")

def generate_gold():
    """Pipeline complet Silver → Gold"""
    logger.info("=" * 60)
    logger.info("Agrégation Silver → Gold (indicateurs)")
    logger.info("=" * 60)
    
    # Charge Silver
    df = load_silver_data()
    if df.empty:
        logger.error("Impossible de charger les données Silver")
        return
    
    # Étape 1: Agrégation quotidienne
    daily = aggregate_daily(df)
    
    # Étape 2: Détection jours extrêmes
    extreme = detect_extreme_days(daily)
    
    # Étape 3: Corrélations
    corr = compute_correlations(daily)
    
    # Étape 4: Sauvegarde
    save_gold_tables(daily, extreme, corr)
    
    logger.info("\n" + "=" * 60)
    logger.info(f"✓ Pipeline Gold terminé")
    logger.info(f"  Jours analysés: {len(daily)}")
    logger.info(f"  Événements extrêmes: {len(extreme)}")
    logger.info(f"  Destination: {GOLD_DIR}")
    logger.info("=" * 60)
    
    # Affiche top événements
    if not extreme.empty:
        logger.info("\nTop 10 événements extrêmes:")
        event_counts = extreme['event_type'].value_counts().head(10)
        for event, count in event_counts.items():
            logger.info(f"  {event}: {count} occurrences")

if __name__ == "__main__":
    generate_gold()
