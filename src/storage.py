"""
UrbanHub Storage Layer
Support local filesystem et MinIO (S3-compatible)
"""

import os
from pathlib import Path
from typing import Optional, Union
import logging
from abc import ABC, abstractmethod

import pandas as pd
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Interface abstraite pour les backends de stockage"""
    
    @abstractmethod
    def upload_parquet(self, local_path: str, remote_path: str) -> bool:
        """Upload un fichier Parquet"""
        pass
    
    @abstractmethod
    def download_parquet(self, remote_path: str, local_path: str) -> bool:
        """Download un fichier Parquet"""
        pass
    
    @abstractmethod
    def upload_csv(self, local_path: str, remote_path: str) -> bool:
        """Upload un fichier CSV"""
        pass
    
    @abstractmethod
    def list_files(self, prefix: str) -> list:
        """Liste les fichiers"""
        pass


class LocalStorage(StorageBackend):
    """Backend stockage local (filesystem)"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalStorage initialized: {self.base_path}")
    
    def upload_parquet(self, local_path: str, remote_path: str) -> bool:
        """Upload local → local (copie)"""
        try:
            src = Path(local_path)
            dst = self.base_path / remote_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            if src.exists():
                logger.debug(f"LocalStorage: {src} - {dst}")
                return True
            return False
        except Exception as e:
            logger.error(f"LocalStorage upload error: {e}")
            return False
    
    def download_parquet(self, remote_path: str, local_path: str) -> bool:
        """Download local → local (copie)"""
        try:
            src = self.base_path / remote_path
            if src.exists():
                logger.debug(f"LocalStorage: {src} - {local_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"LocalStorage download error: {e}")
            return False
    
    def upload_csv(self, local_path: str, remote_path: str) -> bool:
        """Upload CSV local"""
        return self.upload_parquet(local_path, remote_path)
    
    def list_files(self, prefix: str) -> list:
        """Liste les fichiers locaux"""
        try:
            dir_path = self.base_path / prefix
            if not dir_path.exists():
                return []
            return [str(f.relative_to(self.base_path)) 
                   for f in dir_path.glob("**/*") if f.is_file()]
        except Exception as e:
            logger.error(f"LocalStorage list error: {e}")
            return []


class MinIOStorage(StorageBackend):
    """Backend MinIO (S3-compatible)"""
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool = False):
        """
        Initialise connexion MinIO
        
        Args:
            endpoint: "localhost:9000" ou "minio.example.com"
            access_key: "minioadmin"
            secret_key: "minioadmin123"
            bucket: "urbanhub"
            secure: True si HTTPS, False si HTTP
        """
        self.bucket = bucket
        
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=f"{'https' if secure else 'http'}://{endpoint}",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name='us-east-1'
            )
            
            # Crée bucket s'il n'existe pas
            self._create_bucket()
            logger.info(f"MinIOStorage initialized: {endpoint}/{bucket}")
            
        except Exception as e:
            logger.error(f"MinIO connection error: {e}")
            raise
    
    def _create_bucket(self) -> bool:
        """Crée le bucket s'il n'existe pas"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
            logger.debug(f"Bucket '{self.bucket}' exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket)
                    logger.info(f"Created bucket '{self.bucket}'")
                    return True
                except Exception as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    return False
            raise
    
    def upload_parquet(self, local_path: str, remote_path: str) -> bool:
        """Upload Parquet vers MinIO"""
        try:
            if not Path(local_path).exists():
                logger.error(f"File not found: {local_path}")
                return False
            
            self.s3_client.upload_file(local_path, self.bucket, remote_path)
            logger.info(f"Uploaded Parquet: s3://{self.bucket}/{remote_path}")
            return True
            
        except ClientError as e:
            logger.error(f"MinIO upload error: {e}")
            return False
    
    def download_parquet(self, remote_path: str, local_path: str) -> bool:
        """Download Parquet depuis MinIO"""
        try:
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            self.s3_client.download_file(self.bucket, remote_path, local_path)
            logger.info(f"Downloaded Parquet: s3://{self.bucket}/{remote_path}")
            return True
            
        except ClientError as e:
            logger.error(f"MinIO download error: {e}")
            return False
    
    def upload_csv(self, local_path: str, remote_path: str) -> bool:
        """Upload CSV vers MinIO"""
        return self.upload_parquet(local_path, remote_path)
    
    def list_files(self, prefix: str) -> list:
        """Liste fichiers MinIO avec prefix"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            return [obj['Key'] for obj in response['Contents']]
            
        except ClientError as e:
            logger.error(f"MinIO list error: {e}")
            return []


class HybridStorage:
    """Stockage hybride: local + MinIO"""
    
    def __init__(self, use_minio: bool = False, **minio_config):
        """
        Initialise storage hybride
        
        Args:
            use_minio: True pour utiliser MinIO en plus du local
            minio_config: {endpoint, access_key, secret_key, bucket, secure}
        """
        from src.config import GOLD_DIR
        
        self.local = LocalStorage(str(GOLD_DIR))
        self.use_minio = use_minio
        self.minio = None
        
        if use_minio:
            try:
                self.minio = MinIOStorage(**minio_config)
                logger.info("Hybrid storage: local + MinIO enabled")
            except Exception as e:
                logger.warning(f"MinIO disabled: {e}")
                self.use_minio = False
    
    def save_parquet(self, df: pd.DataFrame, local_path: str, remote_path: Optional[str] = None):
        """Sauvegarde Parquet localement et optionnellement sur MinIO"""
        try:
            # Sauvegarde local
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(local_path, index=False, compression='snappy')
            logger.info(f"Saved Parquet: {local_path}")
            
            # Sauvegarde MinIO si activé
            if self.use_minio and self.minio and remote_path:
                if self.minio.upload_parquet(local_path, remote_path):
                    logger.info(f"Synced to MinIO: {remote_path}")
            
            return True
        except Exception as e:
            logger.error(f"Save error: {e}")
            return False
    
    def save_csv(self, df: pd.DataFrame, local_path: str, remote_path: Optional[str] = None):
        """Sauvegarde CSV localement et optionnellement sur MinIO"""
        try:
            # Sauvegarde local
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(local_path, index=False)
            logger.info(f"Saved CSV: {local_path}")
            
            # Sauvegarde MinIO si activé
            if self.use_minio and self.minio and remote_path:
                if self.minio.upload_csv(local_path, remote_path):
                    logger.info(f"Synced to MinIO: {remote_path}")
            
            return True
        except Exception as e:
            logger.error(f"Save error: {e}")
            return False
