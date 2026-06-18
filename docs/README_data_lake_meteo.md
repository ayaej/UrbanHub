# 📊 Documentation Data Lake - UrbanHub

👉 **Besoin de démarrer?** Consultez:
- [../INDEX.md](../INDEX.md) - Navigation complète
- [../START.md](../START.md) - Démarrage rapide
- [../QUICKSTART.md](../QUICKSTART.md) - Guide complet

---

## 📁 Structure du Data Lake

Un **Data Lake** est un repository centralisé stockant les données brutes et transformées en couches (Bronze → Silver → Gold).

### Vue d'ensemble

```
data/lake/
├── bronze/                          # Données brutes NOAA
│   └── weather/
│       └── noaa/
│           └── year=YYYY/
│               └── station=STATION_ID/
│                   ├── data_YYYY_1.csv
│                   ├── data_YYYY_2.csv
│                   └── ...
│
├── silver/                          # Données nettoyées & harmonisées
│   └── weather/
│       └── year=YYYY/
│           └── month=MM/
│               └── city=CITY_NAME/
│                   ├── weather_data_YYYY_MM_CITY.parquet
│                   └── ...
│
└── gold/                            # Tables d'indicateurs & agrégation
    └── weather/
        ├── weather_daily.parquet    # Agrégation quotidienne
        ├── weather_extreme_days.parquet  # Événements extrêmes
        ├── weather_correlations.csv # Corrélations
        ├── city_summary_annual.csv  # Résumé annuel par ville
        └── visualizations/          # Graphiques
            ├── seasonal_temperature.png
            ├── extreme_events_distribution.png
            └── precipitation_heatmap.png
```

---

## 🥉 COUCHE BRONZE - Données Brutes

### Objectif
- Stocker les fichiers originaux NOAA sans modification
- Traçabilité complète (source, date, qualité)
- Format partitionné pour scalabilité

### Format
- **Type** : CSV (format NOAA standard)
- **Compression** : Aucune (données brutes)
- **Partitionnement** : Par année et station
- **Rétention** : Permanente

### Schéma (exemple NOAA)
```
STATION | DATE | TMP | WND | VIS | PCP | SLP | ...
--------|------|-----|-----|-----|-----|-----|-----
LFPG    | 2020-01-01T00:00:00 | 256 | 090,0351,4 | 10000,1 | ...
```

### Variables brutes NOAA
- `STATION` : ID station (ex: LFPG)
- `DATE` : Horodatage (ISO 8601)
- `TMP` : Température (°C × 10)
- `WND` : Vent (direction,vitesse,qualité)
- `VIS` : Visibilité (décimètres)
- `PCP` : Précipitations (pouces × 100)
- `SLP` : Pression (hPa × 10)

### Nettoyage
- ❌ Pas de transformation
- ✓ Vérification intégrité fichiers
- ✓ Log des téléchargements

---

## 🥈 COUCHE SILVER - Données Harmonisées

### Objectif
- Données propres prêtes pour analyse
- Unités standards & timestamps normalisés
- Gestion valeurs manquantes
- Format optimisé (Parquet)

### Format
- **Type** : Parquet (columnar, compressé)
- **Compression** : Snappy
- **Partitionnement** : Année, mois, ville
- **Rétention** : Longue (source de vérité)

### Schéma Silver
```
station_id | timestamp | temperature | wind_speed | wind_direction | pressure | precipitation | visibility | city | year | month | day | hour | season
-----------|-----------|-------------|------------|----------------|----------|---------------|-----------|------|------|-------|-----|------|-------
LFPG       | 2020-01-01T00:00:00Z | 2.5 | 3.2 | 90 | 1013.2 | 0.0 | 10.0 | Paris | 2020 | 1 | 1 | 0 | winter
```

### Transformations appliquées
| Variable | Input | Traitement | Output |
|----------|-------|-----------|--------|
| Température | °C × 10 | ÷ 10 | °C |
| Vent (vitesse) | m/s × 10 | ÷ 10 | m/s |
| Vent (direction) | degrés | Extraction | 0-360° |
| Visibilité | décimètres | ÷ 100 | km |
| Précipitations | pouces × 100 | × 25.4 | mm |
| Pression | hPa × 10 | ÷ 10 | hPa |
| Timestamp | YYYY-MM-DDTHH:MM:SS | ISO 8601 + Z | UTC |

### Gestion valeurs manquantes
1. **Détection** : Comptage par variable
2. **Stratégie** :
   - Forward fill (interpolation temporelle)
   - Médiane par station/mois
   - Suppression si > 50% manquants

### Exemple partitionnement
```
silver/weather/year=2020/month=01/city=Paris/weather_data_2020_01_Paris.parquet
```

---

## 🥇 COUCHE GOLD - Indicateurs & Agrégation

### Objectif
- Tables d'indicateurs pour business intelligence
- Agrégations quotidiennes par ville
- Détection anomalies
- Corrélations météo ↔ visibilité

### Fichiers Gold

#### 1. **weather_daily.parquet**
Agrégation quotidienne par ville
```
date | city | temperature_min | temperature_max | temperature_mean | 
     | wind_speed_max | wind_speed_mean | precipitation_sum | 
     | visibility_min | visibility_mean | season
```

**Exemple:**
```
2020-01-01 | Paris | -2.1 | 5.3 | 1.6 | 8.5 | 4.2 | 2.3 | 0.8 | 5.5 | winter
```

#### 2. **weather_extreme_days.parquet**
Événements météorologiques extrêmes
```
date | city | event_type | temperature_max | wind_speed_max | precipitation_sum | visibility_min
```

**Types d'événements:**
- `heat_wave` : Tmax ≥ 30°C
- `cold_wave` : Tmin ≤ 0°C
- `strong_wind` : Vmax ≥ 10 m/s
- `heavy_rain` : Précip ≥ 10 mm/jour
- `low_visibility` : Vis ≤ 1 km

**Exemple:**
```
2020-08-15 | Paris | heat_wave | 32.1 | 3.2 | 0.0 | 8.5
2020-01-22 | Lyon  | cold_wave | -1.5 | 12.3 | 5.2 | 2.1
```

#### 3. **weather_correlations.csv**
Corrélations entre variables par saison
```
pair | correlation
winter_temp_vis | 0.65
summer_precip_vis | -0.42
...
```

#### 4. **city_summary_annual.csv**
Résumé annuel par ville
```
city | temperature_min | temperature_max | temperature_mean | precipitation_sum | wind_speed_max
Paris | -8.5 | 34.2 | 12.1 | 521.3 | 18.2
```

### Indicateurs clés

#### Par ville & jour:
- Température: min, max, moyenne
- Vent: vitesse max, vitesse moyenne, direction prédominante
- Pluie: total quotidien
- Visibilité: minimale, moyenne
- Saison

#### Événements extrêmes:
- Jours de canicule (T > 30°C)
- Jours froids (T < 0°C)
- Jours venteux (V > 10 m/s)
- Jours pluvieux (P > 10 mm)
- Jours brumeux (Vis < 1 km)

#### Corrélations:
- Température ↔ Visibilité (par saison)
- Précipitations ↔ Visibilité (par saison)

---

## 📊 Exemples d'utilisation

### Requête 1: Canicules à Paris en 2023
```python
extreme_days = pd.read_parquet('gold/weather/weather_extreme_days.parquet')
heat_waves = extreme_days[
    (extreme_days['city'] == 'Paris') & 
    (extreme_days['event_type'] == 'heat_wave') &
    (extreme_days['date'].dt.year == 2023)
]
print(f"Jours de canicule: {len(heat_waves)}")
```

### Requête 2: Température moyenne annuelle par ville
```python
daily = pd.read_parquet('gold/weather/weather_daily.parquet')
annual_temp = daily.groupby('city')['temperature_mean'].mean()
print(annual_temp)
```

### Requête 3: Précipitations par mois (Marseille)
```python
daily['month'] = daily['date'].dt.month
monthly_precip = daily[daily['city'] == 'Marseille'].groupby('month')['precipitation_sum'].sum()
print(monthly_precip)
```

---

## 🔄 Pipeline complet

```
NOAA (Raw files)
     ↓
[downloader.py] 
     ↓
BRONZE (year=YYYY/station=STATION_ID/*.csv)
     ↓
[silver_processor.py] - Nettoyage, harmonisation, partitionnement
     ↓
SILVER (year=YYYY/month=MM/city=CITY/*.parquet)
     ↓
[gold_aggregator.py] - Agrégation quotidienne, extrêmes, corrélations
     ↓
GOLD (weather_daily.parquet, weather_extreme_days.parquet, correlations.csv)
     ↓
[visualizer.py]
     ↓
Graphiques (PNG) + Insights pour décideurs
```

---

## 📈 Qualité & Validation

### Contrôles Bronze
- Intégrité téléchargement (taille, checksum)
- Validation structure (colonnes NOAA)
- Log des erreurs

### Contrôles Silver
- Nombre enregistrements avant/après
- % valeurs manquantes par variable
- Distribution des timestamps
- Statistiques descriptives (min, max, mean)

### Contrôles Gold
- Cohérence agrégation
- Plausibilité des extrêmes
- Corrélations statistiquement valides

---

## 🚀 Maintenance

- **Rétention Bronze** : Permanente (archives)
- **Rétention Silver** : 2+ années (référence)
- **Rétention Gold** : Long terme (reporting)
- **Mise à jour** : Mensuelle (après téléchargement NOAA)
- **Archivage** : Annuel (cold storage)

