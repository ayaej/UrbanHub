-- 1. Stations avec le plus fort taux d’utilisation
SELECT station_id,
       station_name,
       network,
       ROUND(AVG(bikes_available::numeric / NULLIF(bikes_available + free_slots, 0)), 4) AS usage_rate,
       ROUND(AVG(bikes_available)::numeric, 2) AS avg_bikes,
       ROUND(AVG(free_slots)::numeric, 2) AS avg_free_slots,
       COUNT(*) AS samples
FROM citybikes_station_events
GROUP BY station_id, station_name, network
ORDER BY usage_rate DESC NULLS LAST
LIMIT 20;

-- 2. Zones où l’offre de vélos est insuffisante
SELECT station_id,
       station_name,
       network,
       latitude,
       longitude,
       COUNT(*) FILTER (WHERE bikes_available = 0) AS zero_bike_count,
       AVG(bikes_available) AS avg_bikes,
       AVG(free_slots) AS avg_free_slots,
       COUNT(*) AS samples
FROM citybikes_station_events
GROUP BY station_id, station_name, network, latitude, longitude
HAVING COUNT(*) FILTER (WHERE bikes_available = 0) > 5
ORDER BY zero_bike_count DESC
LIMIT 20;

-- 3. Pics d’utilisation journaliers du réseau de vélos
SELECT date_trunc('day', event_timestamp) AS day,
       date_trunc('hour', event_timestamp) AS hour,
       ROUND(AVG(bikes_available::numeric / NULLIF(bikes_available + free_slots, 0)), 4) AS avg_usage,
       SUM(bikes_available) AS total_bikes,
       SUM(free_slots) AS total_free_slots,
       COUNT(*) AS samples
FROM citybikes_station_events
GROUP BY date_trunc('day', event_timestamp), date_trunc('hour', event_timestamp)
ORDER BY day, avg_usage DESC
LIMIT 50;

-- 4. Déséquilibres géographiques dans la disponibilité des vélos
SELECT station_id,
       station_name,
       network,
       latitude,
       longitude,
       ROUND(AVG(bikes_available)::numeric, 2) AS avg_bikes,
       ROUND(AVG(free_slots)::numeric, 2) AS avg_free_slots,
       ROUND(ABS(AVG(bikes_available - free_slots))::numeric, 2) AS imbalance_score,
       COUNT(*) AS samples
FROM citybikes_station_events
GROUP BY station_id, station_name, network, latitude, longitude
ORDER BY imbalance_score DESC
LIMIT 50;

-- 5. Stations critiques nécessitant un rééquilibrage des vélos
SELECT station_id,
       station_name,
       network,
       latitude,
       longitude,
       COUNT(*) FILTER (WHERE bikes_available = 0) AS no_bike_count,
       COUNT(*) FILTER (WHERE free_slots = 0) AS no_slot_count,
       COUNT(*) AS total_observations
FROM citybikes_station_events
GROUP BY station_id, station_name, network, latitude, longitude
HAVING COUNT(*) FILTER (WHERE bikes_available = 0) > 5
    OR COUNT(*) FILTER (WHERE free_slots = 0) > 5
ORDER BY GREATEST(no_bike_count, no_slot_count) DESC
LIMIT 50;
