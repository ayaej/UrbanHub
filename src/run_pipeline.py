#!/usr/bin/env python3
"""
UrbanHub Complete Pipeline
Orchestrate: Bronze → Silver → Gold + MinIO + PostgreSQL
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import PROJECT_ROOT, BRONZE_DIR, SILVER_DIR, GOLD_DIR, setup_logger
from src.downloader import download_all_data
from src.silver_processor import process_bronze_to_silver
from src.gold_aggregator import generate_gold
from src.visualizer import generate_visualizations
from src.storage import HybridStorage, LocalStorage
from src.postgres_export import export_to_postgres

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrateur complet du pipeline"""
    
    def __init__(self, skip_download: bool = False, workers: int = 4, 
                 use_minio: bool = False, use_postgres: bool = False,
                 minio_config: dict = None, postgres_config: dict = None):
        """
        Initialise l'orchestrateur
        
        Args:
            skip_download: Skip étape download
            workers: Nombre de workers parallèles
            use_minio: Activer MinIO sync
            use_postgres: Activer PostgreSQL export
            minio_config: Config MinIO {endpoint, access_key, secret_key, bucket, secure}
            postgres_config: Config PostgreSQL {host, port, database, user, password}
        """
        self.skip_download = skip_download
        self.workers = workers
        self.use_minio = use_minio
        self.use_postgres = use_postgres
        
        # Configuration par défaut
        self.minio_config = minio_config or {
            'endpoint': os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
            'access_key': os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
            'secret_key': os.getenv('MINIO_SECRET_KEY', 'minioadmin123'),
            'bucket': os.getenv('MINIO_BUCKET', 'urbanhub'),
            'secure': os.getenv('MINIO_SECURE', 'false').lower() == 'true',
        }
        
        self.postgres_config = postgres_config or {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'urbanhub'),
            'user': os.getenv('POSTGRES_USER', 'urbanhub_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'urbanhub_password'),
        }
        
        # Initialise storage hybride
        self.storage = HybridStorage(use_minio=use_minio, **self.minio_config) if use_minio else None
        
        self.start_time = datetime.now()
        self.stats = {
            'bronze_files': 0,
            'silver_records': 0,
            'gold_records': 0,
            'extreme_events': 0,
        }
    
    def run_full_pipeline(self) -> bool:
        """Exécute le pipeline complet"""
        try:
            logger.info("=" * 80)
            logger.info("🚀 UrbanHub Pipeline - Démarrage complet")
            logger.info("=" * 80)
            
            # 1️⃣ SETUP
            logger.info("\n[1/6] Initialisation Data Lake...")
            self._setup_datalake()
            
            # 2️⃣ DOWNLOAD
            if not self.skip_download:
                logger.info("\n[2/6] Téléchargement NOAA...")
                if not self._run_download():
                    logger.error("Download failed!")
                    return False
            else:
                logger.info("\n[2/6] ⏭️  Skip download (Bronze déjà téléchargé)")
            
            # 3️⃣ SILVER
            logger.info("\n[3/6] Transformation Silver (Bronze - Parquet)...")
            if not self._run_silver():
                logger.error("Silver processing failed!")
                return False
            
            # 4️⃣ GOLD
            logger.info("\n[4/6] Agrégation Gold (indicateurs)...")
            if not self._run_gold():
                logger.error("Gold aggregation failed!")
                return False
            
            # 5️⃣ VISUALIZATIONS
            logger.info("\n[5/6] Génération visualisations...")
            if not self._run_visualizations():
                logger.warning("Visualization generation failed (non-critique)")
            
            # 6️⃣ EXPORT
            logger.info("\n[6/6] Export PostGreSQL + MinIO...")
            self._run_export()
            
            # Résumé final
            self._print_summary()
            return True
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            return False
    
    def _setup_datalake(self):
        """Initialise structure Data Lake"""
        try:
            BRONZE_DIR.mkdir(parents=True, exist_ok=True)
            SILVER_DIR.mkdir(parents=True, exist_ok=True)
            GOLD_DIR.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"✅ Bronze: {BRONZE_DIR}")
            logger.info(f"✅ Silver: {SILVER_DIR}")
            logger.info(f"✅ Gold: {GOLD_DIR}")
        except Exception as e:
            logger.error(f"Setup error: {e}")
            raise
    
    def _run_download(self) -> bool:
        """Exécute téléchargement NOAA"""
        try:
            result = download_all_data(workers=self.workers)
            self.stats['bronze_files'] = len(list(BRONZE_DIR.glob("**/*.gz")))
            logger.info(f"✅ Download complete: {self.stats['bronze_files']} files")
            return True
        except Exception as e:
            logger.error(f"Download error: {e}")
            return False
    
    def _run_silver(self) -> bool:
        """Exécute transformation Silver"""
        try:
            result = process_bronze_to_silver()
            self.stats['silver_records'] = len(list(SILVER_DIR.glob("**/*.parquet")))
            logger.info(f"✅ Silver complete: {self.stats['silver_records']} partitions")
            return True
        except Exception as e:
            logger.error(f"Silver error: {e}")
            return False
    
    def _run_gold(self) -> bool:
        """Exécute agrégation Gold"""
        try:
            generate_gold()
            
            # Compte records
            daily_parquet = GOLD_DIR / "weather_daily.parquet"
            extreme_parquet = GOLD_DIR / "weather_extreme_days.parquet"
            
            if daily_parquet.exists():
                import pandas as pd
                df = pd.read_parquet(daily_parquet)
                self.stats['gold_records'] = len(df)
            
            if extreme_parquet.exists():
                extreme_df = pd.read_parquet(extreme_parquet)
                self.stats['extreme_events'] = len(extreme_df)
            
            logger.info(f"✅ Gold complete: {self.stats['gold_records']} daily + {self.stats['extreme_events']} events")
            return True
        except Exception as e:
            logger.error(f"Gold error: {e}")
            return False
    
    def _run_visualizations(self) -> bool:
        """Exécute génération visualisations"""
        try:
            generate_visualizations()
            viz_dir = GOLD_DIR / "visualizations"
            if viz_dir.exists():
                viz_count = len(list(viz_dir.glob("*.png")))
                logger.info(f"✅ Visualizations: {viz_count} charts generated")
            return True
        except Exception as e:
            logger.error(f"Visualization error: {e}")
            return False
    
    def _run_export(self):
        """Exécute exports (MinIO + PostgreSQL)"""
        try:
            # Export MinIO
            if self.use_minio:
                logger.info("Uploading to MinIO...")
                self._sync_to_minio()
            
            # Export PostgreSQL
            if self.use_postgres:
                logger.info("Exporting to PostgreSQL...")
                self._export_to_postgres()
            
        except Exception as e:
            logger.warning(f"Export error: {e}")
    
    def _sync_to_minio(self):
        """Sync fichiers Gold vers MinIO"""
        if not self.storage or not self.storage.minio:
            logger.warning("MinIO not available")
            return
        
        try:
            for file in GOLD_DIR.glob("**/*"):
                if file.is_file():
                    remote_path = f"gold/{file.relative_to(GOLD_DIR)}"
                    self.storage.minio.upload_parquet(str(file), remote_path)
            
            logger.info("✅ MinIO sync complete")
        except Exception as e:
            logger.error(f"MinIO sync error: {e}")
    
    def _export_to_postgres(self):
        """Export données vers PostgreSQL"""
        try:
            export_to_postgres(
                str(GOLD_DIR),
                **self.postgres_config
            )
            logger.info("✅ PostgreSQL export complete")
        except Exception as e:
            logger.error(f"PostgreSQL export error: {e}")
    
    def _print_summary(self):
        """Affiche résumé final"""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        summary = f"""
{'='*80}
✅ PIPELINE COMPLETED SUCCESSFULLY
{'='*80}

📊 STATISTICS:
   Bronze files:      {self.stats['bronze_files']} fichiers
   Silver records:    {self.stats['silver_records']} partitions
   Gold daily:        {self.stats['gold_records']:,} lignes
   Extreme events:    {self.stats['extreme_events']:,} événements

⏱️  DURATION: {duration:.1f} secondes

📁 OUTPUT:
   Bronze: {BRONZE_DIR}
   Silver: {SILVER_DIR}
   Gold:   {GOLD_DIR}

✨ NEXT STEPS:
   1. python validate_pipeline.py      (Valide les résultats)
   2. ls data/lake/gold/               (Explore les fichiers)
   3. Charger dans Power BI/Tableau   (Connecter à PostgreSQL)

{'='*80}
"""
        logger.info(summary)
        print(summary)


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(
        description='UrbanHub Complete Pipeline'
    )
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help='Skip NOAA download (Bronze déjà présent)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Nombre de workers parallèles (défaut: 4)'
    )
    parser.add_argument(
        '--use-minio',
        action='store_true',
        help='Activer MinIO sync'
    )
    parser.add_argument(
        '--use-postgres',
        action='store_true',
        help='Activer PostgreSQL export'
    )
    parser.add_argument(
        '--logs-dir',
        default='logs',
        help='Répertoire logs'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logger(args.logs_dir)
    
    # Exécute pipeline
    orchestrator = PipelineOrchestrator(
        skip_download=args.skip_download,
        workers=args.workers,
        use_minio=args.use_minio,
        use_postgres=args.use_postgres,
    )
    
    success = orchestrator.run_full_pipeline()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
