"""
Setup initial du Data Lake
Crée les répertoires et fichiers de configuration
"""
import json
from pathlib import Path
from config import BRONZE_DIR, SILVER_DIR, GOLD_DIR, FRENCH_STATIONS, YEARS

def setup_datalake():
    """Initialise la structure du Data Lake"""
    
    # Crée les répertoires principaux
    for dir_path in [BRONZE_DIR, SILVER_DIR, GOLD_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Créé: {dir_path}")
    
    # Crée un fichier de configuration
    config = {
        'datalake': {
            'bronze': str(BRONZE_DIR),
            'silver': str(SILVER_DIR),
            'gold': str(GOLD_DIR),
        },
        'metadata': {
            'stations': FRENCH_STATIONS,
            'years': YEARS,
            'total_expected_files': len(FRENCH_STATIONS) * len(YEARS),
        },
        'created': Path.cwd().name,
    }
    
    config_file = BRONZE_DIR.parent.parent / 'datalake_config.json'
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Configuration: {config_file}")
    print("\n" + "="*60)
    print("Data Lake setup complété!")
    print("="*60)

if __name__ == "__main__":
    setup_datalake()
