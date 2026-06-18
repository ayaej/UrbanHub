#!/usr/bin/env python
"""Test d'accès aux URLs NOAA"""
import requests

# Test les 3 premières stations pour 2020
stations = ['07015099999', '07149099999', '07480099999']
year = 2020

print(f"Test accès NOAA - Année {year}\n")
print("=" * 60)

for station in stations:
    url = f'https://www.ncei.noaa.gov/data/global-hourly/access/{year}/{station}.csv'
    try:
        response = requests.head(url, timeout=5)
        status = "✅" if response.status_code == 200 else "❌"
        size = response.headers.get('Content-Length', 'N/A')
        print(f"{status} {station}: {response.status_code} ({size} bytes)")
    except Exception as e:
        print(f"❌ {station}: Erreur - {type(e).__name__}")
