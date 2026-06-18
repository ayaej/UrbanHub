-- UrbanHub Database Initialization
-- Initialise PostgreSQL avec tables et permissions

-- Création utilisateur n8n
CREATE USER n8n_user WITH PASSWORD 'n8n_password';
GRANT ALL PRIVILEGES ON DATABASE n8n TO n8n_user;

-- Connexion à base urbanhub
\c urbanhub

-- Table: weather_daily (données quotidiennes)
CREATE TABLE IF NOT EXISTS weather_daily (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    city VARCHAR(100) NOT NULL,
    station_id VARCHAR(10) NOT NULL,
    temperature_mean FLOAT,
    temperature_min FLOAT,
    temperature_max FLOAT,
    wind_speed_mean FLOAT,
    wind_direction_mean FLOAT,
    pressure_mean FLOAT,
    precipitation_total FLOAT,
    visibility_mean FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, city, station_id)
);

-- Table: weather_extreme_days (événements extrêmes)
CREATE TABLE IF NOT EXISTS weather_extreme_days (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    city VARCHAR(100) NOT NULL,
    station_id VARCHAR(10) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    severity FLOAT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: weather_correlations (corrélations statistiques)
CREATE TABLE IF NOT EXISTS weather_correlations (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    season VARCHAR(20) NOT NULL,
    weather_variable VARCHAR(50) NOT NULL,
    correlation FLOAT,
    sample_size INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: city_summary_annual (résumés annuels)
CREATE TABLE IF NOT EXISTS city_summary_annual (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    avg_temperature FLOAT,
    extreme_hot_days INT,
    extreme_cold_days INT,
    total_precipitation FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(city, year)
);

-- Table: pipeline_runs (suivi exécutions)
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id SERIAL PRIMARY KEY,
    run_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    records_processed INT,
    duration_seconds INT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour performance BI
CREATE INDEX idx_weather_daily_date ON weather_daily(date);
CREATE INDEX idx_weather_daily_city ON weather_daily(city);
CREATE INDEX idx_weather_daily_station ON weather_daily(station_id);
CREATE INDEX idx_extreme_days_date ON weather_extreme_days(date);
CREATE INDEX idx_extreme_days_city ON weather_extreme_days(city);
CREATE INDEX idx_extreme_days_type ON weather_extreme_days(event_type);
CREATE INDEX idx_city_summary_year ON city_summary_annual(year);
CREATE INDEX idx_city_summary_city ON city_summary_annual(city);

-- Vues analytiques
CREATE OR REPLACE VIEW v_temperature_trends AS
SELECT 
    city,
    DATE_TRUNC('month', date)::DATE as month,
    AVG(temperature_mean) as avg_temp,
    MIN(temperature_min) as min_temp,
    MAX(temperature_max) as max_temp,
    STDDEV(temperature_mean) as volatility
FROM weather_daily
GROUP BY city, DATE_TRUNC('month', date)
ORDER BY city, month;

CREATE OR REPLACE VIEW v_extreme_events_summary AS
SELECT 
    city,
    event_type,
    EXTRACT(YEAR FROM date)::INT as year,
    COUNT(*) as count,
    AVG(severity) as avg_severity
FROM weather_extreme_days
GROUP BY city, event_type, EXTRACT(YEAR FROM date)
ORDER BY year DESC, count DESC;

CREATE OR REPLACE VIEW v_daily_metrics AS
SELECT 
    date,
    city,
    COUNT(*) as measurements,
    AVG(temperature_mean) as avg_temperature,
    MAX(wind_speed_mean) as max_wind,
    SUM(precipitation_total) as total_rain
FROM weather_daily
GROUP BY date, city
ORDER BY date DESC, city;

-- Permissions
GRANT CONNECT ON DATABASE urbanhub TO urbanhub_user;
GRANT USAGE ON SCHEMA public TO urbanhub_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO urbanhub_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO urbanhub_user;

-- Permissions n8n
GRANT SELECT, INSERT, UPDATE ON pipeline_runs TO n8n_user;
