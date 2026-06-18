"""
Téléchargement parallèle des données NOAA pour stations françaises
Gère : index parsing, téléchargement parallèle, retry, logging
"""
import requests
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import (
    NOAA_BASE_URL, FRENCH_STATIONS, YEARS, BRONZE_DIR, 
    WORKERS, RETRY_ATTEMPTS, TIMEOUT
)
from utils import setup_logger, ProgressTracker

logger = setup_logger("downloader", "logs/downloader.log")

def create_session() -> requests.Session:
    """Crée une session requests avec retry strategy"""
    session = requests.Session()
    retry_strategy = Retry(
        total=RETRY_ATTEMPTS,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def list_noaa_files(station_id: str, year: int) -> List[str]:
    """
    Construit l'URL NOAA pour une station et année
    Format: https://www.ncei.noaa.gov/data/global-hourly/access/YYYY/STATION_ID.csv
    Retourne: liste avec l'URL unique du fichier
    """
    # Construit directement l'URL (un seul fichier par station/année)
    file_url = f"{NOAA_BASE_URL}/{year}/{station_id}.csv"
    
    try:
        session = create_session()
        # Vérifie que le fichier existe avec HEAD request
        response = session.head(file_url, timeout=TIMEOUT)
        response.raise_for_status()
        
        logger.debug(f"✓ Trouvé: {station_id}/{year}")
        return [file_url]
        
    except Exception as e:
        logger.warning(f"✗ Fichier absent: {station_id}/{year} - {e}")
        return []

def download_file(url: str, destination: Path, station_id: str, year: int) -> Tuple[bool, str]:
    """
    Télécharge un fichier unique
    Retourne: (succès, message)
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    if destination.exists():
        logger.debug(f"Fichier déjà présent: {destination.name}")
        return True, f"Skipped (exists): {destination.name}"
    
    try:
        session = create_session()
        response = session.get(url, timeout=TIMEOUT, stream=True)
        response.raise_for_status()
        
        # Écriture avec vérification de taille
        with open(destination, 'wb') as f:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
        
        logger.info(f"✓ Téléchargé {destination.name} ({total_size:,} bytes)")
        return True, f"Downloaded: {destination.name}"
        
    except Exception as e:
        logger.error(f"[FAILED] Download {url}: {e}")
        if destination.exists():
            destination.unlink()  # Supprime le fichier partiel
        return False, f"Failed: {url} - {str(e)}"

def download_station_year(station_id: str, year: int) -> Tuple[int, int]:
    """
    Télécharge tous les fichiers pour une station et année
    Retourne: (succès, total)
    """
    files = list_noaa_files(station_id, year)
    
    if not files:
        logger.warning(f"Aucun fichier trouvé: {station_id}/{year}")
        return 0, 0
    
    success_count = 0
    for url in files:
        filename = url.split('/')[-1]
        destination = BRONZE_DIR / f"year={year}" / f"station={station_id}" / filename
        
        success, msg = download_file(url, destination, station_id, year)
        if success:
            success_count += 1
    
    return success_count, len(files)

def download_all_data(workers: int = WORKERS, verbose: bool = True):
    """
    Télécharge toutes les données NOAA pour stations françaises (2020-2025)
    """
    logger.info("=" * 60)
    logger.info(f"Démarrage téléchargement NOAA - {len(FRENCH_STATIONS)} stations × {len(YEARS)} années")
    logger.info(f"Stations: {', '.join(FRENCH_STATIONS.keys())}")
    logger.info(f"Années: {YEARS[0]}-{YEARS[-1]}")
    logger.info(f"Workers: {workers}")
    logger.info("=" * 60)
    
    tasks = [
        (station_id, year)
        for station_id in FRENCH_STATIONS.keys()
        for year in YEARS
    ]
    
    total_tasks = len(tasks)
    tracker = ProgressTracker(total_tasks, "Downloads")
    
    stats = {'total_files': 0, 'downloaded': 0, 'failed': 0, 'start_time': time.time()}
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(download_station_year, station, year): (station, year)
            for station, year in tasks
        }
        
        for future in as_completed(futures):
            station, year = futures[future]
            try:
                success, total = future.result()
                stats['total_files'] += total
                stats['downloaded'] += success
                stats['failed'] += (total - success)
            except Exception as e:
                logger.error(f"Exception for {station}/{year}: {e}")
                stats['failed'] += 1
            
            tracker.update()
    
    tracker.finish()
    
    # Résumé
    elapsed = time.time() - stats['start_time']
    logger.info("\n" + "=" * 60)
    logger.info("RÉSUMÉ DU TÉLÉCHARGEMENT")
    logger.info(f"Fichiers traités: {stats['total_files']}")
    logger.info(f"Réussis: {stats['downloaded']}")
    logger.info(f"Échoués: {stats['failed']}")
    logger.info(f"Taux réussite: {(stats['downloaded']/max(stats['total_files'],1)*100):.1f}%")
    logger.info(f"Durée: {elapsed:.1f}s ({elapsed/60:.1f}min)")
    logger.info(f"Destination: {BRONZE_DIR}")
    logger.info("=" * 60)
    
    return stats

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Télécharge données NOAA pour stations françaises')
    parser.add_argument('--workers', type=int, default=WORKERS, help='Nombre de workers parallèles')
    parser.add_argument('--dry-run', action='store_true', help='Liste les fichiers sans télécharger')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("DRY RUN - Listing fichiers...")
        for station in list(FRENCH_STATIONS.keys())[:2]:  # Test 2 stations
            for year in YEARS[:1]:  # Test 1 année
                files = list_noaa_files(station, year)
                logger.info(f"{station}/{year}: {len(files)} fichiers")
    else:
        download_all_data(workers=args.workers)
