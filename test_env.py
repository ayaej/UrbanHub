# test_env.py
from pathlib import Path
from dotenv import load_dotenv
import os

ROOT_DIR = Path(__file__).resolve().parent  # racine du projet
load_dotenv(ROOT_DIR / ".env")

print("ROOT_DIR =", ROOT_DIR)
print("OPENAQ_API_KEY =", os.getenv("OPENAQ_API_KEY"))
print("N8N_WEBHOOK_IOT =", os.getenv("N8N_WEBHOOK_IOT"))