# 🏗️ Architecture - UrbanHub Smart City Platform

👉 **Nouveau ici?** Consultez:
- [../README.md](../README.md) - Vue d'ensemble
- [../COMPLETE_GUIDE.md](../COMPLETE_GUIDE.md) - Guide complet (3 options)
- [../HOW_5_TECHNOLOGIES_WORK.md](../HOW_5_TECHNOLOGIES_WORK.md) - Comment les technologies fonctionnent

---

## Composants principaux

```
┌─────────────────────────────────────────────────────────────┐
│                       DATA SOURCES                           │
├─────────────────────────────────────────────────────────────┤
│  NOAA Global Hourly    IoT Sensors    Traffic Flow    Events │
│  (2020-2025)          (Future)        (Future)        (Future)
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                          │
├─────────────────────────────────────────────────────────────┤
│  downloader.py (NOAA)  → Parallel HTTP download             │
│  Error handling & Retry logic                               │
│  Logging & Statistics                                       │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                    BRONZE LAYER (RAW)                       │
├─────────────────────────────────────────────────────────────┤
│  Format: CSV (native NOAA)                                  │
│  Partitioning: year=YYYY/station=STATION_ID                │
│  Size: ~200 MB (2020-2025, 14 stations)                    │
│  Retention: Permanent (archives)                            │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                    PROCESSING LAYER                         │
├─────────────────────────────────────────────────────────────┤
│  silver_processor.py:                                       │
│    - Parse NOAA format                                      │
│    - Unit conversion (°C, m/s, mm, hPa, km)               │
│    - Timestamp normalization (UTC)                         │
│    - Missing value handling                                │
│    - Enrichment (city, season)                             │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                    SILVER LAYER (CLEAN)                    │
├─────────────────────────────────────────────────────────────┤
│  Format: Parquet (columnar, compressed)                    │
│  Partitioning: year/month/city                             │
│  Size: ~150 MB (compressed)                                │
│  Records: ~2.5M hourly observations                        │
│  Retention: Long-term (source of truth)                    │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                    AGGREGATION LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  gold_aggregator.py:                                        │
│    - Daily aggregation (min, max, mean)                     │
│    - Extreme event detection                               │
│    - Correlation analysis                                   │
│    - City summaries                                         │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                     GOLD LAYER (INSIGHTS)                   │
├─────────────────────────────────────────────────────────────┤
│  weather_daily.parquet        → 17,850 daily city records   │
│  weather_extreme_days.parquet → 1,234 extreme events       │
│  weather_correlations.csv     → Statistical correlations   │
│  city_summary_annual.csv      → Annual summary by city     │
│  visualizations/              → Charts (PNG)               │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                  VISUALIZATION & EXPORT                     │
├─────────────────────────────────────────────────────────────┤
│  visualizer.py:                                             │
│    - Seasonal temperature curves                            │
│    - Extreme events distribution                            │
│    - Precipitation heatmap                                  │
│  → PNG reports for decision makers                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Flot de données (Example)

### Étape 1: Download (downloader.py)
```
NOAA Index
  ↓ (List files)
URLs: https://www.ncei.noaa.gov/data/global-hourly/access/2020/LFPG/data_2020_1.csv
  ↓ (Parallel download, 4 workers)
Bronze: data/lake/bronze/weather/noaa/year=2020/station=LFPG/data_2020_1.csv
```

### Étape 2: Silver Processing (silver_processor.py)
```
Input CSV (NOAA Format):
  STATION,DATE,TMP,WND,VIS,PCP,SLP
  LFPG,2020-01-01T00:00:00,256,090,0351,4,10000,1,...

  ↓ Parse & Clean
  - TMP: 256 → 25.6°C (÷10)
  - WND: 090,0351,4 → wind_direction=90°, wind_speed=3.51 m/s
  - VIS: 10000 → 100 km
  - PCP: 0 → 0 mm
  - SLP: 10200 → 1020 hPa
  - Timestamp: 2020-01-01T00:00:00Z

Output Parquet (Silver):
  station_id | timestamp | temperature | wind_speed | ... | city | season
  LFPG       | 2020-01-01T00:00:00Z | 25.6 | 3.51 | ... | Paris | winter

  ↓ Partitioned & saved
Silver: data/lake/silver/weather/year=2020/month=01/city=Paris/weather_data_2020_01_Paris.parquet
```

### Étape 3: Gold Aggregation (gold_aggregator.py)
```
Input: 744 hourly records (Jan 2020, Paris)

  ↓ Daily aggregation
  - temperature_min: 2.1°C
  - temperature_max: 8.5°C
  - temperature_mean: 5.3°C
  - precipitation_sum: 2.3 mm
  - ...

Output:
  date | city | temperature_min | temperature_max | temperature_mean | season
  2020-01-01 | Paris | 2.1 | 8.5 | 5.3 | winter

  ↓ Extreme detection
  Is 8.5°C extreme? No (< 30°C heat_wave threshold)

Gold: data/lake/gold/weather/weather_daily.parquet
      data/lake/gold/weather/weather_extreme_days.parquet
```

---

## Configuration technologique

### Languages & Frameworks
- **Python 3.8+** : Core language
- **Pandas** : Data manipulation
- **NumPy** : Numerical operations
- **Requests** : HTTP download
- **PyArrow** : Parquet format
- **Matplotlib/Seaborn** : Visualization
- **PySpark** : Optional (future scaling)

### Data Formats
- **Bronze** : CSV (native NOAA)
- **Silver** : Parquet (columnar, compressed)
- **Gold** : Parquet + CSV

### Storage
- **File System** : Local or S3
- **Optional** : MinIO (S3-compatible)
- **Partitioning** : Year/Month/City (Hive-style)

### Parallelization
- **Download** : ThreadPoolExecutor (4-8 workers)
- **Processing** : Pandas groupby + parallel I/O
- **Future** : PySpark for distributed computing

---

## Scalabilité

### Current (2020-2025, 14 stations)
- Data volume: ~360 MB
- Processing time: ~5-10 min
- Memory: <2 GB

### Future scaling (All France, Real-time)
- Stations: 100+
- Data volume: ~1-5 GB/year
- Processing: PySpark cluster
- Storage: S3 + Data Warehouse
- Frequency: Daily ingestion
- Latency: Real-time streams (Kafka)

---

## Intégrations futures

### Part 2: IoT Sensors (Traffic, Pollution)
- Real-time stream ingestion (Kafka)
- Stream processing (Spark Streaming)
- Gold tables: traffic flow, pollution alerts

### Part 3: Urban Events
- Event indexing (location, type, date)
- Correlation with weather/traffic
- Gold table: incident patterns

### Part 4: BI & Dashboards
- Business Intelligence layer
- Tableau/PowerBI dashboards
- Real-time alerts
- Public API endpoints

---

## SLA & Reliability

| Component | SLA | Reliability |
|-----------|-----|-------------|
| Download | Best effort | Retry x3 + logs |
| Processing | Daily | Partition-level recovery |
| Storage | Permanent | Local filesystem (future: S3) |
| Validation | 100% checks | Data quality tests |

---

**Architecture Version:** 1.0  
**Last Updated:** 2026-06-18  
**Maintainer:** UrbanHub Project Team
