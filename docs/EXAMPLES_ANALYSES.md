# 📊 Exemples d'utilisation avancée - UrbanHub Gold Data

👉 **Besoin de démarrer?** Consultez:
- [../INDEX.md](../INDEX.md) - Navigation complète
- [../START.md](../START.md) - Démarrage rapide
- [../README.md](../README.md) - Vue d'ensemble

---

```python
import pandas as pd
import numpy as np
from pathlib import Path

# ============================================
# 1. CHARGER LES DONNÉES GOLD
# ============================================

daily = pd.read_parquet('data/lake/gold/weather/weather_daily.parquet')
extreme = pd.read_parquet('data/lake/gold/weather/weather_extreme_days.parquet')
corr = pd.read_csv('data/lake/gold/weather/weather_correlations.csv')

print(f"✓ Données quotidiennes: {len(daily):,} lignes")
print(f"✓ Événements extrêmes: {len(extreme):,} lignes")
print(f"✓ Corrélations: {len(corr):,} paires")

# ============================================
# 2. ANALYSES PAR VILLE
# ============================================

# Température moyenne annuelle par ville
annual_temp = daily.groupby('city')['temperature_mean'].agg(['min', 'max', 'mean'])
print("\n📊 Température annuelle par ville (°C):")
print(annual_temp.round(1))

# Jours de canicule par ville
heat_waves = extreme[extreme['event_type'] == 'heat_wave']
heatwave_by_city = heat_waves.groupby('city').size().sort_values(ascending=False)
print("\n🔥 Jours de canicule (T ≥ 30°C) par ville:")
print(heatwave_by_city)

# ============================================
# 3. TENDANCES SAISONNIÈRES
# ============================================

# Température moyenne par saison et ville
seasonal = daily.groupby(['season', 'city'])['temperature_mean'].mean().unstack()
print("\n🌍 Température moyenne par saison (°C):")
print(seasonal.round(1))

# Précipitations annuelles par saison
precip_seasonal = daily.groupby(['season', 'city'])['precipitation_sum'].sum().unstack()
print("\n💧 Précipitations annuelles par saison (mm):")
print(precip_seasonal.round(0))

# ============================================
# 4. CORRÉLATIONS MÉTÉO-VISIBILITÉ
# ============================================

print("\n📈 Corrélations Température-Visibilité par saison:")
temp_vis = corr[corr['pair'].str.contains('temp_vis')]
print(temp_vis.to_string(index=False))

print("\n📈 Corrélations Précipitations-Visibilité par saison:")
precip_vis = corr[corr['pair'].str.contains('precip_vis')]
print(precip_vis.to_string(index=False))

# ============================================
# 5. ÉVÉNEMENTS MÉTÉOROLOGIQUES EXTRÊMES
# ============================================

# Distribution des événements
print("\n⚠️  Distribution des événements extrêmes:")
print(extreme['event_type'].value_counts())

# Top 10 jours extrêmes (Tmax)
print("\n🔴 Top 10 jours chauds:")
hottest = extreme[extreme['event_type'] == 'heat_wave'].nlargest(10, 'temperature_max')
for _, row in hottest.iterrows():
    print(f"  {row['date']} | {row['city']:12s} | {row['temperature_max']:.1f}°C")

# Jours froids
print("\n🔵 Jours froids les plus extrêmes:")
coldest = extreme[extreme['event_type'] == 'cold_wave'].nsmallest(5, 'temperature_max')
for _, row in coldest.iterrows():
    print(f"  {row['date']} | {row['city']:12s} | {row['temperature_max']:.1f}°C")

# ============================================
# 6. PATTERNS RÉGIONAUX
# ============================================

# Moyenne par mois et région (cluster de villes)
daily['date'] = pd.to_datetime(daily['date'])
daily['month'] = daily['date'].dt.month

print("\n📅 Température moyenne par mois (top 3 villes froides/chaudes):")
monthly_temp = daily.groupby(['month', 'city'])['temperature_mean'].mean()
for month in range(1, 13):
    temps = monthly_temp[month]
    coldest_city = temps.idxmin()
    hottest_city = temps.idxmax()
    print(f"  Mois {month:2d}: Froide={coldest_city:12s} ({temps.min():5.1f}°C) | "
          f"Chaude={hottest_city:12s} ({temps.max():5.1f}°C)")

# ============================================
# 7. REQUÊTES MÉTIER
# ============================================

# Q1: Combien de jours avec visibilité < 1km à Marseille?
low_vis = daily[(daily['city'] == 'Marseille') & (daily['visibility_min'] < 1.0)]
print(f"\n❓ Jours brumeux à Marseille: {len(low_vis)} jours")

# Q2: Précipitations totales par ville (années 2020-2025)
total_rain = daily.groupby('city')['precipitation_sum'].sum().sort_values(ascending=False)
print("\n❓ Précipitations totales (mm):")
print(total_rain.round(0))

# Q3: Année la plus chaude
daily['year'] = daily['date'].dt.year
yearly_avg = daily.groupby('year')['temperature_mean'].mean()
warmest_year = yearly_avg.idxmax()
print(f"\n❓ Année la plus chaude: {int(warmest_year)} ({yearly_avg[warmest_year]:.1f}°C)")

# ============================================
# 8. EXPORT RAPPORTS
# ============================================

# Rapport texte
report_file = Path('data/lake/gold/weather/RAPPORT_METEOROLOGIE.txt')
with open(report_file, 'w') as f:
    f.write("=" * 60 + "\n")
    f.write("RAPPORT MÉTÉOROLOGIQUE URBAIN - FRANCE 2020-2025\n")
    f.write("=" * 60 + "\n\n")
    
    f.write("1. RÉSUMÉ PAR VILLE\n")
    f.write("-" * 60 + "\n")
    for city in daily['city'].unique():
        city_data = daily[daily['city'] == city]
        f.write(f"\n{city}:\n")
        f.write(f"  - Jours analysés: {len(city_data)}\n")
        f.write(f"  - Temp moyenne: {city_data['temperature_mean'].mean():.1f}°C\n")
        f.write(f"  - Pluie totale: {city_data['precipitation_sum'].sum():.1f} mm\n")
        f.write(f"  - Jours extrêmes: {len(extreme[extreme['city'] == city])}\n")
    
    f.write("\n\n2. ÉVÉNEMENTS EXTRÊMES\n")
    f.write("-" * 60 + "\n")
    f.write(extreme.to_string())

print(f"\n✓ Rapport généré: {report_file}")
```

---

## Cas d'usage - Décideurs publics

### 🏥 Santé publique
```python
# Identifier périodes à risque (chaleur, brouillard)
heat_waves_by_year = extreme[extreme['event_type'] == 'heat_wave'].groupby('year').size()
print("Plan de prévention canicule:", heat_waves_by_year.to_dict())
```

### 🚗 Mobilité urbaine
```python
# Visibilité faible → prévention accidents
low_vis_days = daily[daily['visibility_min'] < 0.5]
print(f"Jours à risque routier: {len(low_vis_days)}")
```

### ⚡ Énergie
```python
# Température extrême → pics consommation
temp_range = daily['temperature_mean'].max() - daily['temperature_mean'].min()
print(f"Écart thermique annuel: {temp_range:.1f}°C")
```

### 🌿 Environnement
```python
# Tendances de précipitations
precip_trend = daily.groupby('year')['precipitation_sum'].sum()
print("Tendance pluviométrique:", precip_trend.to_dict())
```

---

**Version:** 1.0  
**Dernière mise à jour:** 2026-06-18
