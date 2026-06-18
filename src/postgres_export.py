"""
UrbanHub PostgreSQL Export
Export données Gold vers PostgreSQL pour BI
"""

import os
import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import sqlalchemy as sql
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class PostgreSQLExporter:
    """Export données vers PostgreSQL pour analytique BI"""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        """
        Initialise connexion PostgreSQL
        
        Args:
            host: "localhost"
            port: 5432
            database: "urbanhub"
            user: "urbanhub_user"
            password: "urbanhub_password"
        """
        self.connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        try:
            self.engine = create_engine(self.connection_string, echo=False)
            
            # Test connexion
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"PostgreSQL connected: {host}:{port}/{database}")
            
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """Vérifie si une table existe"""
        try:
            inspector = inspect(self.engine)
            return table_name in inspector.get_table_names()
        except Exception as e:
            logger.error(f"Check table error: {e}")
            return False
    
    def drop_table(self, table_name: str) -> bool:
        """Supprime une table (utile pour rechargement)"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                conn.commit()
            logger.info(f"Dropped table: {table_name}")
            return True
        except Exception as e:
            logger.error(f"Drop table error: {e}")
            return False
    
    def export_dataframe(self, df: pd.DataFrame, table_name: str, if_exists: str = 'replace') -> bool:
        """
        Export DataFrame vers PostgreSQL
        
        Args:
            df: DataFrame Pandas
            table_name: Nom table PostgreSQL
            if_exists: 'fail', 'replace', 'append'
        """
        try:
            rows = df.to_sql(
                table_name,
                self.engine,
                if_exists=if_exists,
                index=False,
                method='multi',
                chunksize=10000
            )
            logger.info(f"Exported {rows} rows to {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            return False
    
    def export_weather_daily(self, parquet_path: str) -> bool:
        """Export weather_daily.parquet"""
        try:
            if not Path(parquet_path).exists():
                logger.error(f"File not found: {parquet_path}")
                return False
            
            df = pd.read_parquet(parquet_path)
            
            # Rename columns to match database schema
            df = df.rename(columns={
                'temperature_min': 'temperature_min',
                'temperature_max': 'temperature_max',
                'temperature_mean': 'temperature_mean',
                'wind_speed_mean': 'wind_speed_mean',
                'wind_direction_mean': 'wind_direction_mean',
                'pressure_mean': 'pressure_mean',
                'precipitation_sum': 'precipitation_total',  # Rename to match database
                'visibility_mean': 'visibility_mean',
            })
            
            # Remove columns that don't exist in database
            allowed_cols = ['date', 'city', 'station_id', 'temperature_mean', 'temperature_min', 
                           'temperature_max', 'wind_speed_mean', 'wind_direction_mean', 
                           'pressure_mean', 'precipitation_total', 'visibility_mean']
            df = df[[col for col in allowed_cols if col in df.columns]]
            
            # Type conversions for PostgreSQL
            df['date'] = pd.to_datetime(df['date'])
            for col in ['temperature_mean', 'temperature_min', 'temperature_max', 
                       'wind_speed_mean', 'wind_direction_mean', 'pressure_mean', 
                       'precipitation_total', 'visibility_mean']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Create table
            self.drop_table('weather_daily')
            self.export_dataframe(df, 'weather_daily', if_exists='replace')
            
            # Index for BI performance
            self._create_indexes('weather_daily', ['date', 'city', 'station_id'])
            
            return True
            
        except Exception as e:
            logger.error(f"Export weather_daily error: {e}")
            return False
    
    def export_extreme_days(self, parquet_path: str) -> bool:
        """Export weather_extreme_days.parquet"""
        try:
            if not Path(parquet_path).exists():
                logger.error(f"File not found: {parquet_path}")
                return False
            
            df = pd.read_parquet(parquet_path)
            
            # Conversions
            df['date'] = pd.to_datetime(df['date'])
            
            self.drop_table('weather_extreme_days')
            self.export_dataframe(df, 'weather_extreme_days', if_exists='replace')
            
            self._create_indexes('weather_extreme_days', ['date', 'city', 'event_type'])
            
            return True
            
        except Exception as e:
            logger.error(f"Export extreme_days error: {e}")
            return False
    
    def export_correlations(self, csv_path: str) -> bool:
        """Export weather_correlations.csv"""
        try:
            if not Path(csv_path).exists():
                logger.error(f"File not found: {csv_path}")
                return False
            
            df = pd.read_csv(csv_path)
            
            self.drop_table('weather_correlations')
            self.export_dataframe(df, 'weather_correlations', if_exists='replace')
            
            return True
            
        except Exception as e:
            logger.error(f"Export correlations error: {e}")
            return False
    
    def export_city_summary(self, csv_path: str) -> bool:
        """Export city_summary_annual.csv"""
        try:
            if not Path(csv_path).exists():
                logger.error(f"File not found: {csv_path}")
                return False
            
            df = pd.read_csv(csv_path)
            
            # Ensure all required columns exist
            if 'year' in df.columns:
                df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int32')
            else:
                df['year'] = 2025  # Default year if missing
            
            # Convert numeric columns
            numeric_cols = [col for col in df.columns if col != 'city' and col != 'year']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            self.drop_table('city_summary_annual')
            self.export_dataframe(df, 'city_summary_annual', if_exists='replace')
            
            self._create_indexes('city_summary_annual', ['city', 'year'])
            
            return True
            
        except Exception as e:
            logger.error(f"Export city_summary error: {e}")
            return False
    
    def _create_indexes(self, table_name: str, columns: list) -> bool:
        """Crée indexes pour performance BI"""
        try:
            with self.engine.connect() as conn:
                for col in columns:
                    index_name = f"{table_name}_{col}_idx"
                    conn.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({col})"))
                conn.commit()
            logger.info(f"Indexes created for {table_name}")
            return True
        except Exception as e:
            logger.error(f"Index creation error: {e}")
            return False
    
    def export_all_gold(self, gold_dir: str) -> bool:
        """Export tous les fichiers Gold"""
        try:
            gold_path = Path(gold_dir)
            
            # Export tous les fichiers
            exports = [
                ('weather_daily.parquet', self.export_weather_daily),
                ('weather_extreme_days.parquet', self.export_extreme_days),
                ('weather_correlations.csv', self.export_correlations),
                ('city_summary_annual.csv', self.export_city_summary),
            ]
            
            success_count = 0
            for filename, export_func in exports:
                file_path = gold_path / filename
                if file_path.exists():
                    if export_func(str(file_path)):
                        success_count += 1
                else:
                    logger.warning(f"File not found: {filename}")
            
            logger.info(f"PostgreSQL export complete: {success_count}/{len(exports)} tables")
            return success_count == len(exports)
            
        except Exception as e:
            logger.error(f"Export all error: {e}")
            return False
    
    def get_connection_info(self) -> dict:
        """Retourne infos connexion pour BI tools"""
        return {
            'engine': 'postgresql',
            'connection_string': self.connection_string,
            'tables': {
                'weather_daily': 'Données quotidiennes (17,850 lignes)',
                'weather_extreme_days': 'Événements extrêmes (~1,200)',
                'weather_correlations': '8 corrélations météo',
                'city_summary_annual': 'Résumé annuel par ville',
            }
        }
    
    def create_analytics_views(self) -> bool:
        """Crée vues SQL pour BI (Power BI, Tableau, etc.)"""
        try:
            with self.engine.connect() as conn:
                
                # Vue: Tendances température par ville
                conn.execute(text("""
                    CREATE OR REPLACE VIEW v_temperature_trends AS
                    SELECT 
                        city,
                        DATE_TRUNC('month', date) as month,
                        AVG(temperature_mean) as avg_temp,
                        MIN(temperature_min) as min_temp,
                        MAX(temperature_max) as max_temp,
                        STDDEV(temperature_mean) as volatility
                    FROM weather_daily
                    GROUP BY city, DATE_TRUNC('month', date)
                    ORDER BY city, month
                """))
                
                # Vue: Événements extrêmes par type
                conn.execute(text("""
                    CREATE OR REPLACE VIEW v_extreme_events_summary AS
                    SELECT 
                        city,
                        event_type,
                        EXTRACT(YEAR FROM date) as year,
                        COUNT(*) as count,
                        AVG(severity) as avg_severity
                    FROM weather_extreme_days
                    GROUP BY city, event_type, EXTRACT(YEAR FROM date)
                    ORDER BY year DESC, count DESC
                """))
                
                # Vue: Corrélations par saison
                conn.execute(text("""
                    CREATE OR REPLACE VIEW v_correlations_by_season AS
                    SELECT 
                        season,
                        city,
                        weather_variable,
                        ROUND(correlation::numeric, 3) as correlation,
                        sample_size
                    FROM weather_correlations
                    WHERE correlation IS NOT NULL
                    ORDER BY season, ABS(correlation) DESC
                """))
                
                conn.commit()
                logger.info("Analytics views created")
                return True
                
        except Exception as e:
            logger.error(f"View creation error: {e}")
            return False


def export_to_postgres(gold_dir: str, host: str = 'localhost', port: int = 5432,
                       database: str = 'urbanhub', user: str = 'urbanhub_user',
                       password: str = 'urbanhub_password') -> bool:
    """Fonction helper pour export complet"""
    try:
        exporter = PostgreSQLExporter(host, port, database, user, password)
        
        # Export données
        success = exporter.export_all_gold(gold_dir)
        
        # Crée vues
        exporter.create_analytics_views()
        
        logger.info("PostgreSQL export complete!")
        return success
        
    except Exception as e:
        logger.error(f"PostgreSQL export failed: {e}")
        return False
