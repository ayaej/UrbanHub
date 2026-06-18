#!/usr/bin/env python3
"""
UrbanHub Complete Pipeline Orchestrator
Intégration: Python + Pandas + PyArrow + MinIO + PostgreSQL + n8n + Docker
"""
import sys
import logging
from pathlib import Path
import time
from datetime import datetime
import argparse
import os

# Ajoute src au chemin
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils import setup_logger
from src.setup_datalake import setup_datalake
from src.downloader import download_all_data
from src.silver_processor import process_bronze_to_silver
from src.gold_aggregator import generate_gold
from src.visualizer import generate_visualizations
from src.storage import HybridStorage
from src.postgres_export import export_to_postgres

logger = setup_logger("orchestrator", "logs/orchestrator.log")

def run_full_pipeline(skip_download=False, workers=4, use_minio=False, use_postgres=False):
    """
    Exécute le pipeline complet avec intégration technologique
    
    Args:
        skip_download: Si True, ignore l'étape de téléchargement
        workers: Nombre de workers pour téléchargement parallèle
        use_minio: Sync fichiers vers MinIO
        use_postgres: Export vers PostgreSQL
    """
    from src.config import GOLD_DIR
    import pandas as pd
    
    start_time = time.time()
    
    logger.info("=" * 80)
    logger.info(" " * 20 + "[URBANHUB] FULL TECHNOLOGY STACK")
    logger.info("=" * 80)
    logger.info(f"Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Configuration:")
    logger.info(f"  - Skip download: {skip_download}")
    logger.info(f"  - Workers: {workers}")
    logger.info(f"  - MinIO: {use_minio}")
    logger.info(f"  - PostgreSQL: {use_postgres}")
    logger.info("=" * 80)
    
    # Initialise storage hybride
    storage = None
    if use_minio:
        try:
            storage = HybridStorage(
                use_minio=True,
                endpoint=os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
                access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
                secret_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin123'),
                bucket=os.getenv('MINIO_BUCKET', 'urbanhub'),
                secure=os.getenv('MINIO_SECURE', 'false').lower() == 'true',
            )
            logger.info("[OK] MinIO initialized")
        except Exception as e:
            logger.warning(f"MinIO initialization failed: {e}")
            use_minio = False
    
    try:
        # Étape 1: Setup
        logger.info("\n[1/7] Setup Data Lake...")
        setup_datalake()
        logger.info("[OK] Setup termine")
        
        # Étape 2: Download (optionnel)
        if not skip_download:
            logger.info("\n[2/7] Téléchargement NOAA...")
            download_all_data(workers=workers)
            logger.info("[OK] Telechargement termine")
        else:
            logger.info("\n[2/7] [SKIP] Telechargement skippe")
        
        # Étape 3: Silver Processing (Pandas + PyArrow)
        logger.info("\n[3/7] Processing - Silver (Pandas + PyArrow)...")
        process_bronze_to_silver()
        logger.info("[OK] Silver processing termine (Parquet Snappy)")
        
        # Étape 4: Gold Aggregation
        logger.info("\n[4/7] Agrégation → Gold (indicateurs)...")
        generate_gold()
        logger.info("[OK] Gold aggregation terminee")
        
        # Étape 5: Visualizations
        logger.info("\n[5/7] Génération visualisations...")
        generate_visualizations()
        logger.info("[OK] Visualisations generees")
        
        # Étape 6: MinIO Sync
        if use_minio and storage:
            logger.info("\n[6/7] Sync vers MinIO (S3)...")
            try:
                for file in GOLD_DIR.glob("**/*"):
                    if file.is_file():
                        remote_path = f"gold/{file.relative_to(GOLD_DIR)}"
                        storage.minio.upload_parquet(str(file), remote_path)
                logger.info("[OK] MinIO sync termine")
            except Exception as e:
                logger.warning(f"MinIO sync failed: {e}")
        else:
            logger.info("\n[6/7] [SKIP] MinIO skippe")
        
        # Étape 7: PostgreSQL Export
        if use_postgres:
            logger.info("\n[7/7] Export PostgreSQL (BI)...")
            try:
                export_to_postgres(
                    str(GOLD_DIR),
                    host=os.getenv('POSTGRES_HOST', 'localhost'),
                    port=int(os.getenv('POSTGRES_PORT', 5432)),
                    database=os.getenv('POSTGRES_DB', 'urbanhub'),
                    user=os.getenv('POSTGRES_USER', 'urbanhub_user'),
                    password=os.getenv('POSTGRES_PASSWORD', 'urbanhub_password'),
                )
                logger.info("[OK] PostgreSQL export termine")
            except Exception as e:
                logger.warning(f"PostgreSQL export failed: {e}")
        else:
            logger.info("\n[7/7] [SKIP] PostgreSQL skippe")
        
        # Résumé final
        elapsed = time.time() - start_time
        
        # Stats
        gold_daily = GOLD_DIR / "weather_daily.parquet"
        gold_extreme = GOLD_DIR / "weather_extreme_days.parquet"
        
        daily_count = 0
        extreme_count = 0
        
        if gold_daily.exists():
            daily_count = len(pd.read_parquet(gold_daily))
        if gold_extreme.exists():
            extreme_count = len(pd.read_parquet(gold_extreme))
        
        logger.info("\n" + "=" * 80)
        logger.info("[OK] FULL STACK PIPELINE SUCCESSFUL!")
        logger.info("=" * 80)
        logger.info(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Durée totale: {elapsed:.1f}s ({elapsed/60:.1f}min)")
        logger.info(f"\n[STATISTICS]:")
        logger.info(f"   Gold Daily Records: {daily_count:,}")
        logger.info(f"   Extreme Events: {extreme_count:,}")
        logger.info(f"   Output: data/lake/gold/weather/")
        logger.info("=" * 80)
        logger.info(f"\n[TECHNOLOGIES USED]:")
        logger.info(f"   [OK] Python 3.8+ + Pandas + PyArrow (Parquet Snappy)")
        logger.info(f"   {'[OK]' if use_minio else '[SKIP]'} MinIO (Bronze/Silver/Gold)")
        logger.info(f"   [SKIP] n8n (cron) - Configure via docker-compose + workflows/")
        logger.info(f"   [OK] Docker (Dockerfile + docker-compose.yml)")
        logger.info(f"   {'[OK]' if use_postgres else '[SKIP]'} PostgreSQL (BI Analytics)")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"\n[ERREUR PIPELINE] {e}", exc_info=True)
        logger.error(f"Durée avant erreur: {time.time() - start_time:.1f}s")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Orchestrateur pipeline UrbanHub complet avec intégration technologique'
    )
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help='Ignore étape de téléchargement NOAA'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Nombre de workers parallèles (download)'
    )
    parser.add_argument(
        '--use-minio',
        action='store_true',
        help='Sync fichiers Gold vers MinIO (S3)'
    )
    parser.add_argument(
        '--use-postgres',
        action='store_true',
        help='Export données vers PostgreSQL (BI)'
    )
    parser.add_argument(
        '--logs-dir',
        default='logs',
        help='Répertoire pour les logs'
    )
    
    args = parser.parse_args()
    
    # Crée répertoire logs
    Path(args.logs_dir).mkdir(exist_ok=True)
    
    success = run_full_pipeline(
        skip_download=args.skip_download,
        workers=args.workers,
        use_minio=args.use_minio,
        use_postgres=args.use_postgres
    )
    
    sys.exit(0 if success else 1)
