-- ============================================================
-- Schéma IoT Pollution – UrbanHub Partie 3
-- Couches Silver et Gold avec contraintes et index
-- ============================================================

-- ------------------------------------------------------------
-- Table de suivi du traitement (idempotence Bronze → Silver)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS iot_processing_state (
    pipeline     VARCHAR(50)  PRIMARY KEY,
    last_line    BIGINT       NOT NULL DEFAULT 0,
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO iot_processing_state (pipeline, last_line)
VALUES ('bronze_to_silver', 0)
ON CONFLICT (pipeline) DO NOTHING;

-- ------------------------------------------------------------
-- Couche Silver – mesures nettoyées et normalisées
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS silver_iot_clean (
    id           BIGSERIAL    PRIMARY KEY,
    sensor_id    VARCHAR(100) NOT NULL,
    location_id  BIGINT,
    sensor_name  TEXT,
    city         VARCHAR(100),
    latitude     DOUBLE PRECISION,
    longitude    DOUBLE PRECISION,
    pollutant    VARCHAR(20)  NOT NULL,
    value        DOUBLE PRECISION NOT NULL,
    unit         VARCHAR(20)  NOT NULL,
    datetime_utc TIMESTAMPTZ  NOT NULL,
    source       VARCHAR(50)  NOT NULL DEFAULT 'OpenAQ',
    ingested_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    -- Évite les doublons exacts (même capteur, même polluant, même instant)
    CONSTRAINT silver_iot_unique UNIQUE (sensor_id, pollutant, datetime_utc)
);

CREATE INDEX IF NOT EXISTS idx_silver_datetime   ON silver_iot_clean (datetime_utc DESC);
CREATE INDEX IF NOT EXISTS idx_silver_sensor     ON silver_iot_clean (sensor_id);
CREATE INDEX IF NOT EXISTS idx_silver_pollutant  ON silver_iot_clean (pollutant);
CREATE INDEX IF NOT EXISTS idx_silver_city       ON silver_iot_clean (city);

-- ------------------------------------------------------------
-- Couche Gold – agrégats horaires par capteur et polluant
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold_pollution_hourly (
    sensor_id      VARCHAR(100)     NOT NULL,
    pollutant      VARCHAR(20)      NOT NULL,
    hour_utc       TIMESTAMPTZ      NOT NULL,
    city           VARCHAR(100),
    latitude       DOUBLE PRECISION,
    longitude      DOUBLE PRECISION,
    avg_value      DOUBLE PRECISION NOT NULL,
    max_value      DOUBLE PRECISION NOT NULL,
    min_value      DOUBLE PRECISION NOT NULL,
    samples_count  INTEGER          NOT NULL,
    computed_at    TIMESTAMPTZ      NOT NULL DEFAULT NOW(),

    PRIMARY KEY (sensor_id, pollutant, hour_utc)
);

CREATE INDEX IF NOT EXISTS idx_gold_hour       ON gold_pollution_hourly (hour_utc DESC);
CREATE INDEX IF NOT EXISTS idx_gold_pollutant  ON gold_pollution_hourly (pollutant);
CREATE INDEX IF NOT EXISTS idx_gold_city       ON gold_pollution_hourly (city);

-- ------------------------------------------------------------
-- Couche Gold – agrégats journaliers par ville et polluant
-- (granularité "jour" pour analyses tendancielles)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold_pollution_daily_city (
    city           VARCHAR(100)     NOT NULL,
    pollutant      VARCHAR(20)      NOT NULL,
    day_utc        DATE             NOT NULL,
    avg_value      DOUBLE PRECISION NOT NULL,
    max_value      DOUBLE PRECISION NOT NULL,
    min_value      DOUBLE PRECISION NOT NULL,
    samples_count  INTEGER          NOT NULL,
    sensors_count  INTEGER          NOT NULL,
    computed_at    TIMESTAMPTZ      NOT NULL DEFAULT NOW(),

    PRIMARY KEY (city, pollutant, day_utc)
);

CREATE INDEX IF NOT EXISTS idx_gold_daily_day       ON gold_pollution_daily_city (day_utc DESC);
CREATE INDEX IF NOT EXISTS idx_gold_daily_city      ON gold_pollution_daily_city (city);
CREATE INDEX IF NOT EXISTS idx_gold_daily_pollutant ON gold_pollution_daily_city (pollutant);
