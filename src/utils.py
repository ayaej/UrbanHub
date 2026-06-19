"""
Fonctions utilitaires pour UrbanHub
"""
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

# Configuration logging
def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Configure et retourne un logger"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optionnel)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def parse_noaa_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse timestamp NOAA en datetime UTC"""
    try:
        # Format: YYYY-MM-DDTHH:MM:SS
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None

def celsius_to_kelvin(celsius: float) -> float:
    """Conversion Celsius → Kelvin"""
    return celsius + 273.15

def convert_visibility(visibility_m: float) -> float:
    """Convertit visibilité de mètres en km"""
    if visibility_m is None or visibility_m < 0:
        return None
    return visibility_m / 1000

def get_season(month: int) -> str:
    """Retourne la saison pour un mois donné"""
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    else:
        return 'autumn'

def validate_weather_record(record: dict) -> bool:
    """Valide un enregistrement météo"""
    required_fields = ['station_id', 'timestamp']
    return all(field in record and record[field] for field in required_fields)

class ProgressTracker:
    """Suivi de progression"""
    def __init__(self, total: int, name: str = "Processing"):
        self.total = total
        self.current = 0
        self.name = name
    
    def update(self, increment: int = 1):
        """Met à jour la progression"""
        self.current += increment
        pct = (self.current / self.total) * 100
        print(f"{self.name}: {self.current}/{self.total} ({pct:.1f}%)", end='\r')
    
    def finish(self):
        """Affiche la fin"""
        print(f"\n✓ {self.name} terminé: {self.total}/{self.total}")

if __name__ == "__main__":
    logger = setup_logger("test")
    logger.info("Test logger")
    print(f"Season for March: {get_season(3)}")
