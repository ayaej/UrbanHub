"""Backend tests for UrbanHub Smart City API.

Tests all /api endpoints (weather, mobility, pollution, analytics, architecture)
based on the contract described in the review request.
"""
import os
import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    # Read frontend/.env directly when env var is not in shell
    from pathlib import Path
    env_path = Path(__file__).resolve().parents[2] / "frontend" / ".env"
    for line in env_path.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().strip('"').strip("'")
            break
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------------------------------------------------------------------------
# Health / Root
# ---------------------------------------------------------------------------
class TestRoot:
    def test_root_info(self, session):
        r = session.get(f"{API}/")
        assert r.status_code == 200
        data = r.json()
        assert data.get("app") == "UrbanHub"
        assert "version" in data
        assert data.get("status") == "ok"


# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------
class TestWeather:
    def test_timeseries_returns_60_monthly_points(self, session):
        r = session.get(f"{API}/weather/timeseries", params={"years": 5})
        assert r.status_code == 200
        body = r.json()
        data = body["data"]
        assert len(data) == 60
        sample = data[0]
        for key in ("date", "temp", "pressure", "wind", "precip"):
            assert key in sample
        assert isinstance(sample["temp"], (int, float))

    def test_cities_12_french(self, session):
        r = session.get(f"{API}/weather/cities")
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) == 12
        sample = data[0]
        for key in ("name", "lat", "lng", "temp", "wind", "humidity", "anomaly"):
            assert key in sample

    def test_alerts_3_to_5(self, session):
        r = session.get(f"{API}/weather/alerts")
        assert r.status_code == 200
        data = r.json()["data"]
        assert 3 <= len(data) <= 5
        sample = data[0]
        for key in ("title", "city", "severity", "ts"):
            assert key in sample


# ---------------------------------------------------------------------------
# Mobility
# ---------------------------------------------------------------------------
class TestMobility:
    def test_stations_returns_240(self, session):
        r = session.get(f"{API}/mobility/stations", params={"limit": 240})
        assert r.status_code == 200
        body = r.json()
        data = body["data"]
        assert len(data) == 240
        sample = data[0]
        for key in ("id", "name", "bikes", "slots", "capacity", "lat", "lng"):
            assert key in sample
        assert sample["bikes"] + sample["slots"] == sample["capacity"]

    def test_timeline_24_hours(self, session):
        r = session.get(f"{API}/mobility/timeline")
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) == 24
        assert "hour" in data[0] and "trips" in data[0]
        assert isinstance(data[0]["trips"], int)

    def test_critical_empty_or_full_with_status(self, session):
        r = session.get(f"{API}/mobility/critical")
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) > 0, "Expected at least one critical station"
        for s in data:
            assert s["bikes"] == 0 or s["slots"] == 0
            assert s.get("status") in ("empty", "full")


# ---------------------------------------------------------------------------
# Pollution
# ---------------------------------------------------------------------------
class TestPollution:
    def test_sensors_12_cities(self, session):
        r = session.get(f"{API}/pollution/sensors")
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) == 12
        sample = data[0]
        for key in ("name", "pm25", "pm10", "no2", "o3", "co", "aqi", "status"):
            assert key in sample
        assert sample["status"] in ("good", "moderate", "critical")

    def test_timeline_48_hourly_readings(self, session):
        r = session.get(f"{API}/pollution/timeline", params={"hours": 48})
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) == 48
        sample = data[0]
        for key in ("ts", "pm25", "pm10", "no2", "o3"):
            assert key in sample

    def test_comparison_12_cities(self, session):
        r = session.get(f"{API}/pollution/comparison")
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) == 12
        sample = data[0]
        for key in ("city", "pm25", "pm10", "no2"):
            assert key in sample


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
class TestAnalytics:
    def test_kpis_6_cards(self, session):
        r = session.get(f"{API}/analytics/kpis")
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) == 6
        for card in data:
            for key in ("key", "label", "value", "delta"):
                assert key in card

    def test_correlation_60_points(self, session):
        r = session.get(f"{API}/analytics/correlation")
        assert r.status_code == 200
        body = r.json()
        assert len(body["weather_pollution"]) == 60
        assert len(body["weather_mobility"]) == 60
        assert "temp" in body["weather_pollution"][0]
        assert "pollution" in body["weather_pollution"][0]
        assert "precip" in body["weather_mobility"][0]
        assert "trips" in body["weather_mobility"][0]

    def test_insights_6_items(self, session):
        r = session.get(f"{API}/analytics/insights")
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) == 6
        sample = data[0]
        for key in ("title", "summary", "tag", "severity"):
            assert key in sample


# ---------------------------------------------------------------------------
# Architecture
# ---------------------------------------------------------------------------
class TestArchitecture:
    def test_flows_nodes_edges_quality(self, session):
        r = session.get(f"{API}/architecture/flows")
        assert r.status_code == 200
        body = r.json()
        assert len(body["nodes"]) >= 11
        assert len(body["edges"]) >= 10
        dq = body["data_quality"]
        for key in ("completeness", "freshness_seconds", "schema_drift", "duplicates_pct"):
            assert key in dq
