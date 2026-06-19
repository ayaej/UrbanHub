"""UrbanHub – Smart City Big Data Platform Backend.

FastAPI service exposant les données Smart City :
- Weather (simulé / Batch)
- Mobility / CityBikes (données réelles depuis PostgreSQL)
- Pollution (IoT simulé)
- Cross analytics & insights
- Architecture flow definition

Migré de MongoDB vers PostgreSQL pour utiliser les vraies données CityBikes
ingérées par citybikes_ingest.py
"""
from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import asyncpg
import os
import math
import random
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.environ.get("POSTGRES_DB", "urbanhub")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "urbanhub")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "urbanhub")

app = FastAPI(title="UrbanHub API", version="2.0.0")
api_router = APIRouter(prefix="/api")

# Pool de connexions PostgreSQL (initialisé au démarrage)
_pool: asyncpg.Pool = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            min_size=2,
            max_size=10,
        )
    return _pool


@app.on_event("startup")
async def startup():
    await get_pool()
    logger.info("PostgreSQL pool connecté sur %s:%s/%s", POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB)


@app.on_event("shutdown")
async def shutdown():
    if _pool:
        await _pool.close()


# ----------------------------------------------------------------------------
# Reference data
# ----------------------------------------------------------------------------
FRENCH_CITIES = [
    {"name": "Paris", "lat": 48.8566, "lng": 2.3522, "pop": 2148000},
    {"name": "Lyon", "lat": 45.7640, "lng": 4.8357, "pop": 522000},
    {"name": "Marseille", "lat": 43.2965, "lng": 5.3698, "pop": 870000},
    {"name": "Toulouse", "lat": 43.6047, "lng": 1.4442, "pop": 493000},
    {"name": "Nice", "lat": 43.7102, "lng": 7.2620, "pop": 342000},
    {"name": "Nantes", "lat": 47.2184, "lng": -1.5536, "pop": 318000},
    {"name": "Strasbourg", "lat": 48.5734, "lng": 7.7521, "pop": 280000},
    {"name": "Montpellier", "lat": 43.6108, "lng": 3.8767, "pop": 295000},
    {"name": "Bordeaux", "lat": 44.8378, "lng": -0.5792, "pop": 260000},
    {"name": "Lille", "lat": 50.6292, "lng": 3.0573, "pop": 235000},
    {"name": "Rennes", "lat": 48.1173, "lng": -1.6778, "pop": 217000},
    {"name": "Reims", "lat": 49.2583, "lng": 4.0317, "pop": 183000},
]


def _seed(key: str) -> random.Random:
    rng = random.Random()
    rng.seed(hash(key) & 0xFFFFFFFF)
    return rng


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================================
# WEATHER (Batch – simulé)
# ============================================================================
@api_router.get("/weather/timeseries")
async def weather_timeseries(years: int = 5):
    rng = _seed(f"weather-ts-{years}")
    out = []
    months = years * 12
    base = _now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    for i in range(months):
        d = base - timedelta(days=30 * (months - i - 1))
        season = math.sin((d.month - 4) / 12 * 2 * math.pi)
        temp = 13 + season * 9 + rng.uniform(-1.5, 1.5)
        pressure = 1013 + rng.uniform(-7, 7)
        wind = 12 + abs(math.cos((d.month - 1) / 12 * 2 * math.pi)) * 8 + rng.uniform(-2, 4)
        precip = max(0, 55 - season * 25 + rng.uniform(-15, 25))
        out.append({
            "date": d.strftime("%Y-%m"),
            "temp": round(temp, 1),
            "pressure": round(pressure, 1),
            "wind": round(wind, 1),
            "precip": round(precip, 1),
        })
    return {"source": "batch", "interval": "monthly", "data": out}


@api_router.get("/weather/cities")
async def weather_cities():
    rng = _seed(f"weather-cities-{_now().strftime('%Y-%m-%d-%H')}")
    out = []
    month = _now().month
    season = math.sin((month - 4) / 12 * 2 * math.pi)
    for c in FRENCH_CITIES:
        temp = 13 + season * 9 + rng.uniform(-3, 3) + (43.6 - c["lat"]) * 0.4
        wind = 10 + rng.uniform(0, 18)
        humidity = rng.randint(40, 90)
        conditions = rng.choice(["clear", "cloudy", "rain", "storm", "fog"])
        anomaly = abs(rng.uniform(-3, 3)) > 2.5
        out.append({
            **c,
            "temp": round(temp, 1),
            "wind": round(wind, 1),
            "humidity": humidity,
            "condition": conditions,
            "anomaly": anomaly,
        })
    return {"source": "batch", "data": out}


@api_router.get("/weather/alerts")
async def weather_alerts():
    rng = _seed(f"weather-alerts-{_now().strftime('%Y-%m-%d-%H')}")
    types = [
        ("Vague de chaleur", "warning"),
        ("Tempête côtière", "critical"),
        ("Gel intense", "warning"),
        ("Précipitations record", "critical"),
        ("Vent violent", "warning"),
    ]
    out = []
    for _ in range(rng.randint(3, 5)):
        t, sev = rng.choice(types)
        city = rng.choice(FRENCH_CITIES)["name"]
        out.append({
            "title": t,
            "city": city,
            "severity": sev,
            "ts": (_now() - timedelta(hours=rng.randint(0, 23))).isoformat(),
        })
    return {"data": out}


# ============================================================================
# MOBILITY – données réelles depuis PostgreSQL (CityBikes)
# ============================================================================
@api_router.get("/mobility/stations")
async def mobility_stations(limit: int = 240, network: Optional[str] = None):
    """Stations depuis citybikes_station_last_status (données live)."""
    pool = await get_pool()
    try:
        if network:
            rows = await pool.fetch(
                """
                SELECT station_id AS id, station_name AS name, network,
                       latitude AS lat, longitude AS lng,
                       bikes_available AS bikes,
                       free_slots AS slots,
                       bikes_available + free_slots AS capacity,
                       event_timestamp AS last_update
                FROM citybikes_station_last_status
                WHERE network ILIKE $1
                ORDER BY updated_at DESC
                LIMIT $2
                """,
                f"%{network}%", limit
            )
        else:
            rows = await pool.fetch(
                """
                SELECT station_id AS id, station_name AS name, network,
                       latitude AS lat, longitude AS lng,
                       bikes_available AS bikes,
                       free_slots AS slots,
                       bikes_available + free_slots AS capacity,
                       event_timestamp AS last_update
                FROM citybikes_station_last_status
                ORDER BY updated_at DESC
                LIMIT $1
                """,
                limit
            )
        data = [dict(r) for r in rows]
        return {"source": "postgresql", "count": len(data), "data": data}
    except Exception as e:
        logger.error("Erreur mobility/stations: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/mobility/timeline")
async def mobility_timeline():
    """Utilisation horaire des dernières 24h depuis les événements réels."""
    pool = await get_pool()
    try:
        rows = await pool.fetch(
            """
            SELECT
                date_trunc('hour', event_timestamp) AS hour,
                SUM(bikes_available) AS total_bikes,
                SUM(free_slots) AS total_slots,
                COUNT(DISTINCT station_id) AS active_stations,
                ROUND(AVG(bikes_available::numeric /
                    NULLIF(bikes_available + free_slots, 0)) * 100, 1) AS usage_pct
            FROM citybikes_station_events
            WHERE event_timestamp >= NOW() - INTERVAL '24 hours'
            GROUP BY date_trunc('hour', event_timestamp)
            ORDER BY hour
            """
        )
        data = []
        for r in rows:
            data.append({
                "hour": r["hour"].strftime("%Hh") if r["hour"] else None,
                "total_bikes": r["total_bikes"],
                "total_slots": r["total_slots"],
                "active_stations": r["active_stations"],
                "usage_pct": float(r["usage_pct"]) if r["usage_pct"] else None,
            })
        return {"source": "postgresql", "data": data}
    except Exception as e:
        logger.error("Erreur mobility/timeline: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/mobility/critical")
async def mobility_critical():
    """Stations vides ou pleines (état actuel)."""
    pool = await get_pool()
    try:
        rows = await pool.fetch(
            """
            SELECT station_id AS id, station_name AS name, network,
                   latitude AS lat, longitude AS lng,
                   bikes_available AS bikes,
                   free_slots AS slots,
                   CASE
                     WHEN bikes_available = 0 THEN 'empty'
                     WHEN free_slots = 0 THEN 'full'
                     ELSE 'ok'
                   END AS status,
                   event_timestamp AS last_update
            FROM citybikes_station_last_status
            WHERE bikes_available = 0 OR free_slots = 0
            ORDER BY updated_at DESC
            LIMIT 50
            """
        )
        data = [dict(r) for r in rows]
        return {"source": "postgresql", "data": data}
    except Exception as e:
        logger.error("Erreur mobility/critical: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/mobility/networks")
async def mobility_networks():
    """Liste des réseaux disponibles dans la base."""
    pool = await get_pool()
    try:
        rows = await pool.fetch(
            """
            SELECT network,
                   COUNT(DISTINCT station_id) AS station_count,
                   SUM(bikes_available) AS total_bikes,
                   SUM(free_slots) AS total_slots,
                   MAX(updated_at) AS last_update
            FROM citybikes_station_last_status
            GROUP BY network
            ORDER BY station_count DESC
            """
        )
        data = [dict(r) for r in rows]
        return {"source": "postgresql", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/mobility/history/{station_id}")
async def mobility_station_history(station_id: str, hours: int = 24):
    """Historique d'une station sur les dernières N heures."""
    pool = await get_pool()
    try:
        rows = await pool.fetch(
            """
            SELECT
                event_timestamp AS ts,
                bikes_available AS bikes,
                free_slots AS slots
            FROM citybikes_station_events
            WHERE station_id = $1
              AND event_timestamp >= NOW() - ($2 || ' hours')::interval
            ORDER BY event_timestamp
            """,
            station_id, str(hours)
        )
        data = [
            {
                "ts": r["ts"].isoformat(),
                "bikes": r["bikes"],
                "slots": r["slots"],
            }
            for r in rows
        ]
        return {"source": "postgresql", "station_id": station_id, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# POLLUTION (IoT – simulé)
# ============================================================================
POLLUTANTS = ["pm25", "pm10", "no2", "o3", "co"]
POLLUTANT_BASES = {"pm25": 15, "pm10": 25, "no2": 30, "o3": 55, "co": 0.6}


def _pollution_value(rng, pollutant):
    base = POLLUTANT_BASES.get(pollutant, 20)
    return round(base + rng.uniform(-base * 0.4, base * 0.7), 2)


@api_router.get("/pollution/sensors")
async def pollution_sensors():
    rng = _seed(f"pollution-{_now().strftime('%Y-%m-%d-%H')}")
    out = []
    for c in FRENCH_CITIES:
        readings = {p: _pollution_value(rng, p) for p in POLLUTANTS}
        aqi = int(readings["pm25"] * 2 + readings["pm10"] + readings["no2"] * 0.8 + readings["o3"] * 0.3)
        status = "good" if aqi < 50 else ("moderate" if aqi < 100 else "critical")
        out.append({**c, **readings, "aqi": aqi, "status": status})
    return {"source": "iot", "data": out}


@api_router.get("/pollution/timeline")
async def pollution_timeline(city: Optional[str] = None, hours: int = 48):
    rng = _seed(f"pollution-tl-{city}-{hours}")
    out = []
    base = _now().replace(minute=0, second=0, microsecond=0)
    for i in range(hours):
        d = base - timedelta(hours=hours - i - 1)
        circadian = math.sin((d.hour - 6) / 24 * 2 * math.pi)
        out.append({
            "ts": d.strftime("%d/%m %Hh"),
            "pm25": round(14 + circadian * 6 + rng.uniform(-2, 4), 1),
            "pm10": round(22 + circadian * 8 + rng.uniform(-3, 6), 1),
            "no2": round(28 + circadian * 10 + rng.uniform(-4, 7), 1),
            "o3": round(55 - circadian * 12 + rng.uniform(-5, 5), 1),
        })
    return {"data": out, "city": city or "France"}


@api_router.get("/pollution/comparison")
async def pollution_comparison():
    rng = _seed(f"pollution-cmp-{_now().strftime('%Y-%m-%d')}")
    out = []
    for c in FRENCH_CITIES:
        out.append({
            "city": c["name"],
            "pm25": _pollution_value(rng, "pm25"),
            "pm10": _pollution_value(rng, "pm10"),
            "no2": _pollution_value(rng, "no2"),
        })
    return {"data": out}


# ============================================================================
# ANALYTICS – KPIs mixant données réelles et simulées
# ============================================================================
@api_router.get("/analytics/kpis")
async def analytics_kpis():
    pool = await get_pool()
    rng = _seed(f"kpis-{_now().strftime('%Y-%m-%d-%H')}")

    # KPIs réels depuis Postgres
    try:
        row = await pool.fetchrow(
            """
            SELECT
                SUM(bikes_available) AS total_bikes,
                SUM(free_slots) AS total_slots,
                COUNT(*) AS total_stations,
                COUNT(*) FILTER (WHERE bikes_available = 0 OR free_slots = 0) AS critical_count,
                (SELECT COUNT(*) FROM citybikes_station_events
                 WHERE event_timestamp >= NOW() - INTERVAL '24 hours') AS events_24h
            FROM citybikes_station_last_status
            """
        )
        total_bikes = int(row["total_bikes"] or 0)
        total_slots = int(row["total_slots"] or 0)
        total_capacity = total_bikes + total_slots
        usage_pct = round(total_bikes / total_capacity * 100, 1) if total_capacity > 0 else 0
        critical_count = int(row["critical_count"] or 0)
        events_24h = int(row["events_24h"] or 0)
    except Exception:
        total_bikes, total_slots, usage_pct, critical_count, events_24h = 0, 0, 0, 0, 0

    return {
        "data": [
            {"key": "total_bikes", "label": "Vélos disponibles (live)", "value": total_bikes, "delta": None, "unit": ""},
            {"key": "total_slots", "label": "Places libres (live)", "value": total_slots, "delta": None, "unit": ""},
            {"key": "usage_pct", "label": "Taux d'utilisation", "value": usage_pct, "delta": None, "unit": "%"},
            {"key": "stations_critical", "label": "Stations critiques", "value": critical_count, "delta": None, "unit": ""},
            {"key": "events_24h", "label": "Événements ingérés (24h)", "value": events_24h, "delta": None, "unit": ""},
            {"key": "avg_pollution", "label": "Pollution moyenne (AQI)", "value": 62 + rng.randint(-5, 5), "delta": -2.1, "unit": ""},
        ]
    }


@api_router.get("/analytics/correlation")
async def analytics_correlation():
    rng = _seed("correlation")
    weather_pollution = []
    weather_mobility = []
    for _ in range(60):
        t = rng.uniform(-5, 35)
        wp_y = max(5, 60 - t * 0.6 + rng.uniform(-10, 12))
        weather_pollution.append({"temp": round(t, 1), "pollution": round(wp_y, 1)})
        precip = rng.uniform(0, 30)
        trips = max(800, 7500 - precip * 120 + rng.uniform(-600, 600))
        weather_mobility.append({"precip": round(precip, 1), "trips": int(trips)})
    return {"weather_pollution": weather_pollution, "weather_mobility": weather_mobility}


@api_router.get("/analytics/insights")
async def analytics_insights():
    insights = [
        {"title": "Pic de pollution corrélé à la canicule", "summary": "L'O3 augmente de +28% lorsque la température dépasse 30°C sur Paris.", "tag": "Cross", "severity": "warning"},
        {"title": "Stations Vélib saturées en heure de pointe", "summary": "14 stations atteignent 100% d'occupation entre 8h et 9h chaque jour ouvré.", "tag": "Streaming", "severity": "critical"},
        {"title": "Anomalie capteur PM2.5 Marseille-Sud", "summary": "Variance anormale détectée sur 6 capteurs - investigation IoT recommandée.", "tag": "IoT", "severity": "warning"},
        {"title": "Qualité air optimale week-end", "summary": "Réduction de 18% du NO2 le dimanche - corrélation avec baisse du trafic.", "tag": "Batch", "severity": "good"},
        {"title": "Précipitations réduisent l'usage vélo de 35%", "summary": "Modèle linéaire (R²=0.78) confirme l'impact pluie sur la mobilité douce.", "tag": "Cross", "severity": "good"},
        {"title": "Croissance trafic data 8.4% MoM", "summary": "Volume ingéré dans MinIO Data Lake progresse régulièrement - capacité OK 6 mois.", "tag": "Batch", "severity": "good"},
    ]
    return {"data": insights}


# ============================================================================
# ARCHITECTURE
# ============================================================================
@api_router.get("/architecture/flows")
async def architecture_flows():
    return {
        "nodes": [
            {"id": "src-weather", "label": "NOAA / Météo APIs", "type": "source", "flow": "batch"},
            {"id": "src-bikes", "label": "CityBikes / Vélib", "type": "source", "flow": "streaming"},
            {"id": "src-iot", "label": "Capteurs IoT MQTT", "type": "source", "flow": "iot"},
            {"id": "python", "label": "Python + Pandas / PyArrow", "type": "compute"},
            {"id": "kafka", "label": "Kafka Broker", "type": "stream", "flow": "streaming"},
            {"id": "mqtt", "label": "MQTT Broker", "type": "stream", "flow": "iot"},
            {"id": "n8n", "label": "n8n Orchestrator", "type": "orchestrator"},
            {"id": "minio", "label": "MinIO Data Lake", "type": "storage", "layers": ["Bronze", "Silver", "Gold"]},
            {"id": "postgres", "label": "PostgreSQL", "type": "warehouse"},
            {"id": "grafana", "label": "Grafana BI", "type": "consumer"},
            {"id": "urbanhub", "label": "UrbanHub Frontend", "type": "consumer"},
        ],
        "edges": [
            {"from": "src-weather", "to": "python", "flow": "batch"},
            {"from": "src-bikes", "to": "kafka", "flow": "streaming"},
            {"from": "src-iot", "to": "mqtt", "flow": "iot"},
            {"from": "kafka", "to": "n8n", "flow": "streaming"},
            {"from": "mqtt", "to": "n8n", "flow": "iot"},
            {"from": "python", "to": "n8n", "flow": "batch"},
            {"from": "n8n", "to": "minio"},
            {"from": "minio", "to": "postgres"},
            {"from": "postgres", "to": "grafana"},
            {"from": "postgres", "to": "urbanhub"},
        ],
        "data_quality": {
            "completeness": 98.7,
            "freshness_seconds": 12,
            "schema_drift": 0,
            "duplicates_pct": 0.4,
        },
    }


# ============================================================================
# HEALTH
# ============================================================================
@api_router.get("/")
async def root():
    pool = await get_pool()
    try:
        await pool.fetchval("SELECT 1")
        db_status = "ok"
    except Exception:
        db_status = "error"
    return {"app": "UrbanHub", "version": "2.0.0", "status": "ok", "db": db_status}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)