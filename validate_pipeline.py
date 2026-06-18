"""
Script de validation du pipeline
Vérifie que toutes les étapes se sont déroulées correctement
"""
import pandas as pd
from pathlib import Path
import json

def validate_pipeline():
    """Valide la complétude du pipeline"""
    
    print("=" * 70)
    print("VALIDATION PIPELINE URBANHUB")
    print("=" * 70)
    
    checks = {}
    
    # 1. Check Bronze (fichiers CSV)
    print("\n[1/5] Vérification Bronze...")
    bronze_dir = Path("data/lake/bronze/weather/noaa")
    if bronze_dir.exists():
        csv_files = list(bronze_dir.glob("**/*.csv"))
        checks['bronze_files'] = len(csv_files)
        print(f"  ✓ Fichiers Bronze: {len(csv_files)}")
    else:
        checks['bronze_files'] = 0
        print(f"  ⚠️  Répertoire Bronze non trouvé")
    
    # 2. Check Silver (fichiers Parquet)
    print("\n[2/5] Vérification Silver...")
    silver_dir = Path("data/lake/silver/weather")
    if silver_dir.exists():
        parquet_files = list(silver_dir.glob("**/*.parquet"))
        checks['silver_files'] = len(parquet_files)
        print(f"  ✓ Fichiers Silver: {len(parquet_files)}")
        
        if parquet_files:
            # Check contenu d'un fichier
            try:
                df = pd.read_parquet(parquet_files[0])
                checks['silver_records'] = len(df)
                checks['silver_columns'] = list(df.columns)
                print(f"  ✓ Premier fichier: {len(df)} enregistrements")
                print(f"  ✓ Colonnes: {', '.join(df.columns.tolist())}")
            except Exception as e:
                print(f"  ✗ Erreur lecture Parquet: {e}")
    else:
        checks['silver_files'] = 0
        print(f"  ⚠️  Répertoire Silver non trouvé")
    
    # 3. Check Gold (tables)
    print("\n[3/5] Vérification Gold...")
    gold_dir = Path("data/lake/gold/weather")
    if gold_dir.exists():
        # Weather daily
        daily_file = gold_dir / "weather_daily.parquet"
        if daily_file.exists():
            df = pd.read_parquet(daily_file)
            checks['gold_daily_records'] = len(df)
            checks['gold_daily_cities'] = df['city'].nunique()
            print(f"  ✓ weather_daily.parquet: {len(df)} lignes, {df['city'].nunique()} villes")
        
        # Weather extreme
        extreme_file = gold_dir / "weather_extreme_days.parquet"
        if extreme_file.exists():
            df = pd.read_parquet(extreme_file)
            checks['gold_extreme_events'] = len(df)
            event_types = df['event_type'].unique()
            checks['gold_event_types'] = list(event_types)
            print(f"  ✓ weather_extreme_days.parquet: {len(df)} événements")
            print(f"    Types: {', '.join(event_types)}")
        
        # Correlations
        corr_file = gold_dir / "weather_correlations.csv"
        if corr_file.exists():
            df = pd.read_csv(corr_file)
            checks['gold_correlations'] = len(df)
            print(f"  ✓ weather_correlations.csv: {len(df)} paires")
    else:
        print(f"  ⚠️  Répertoire Gold non trouvé")
    
    # 4. Check Visualizations
    print("\n[4/5] Vérification Visualizations...")
    viz_dir = gold_dir / "visualizations" if gold_dir.exists() else None
    if viz_dir and viz_dir.exists():
        png_files = list(viz_dir.glob("*.png"))
        checks['visualizations'] = len(png_files)
        print(f"  ✓ Graphiques PNG: {len(png_files)}")
        for png in png_files:
            print(f"    - {png.name}")
    else:
        print(f"  ⚠️  Répertoire Visualizations non trouvé")
    
    # 5. Check Config
    print("\n[5/5] Vérification Configuration...")
    config_file = Path("config/datalake_config.json")
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
        checks['config_stations'] = len(config['stations'])
        checks['config_version'] = config['datalake']['version']
        print(f"  ✓ Configuration trouvée")
        print(f"    Stations: {checks['config_stations']}")
        print(f"    Version: {checks['config_version']}")
    
    # Résumé
    print("\n" + "=" * 70)
    print("RÉSUMÉ VALIDATION")
    print("=" * 70)
    
    total_checks = 5
    passed_checks = 0
    
    if checks.get('bronze_files', 0) > 0:
        print("✓ Bronze: OK")
        passed_checks += 1
    else:
        print("✗ Bronze: MANQUANT")
    
    if checks.get('silver_files', 0) > 0:
        print("✓ Silver: OK")
        passed_checks += 1
    else:
        print("✗ Silver: MANQUANT")
    
    if checks.get('gold_daily_records', 0) > 0:
        print("✓ Gold: OK")
        passed_checks += 1
    else:
        print("✗ Gold: MANQUANT")
    
    if checks.get('visualizations', 0) > 0:
        print("✓ Visualizations: OK")
        passed_checks += 1
    else:
        print("⚠️  Visualizations: MANQUANTES (optionnel)")
    
    if checks.get('config_stations', 0) > 0:
        print("✓ Configuration: OK")
        passed_checks += 1
    else:
        print("✗ Configuration: MANQUANTE")
    
    print("\n" + "=" * 70)
    if passed_checks >= 3:
        print(f"✅ VALIDATION RÉUSSIE ({passed_checks}/{total_checks} couches)")
    else:
        print(f"❌ VALIDATION ÉCHOUÉE ({passed_checks}/{total_checks} couches)")
    
    print("=" * 70)
    
    # Affiche statistiques détaillées
    print("\nSTATISTIQUES DÉTAILLÉES:")
    for key, value in sorted(checks.items()):
        if isinstance(value, (int, str)):
            print(f"  {key}: {value}")
    
    return passed_checks >= 3

if __name__ == "__main__":
    success = validate_pipeline()
    exit(0 if success else 1)
