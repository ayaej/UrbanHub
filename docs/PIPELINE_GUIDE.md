# 📖 Guide d'utilisation - Pipeline UrbanHub Batch Météo

👉 **Besoin de démarrer?** Consultez:
- [../INDEX.md](../INDEX.md) - Navigation complète
- [../START.md](../START.md) - Démarrage rapide (3 étapes)
- [../QUICKSTART.md](../QUICKSTART.md) - Guide complet (3 options)

---

## 🎯 Vue d'ensemble

Ce guide explique comment utiliser le pipeline complet de traitement des données NOAA pour générer des indicateurs météorologiques urbains.

---

## 📋 Prérequis

### Système
- Windows/Linux/macOS
- Python 3.8+
- ~2 GB disque libre (pour données 2020-2025)

### Installation

```bash
# 1. Cloner ou accéder au projet
cd d:\UrbanHub

# 2. Créer un environnement virtuel (optionnel mais recommandé)
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/Mac

# 3. Installer les dépendances
pip install -r requirements.txt
```

### Vérification
```bash
python -c "import pandas; print('✓ Pandas OK')"
python -c "import requests; print('✓ Requests OK')"
```

---

## 🚀 Exécution du pipeline

### Étape 1: Setup initial du Data Lake

Crée la structure des répertoires.

```bash
cd src
python setup_datalake.py
```

**Sortie attendue:**
```
✓ Créé: data/lake/bronze/weather/noaa
✓ Créé: data/lake/silver/weather
✓ Créé: data/lake/gold/weather
✓ Configuration: datalake_config.json

Data Lake setup complété!
```

---

### Étape 2: Téléchargement NOAA (Bronze)

Télécharge les données brutes pour toutes les stations françaises (2020-2025).

```bash
python downloader.py --workers 4
```

**Paramètres:**
- `--workers N` : Nombre de téléchargements parallèles (défaut: 4)
- `--dry-run` : Liste les fichiers sans télécharger

**Sortie attendue:**
```
============================================================
Démarrage téléchargement NOAA - 14 stations × 6 années
Stations: LFPG, LFPO, LFBD, LFML, ...
Années: 2020-2025
Workers: 4
============================================================

Downloads: 84/84 (100.0%)
✓ Downloads terminé: 84/84

============================================================
RÉSUMÉ DU TÉLÉCHARGEMENT
Fichiers traités: ~600
Réussis: ~580
Échoués: ~20 (fichiers manquants sur le serveur)
Taux réussite: 96.7%
Durée: 45s (0.8min)
Destination: data/lake/bronze/weather/noaa
============================================================
```

**Durée estimée:** 30-60 secondes (dépend de la connexion)

**Sortie fichiers:**
```
data/lake/bronze/weather/noaa/
├── year=2020/
│   ├── station=LFPG/
│   │   ├── data_2020_1.csv
│   │   ├── data_2020_2.csv
│   │   └── ...
│   └── station=LFPO/
│       └── ...
├── year=2021/
│   └── ...
└── year=2025/
    └── ...
```

---

### Étape 3: Nettoyage → Silver

Transforme les données brutes en données horaires propres et harmonisées.

```bash
python silver_processor.py
```

**Opérations:**
- Parse fichiers CSV NOAA
- Filtre stations françaises
- Normalise timestamps (UTC ISO 8601)
- Convertit unités (°C, m/s, mm, hPa, km)
- Gère valeurs manquantes
- Enrichit avec localisation (ville, saison)
- Partitionne par année/mois/ville
- Sauvegarde en Parquet compressé

**Sortie attendue:**
```
============================================================
Traitement Bronze → Silver (nettoyage)
============================================================
Fichiers trouvés: 580

[1/580] Traitement data_2020_1.csv...
LFPG: Valeurs manquantes: temp=2, wind=15, pressure=1
✓ Sauvegardé: year=2020/month=01/city=Paris/weather_data_2020_01_Paris.parquet (8760 enregistrements)

[2/580] Traitement data_2020_2.csv...
...

============================================================
✓ Pipeline Silver terminé
  Enregistrements traités: 2,456,890
  Destination: data/lake/silver/weather
============================================================
```

**Durée estimée:** 2-5 minutes

**Sortie fichiers:**
```
data/lake/silver/weather/
├── year=2020/
│   ├── month=01/
│   │   ├── city=Paris/
│   │   │   └── weather_data_2020_01_Paris.parquet
│   │   ├── city=Lyon/
│   │   │   └── weather_data_2020_01_Lyon.parquet
│   │   └── ...
│   ├── month=02/
│   └── ...
├── year=2021/
└── ...
```

---

### Étape 4: Agrégation → Gold

Génère les tables d'indicateurs et détecte les événements extrêmes.

```bash
python gold_aggregator.py
```

**Opérations:**
- Agrégation quotidienne (min, max, mean par ville)
- Détection jours extrêmes (canicule, froid, pluie, vent, brouillard)
- Calcul corrélations (météo ↔ visibilité par saison)
- Résumés annuels par ville
- Sauvegarde tables Gold

**Sortie attendue:**
```
============================================================
Agrégation Silver → Gold (indicateurs)
============================================================
Chargement données Silver...
Chargé 2,456,890 enregistrements

Agrégation quotidienne: 17,850 jours-villes
Détecté 1,234 événements extrêmes

✓ Table quotidienne: gold/weather/weather_daily.parquet (17,850 lignes)
✓ Jours extrêmes: gold/weather/weather_extreme_days.parquet (1,234 événements)
✓ Corrélations: gold/weather/weather_correlations.csv
✓ Résumé annuel: gold/weather/city_summary_annual.csv

Top 10 événements extrêmes:
  heat_wave: 342 occurrences
  strong_wind: 289 occurrences
  heavy_rain: 234 occurrences
  low_visibility: 156 occurrences
  cold_wave: 123 occurrences
  ...

============================================================
✓ Pipeline Gold terminé
  Jours analysés: 17,850
  Événements extrêmes: 1,234
  Destination: data/lake/gold/weather
============================================================
```

**Durée estimée:** 1-2 minutes

**Sortie fichiers:**
```
data/lake/gold/weather/
├── weather_daily.parquet         # Données quotidiennes (17,850 lignes)
├── weather_extreme_days.parquet  # Événements extrêmes (1,234 lignes)
├── weather_correlations.csv      # Corrélations
├── city_summary_annual.csv       # Résumé annuel
└── visualizations/
    ├── seasonal_temperature.png
    ├── extreme_events_distribution.png
    └── precipitation_heatmap.png
```

---

### Étape 5: Visualisations

Génère des graphiques pour les résultats.

```bash
python visualizer.py
```

**Graphiques générés:**
1. **seasonal_temperature.png** - Courbes saisonnières de température
2. **extreme_events_distribution.png** - Histogramme événements extrêmes
3. **precipitation_heatmap.png** - Heatmap précipitations par ville

**Sortie attendue:**
```
============================================================
Génération des visualisations
============================================================
✓ Graphique sauvegardé: data/lake/gold/weather/visualizations/seasonal_temperature.png
✓ Graphique sauvegardé: data/lake/gold/weather/visualizations/extreme_events_distribution.png
✓ Graphique sauvegardé: data/lake/gold/weather/visualizations/precipitation_heatmap.png

✓ Visualisations sauvegardées dans data/lake/gold/weather/visualizations/
```

---

## ⚡ Exécution rapide (all-in-one)

```bash
cd src

# Setup
python setup_datalake.py

# Pipeline complet
python downloader.py --workers 4 && \
python silver_processor.py && \
python gold_aggregator.py && \
python visualizer.py

echo "✓ Pipeline complet terminé!"
```

**Durée totale:** ~5-10 minutes (premiers téléchargement + traitement)

---

## 📊 Utiliser les résultats

### Charger les données Gold en Python

```python
import pandas as pd

# Données quotidiennes
daily = pd.read_parquet('data/lake/gold/weather/weather_daily.parquet')
print(f"Données quotidiennes: {len(daily)} lignes")

# Événements extrêmes
extreme = pd.read_parquet('data/lake/gold/weather/weather_extreme_days.parquet')
print(f"Événements extrêmes: {len(extreme)} occurrences")

# Corrélations
corr = pd.read_csv('data/lake/gold/weather/weather_correlations.csv')
print(corr)
```

### Exemples requêtes

```python
# 1. Température moyenne à Paris en 2023
paris_2023 = daily[
    (daily['city'] == 'Paris') & 
    (daily['date'].dt.year == 2023)
]
avg_temp = paris_2023['temperature_mean'].mean()
print(f"Temp moyenne Paris 2023: {avg_temp:.1f}°C")

# 2. Canicules par ville
heat_waves = extreme[extreme['event_type'] == 'heat_wave']
heat_by_city = heat_waves.groupby('city').size().sort_values(ascending=False)
print(heat_by_city)

# 3. Jours de pluie par mois (Lyon)
daily['date'] = pd.to_datetime(daily['date'])
lyon_rain = daily[(daily['city'] == 'Lyon') & (daily['precipitation_sum'] > 1.0)]
print(f"Jours de pluie à Lyon: {len(lyon_rain)}")
```

---

## 🔍 Dépannage

### Problème: Pas de fichiers téléchargés
**Cause:** Connexion réseau ou serveur NOAA indisponible  
**Solution:** Vérifier la connexion, réessayer avec `--workers 2`

### Problème: Fichiers Bronze mais pas de Silver
**Cause:** Erreur lors du parsing NOAA  
**Solution:** Vérifier les logs (`logs/silver_processor.log`)

### Problème: Erreur "ModuleNotFoundError"
**Cause:** Dépendances manquantes  
**Solution:** `pip install -r requirements.txt`

### Problème: Slow processing
**Cause:** Disque lent ou RAM insuffisante  
**Solution:** Réduire `--workers` ou traiter année par année

---

## 📈 Performances

| Étape | Temps | Entrée | Sortie |
|-------|-------|--------|--------|
| Download | 30-60s | URLs NOAA | ~580 fichiers (~200 MB) |
| Silver | 2-5m | 580 CSV | ~2.5M enregistrements |
| Gold | 1-2m | Silver Parquet | Indicateurs |
| Visualize | 30s | Gold Tables | 3 PNG graphiques |
| **TOTAL** | **~5-10min** | - | Indicateurs complets |

**Disque requis:**
- Bronze: ~200 MB (données brutes)
- Silver: ~150 MB (données nettoyées, Parquet)
- Gold: ~10 MB (agrégations)
- **Total:** ~360 MB

---

## 📞 Support

Pour questions ou problèmes:
1. Consulter les logs: `logs/*.log`
2. Vérifier la documentation: `docs/README_data_lake_meteo.md`
3. Valider l'installation: `pip list`

---

**Dernière mise à jour:** 2025-06-18  
**Version:** 1.0  
**Status:** 🟢 Production
