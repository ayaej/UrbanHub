"""
Génération de visualisations pour les résultats Gold
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging

from config import GOLD_DIR
from utils import setup_logger

logger = setup_logger("visualizer", "logs/visualizer.log")

def plot_seasonal_temperature(daily_df: pd.DataFrame, output_dir: Path):
    """Courbes saisonnières de température"""
    plt.figure(figsize=(14, 6))
    
    for season in ['winter', 'spring', 'summer', 'autumn']:
        season_data = daily_df[daily_df['season'] == season]
        if not season_data.empty:
            plt.plot(season_data['date'], season_data['temperature_mean'], 
                    label=season, marker='o', markersize=3, alpha=0.7)
    
    plt.xlabel('Date')
    plt.ylabel('Température moyenne (°C)')
    plt.title('Évolution saisonnière de la température')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    output_file = output_dir / "seasonal_temperature.png"
    plt.savefig(output_file, dpi=150)
    logger.info(f"✓ Graphique sauvegardé: {output_file}")
    plt.close()

def plot_extreme_events(extreme_df: pd.DataFrame, output_dir: Path):
    """Distribution des événements extrêmes"""
    plt.figure(figsize=(10, 6))
    
    event_counts = extreme_df['event_type'].value_counts()
    event_counts.plot(kind='barh', color='coral')
    
    plt.xlabel('Nombre d\'occurrences')
    plt.title('Distribution des événements météorologiques extrêmes')
    plt.tight_layout()
    
    output_file = output_dir / "extreme_events_distribution.png"
    plt.savefig(output_file, dpi=150)
    logger.info(f"✓ Graphique sauvegardé: {output_file}")
    plt.close()

def plot_precipitation_heatmap(daily_df: pd.DataFrame, output_dir: Path):
    """Heatmap précipitations par ville"""
    plt.figure(figsize=(12, 6))
    
    # Pivot pour avoir villes × mois
    daily_df['month'] = pd.to_datetime(daily_df['date']).dt.month
    precip_pivot = daily_df.groupby(['city', 'month'])['precipitation_sum'].mean().unstack()
    
    sns.heatmap(precip_pivot, annot=True, fmt='.1f', cmap='Blues', cbar_kws={'label': 'Précipitations (mm)'})
    plt.title('Précipitations moyennes mensuelles par ville')
    plt.xlabel('Mois')
    plt.ylabel('Ville')
    plt.tight_layout()
    
    output_file = output_dir / "precipitation_heatmap.png"
    plt.savefig(output_file, dpi=150)
    logger.info(f"✓ Graphique sauvegardé: {output_file}")
    plt.close()

def generate_visualizations():
    """Génère toutes les visualisations"""
    logger.info("=" * 60)
    logger.info("Génération des visualisations")
    logger.info("=" * 60)
    
    output_dir = GOLD_DIR / "visualizations"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Charge données Gold
    daily_file = GOLD_DIR / "weather_daily.parquet"
    extreme_file = GOLD_DIR / "weather_extreme_days.parquet"
    
    if not daily_file.exists():
        logger.error("Fichier weather_daily.parquet non trouvé. Lancez gold_aggregator.py d'abord.")
        return
    
    try:
        daily_df = pd.read_parquet(daily_file)
        extreme_df = pd.read_parquet(extreme_file)
        
        # Génère graphiques
        plot_seasonal_temperature(daily_df, output_dir)
        plot_extreme_events(extreme_df, output_dir)
        plot_precipitation_heatmap(daily_df, output_dir)
        
        logger.info(f"\n✓ Visualisations sauvegardées dans {output_dir}")
        
    except Exception as e:
        logger.error(f"Erreur génération visualisations: {e}")

if __name__ == "__main__":
    generate_visualizations()
