"""
Upload du fichier Bronze IoT vers MinIO (Data Lake).

Ce script est appelé par le workflow maître n8n après chaque cycle
de collecte pour archiver le fichier JSONL dans la couche Bronze du Data Lake.

Structure MinIO :
  urbanhub/
  └── bronze/
      └── iot/
          └── bronze_iot_openaq.log
"""

import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

BRONZE_FILE   = ROOT_DIR / "data" / "bronze_iot" / "bronze_iot_openaq.log"
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS   = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET   = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET   = os.getenv("MINIO_BUCKET", "urbanhub")
MINIO_SECURE   = os.getenv("MINIO_SECURE", "false").lower() == "true"

# Clé S3 : bronze/iot/YYYY-MM-DD/bronze_iot_openaq.log
DATE_PREFIX   = datetime.now(timezone.utc).strftime("%Y-%m-%d")
MINIO_KEY     = f"bronze/iot/{DATE_PREFIX}/bronze_iot_openaq.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def get_s3_client():
    protocol = "https" if MINIO_SECURE else "http"
    return boto3.client(
        "s3",
        endpoint_url=f"{protocol}://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_ACCESS,
        aws_secret_access_key=MINIO_SECRET,
        region_name="us-east-1",
    )


def ensure_bucket(client) -> None:
    try:
        client.head_bucket(Bucket=MINIO_BUCKET)
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            client.create_bucket(Bucket=MINIO_BUCKET)
            logging.info("Bucket '%s' créé.", MINIO_BUCKET)
        else:
            raise


def upload_bronze(client) -> None:
    if not BRONZE_FILE.exists():
        logging.error("Fichier Bronze introuvable : %s", BRONZE_FILE)
        sys.exit(1)

    size_kb = BRONZE_FILE.stat().st_size / 1024
    logging.info("Upload %s (%.1f Ko) → s3://%s/%s", BRONZE_FILE.name, size_kb, MINIO_BUCKET, MINIO_KEY)

    client.upload_file(str(BRONZE_FILE), MINIO_BUCKET, MINIO_KEY)
    logging.info("Upload terminé : s3://%s/%s", MINIO_BUCKET, MINIO_KEY)


def main():
    client = get_s3_client()
    ensure_bucket(client)
    upload_bronze(client)
    print(f"OK|s3://{MINIO_BUCKET}/{MINIO_KEY}|{BRONZE_FILE.stat().st_size}")


if __name__ == "__main__":
    main()
