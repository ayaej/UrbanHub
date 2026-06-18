#!/usr/bin/env python
"""Trouve les stations NOAA françaises"""
import requests
import re

# Stations françaises avec leurs WMO IDs connus
FRENCH_STATIONS_WMO = {
    '07015': 'Paris CDG (LFPG)',
    '07149': 'Paris Orly (LFPO)',
    '07650': 'Marseille (LFML)',
    '07480': 'Lyon (LFLY)',
    '07610': 'Toulouse (LFTH)',
    '07761': 'Nice (LFMN)',
    '07586': 'Strasbourg (LFST)',
    '07379': 'Nantes (LFRJ)',
}

print("Exploration NOAA 2020 - Recherche stations françaises\n")
print("=" * 60)

url = 'https://www.ncei.noaa.gov/data/global-hourly/access/2020/'
try:
    response = requests.get(url, timeout=10)
    
    # Extrait tous les fichiers CSV
    files = re.findall(r'<a href="(\d+\.csv)">', response.text)
    print(f"✓ Total fichiers trouvés: {len(files)}")
    
    # Cherche les stations françaises par leurs codes WMO
    french_files = []
    for file in files:
        for wmo_id in FRENCH_STATIONS_WMO.keys():
            if file.startswith(wmo_id):
                french_files.append((file, wmo_id))
                break
    
    print(f"\n✓ Stations françaises trouvées: {len(french_files)}\n")
    for file, wmo_id in sorted(french_files):
        station_name = FRENCH_STATIONS_WMO[wmo_id]
        print(f"  {file:20} → {station_name}")
    
    if not french_files:
        print("  ❌ Aucune station française trouvée avec WMO IDs")
        print("\n  Cherche patterns alternatifs...")
        
        # Affiche 10 premiers fichiers pour comprendre le pattern
        print("\n  Premiers 10 fichiers disponibles:")
        for f in sorted(files)[:10]:
            print(f"    {f}")
    
except Exception as e:
    print(f"✗ Erreur: {e}")
