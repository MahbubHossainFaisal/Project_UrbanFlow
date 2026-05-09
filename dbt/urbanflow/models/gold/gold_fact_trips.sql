{{ config(materialized='table') }}

WITH trips AS (
    SELECT * FROM {{ ref('stg_taxi_trips') }}
),

weather AS (
    SELECT * FROM {{ ref('stg_weather_hourly') }}
),

zones AS (
    SELECT * FROM {{ ref('stg_zone_lookup') }}
),

joined AS (
    SELECT
        t.*,
        w.temperature_2m,
        w.is_precipitation,
        w.weather_category,
        z.borough AS pickup_borough,
        z.zone AS pickup_zone
    FROM trips t
    LEFT JOIN weather w
        ON t.pickup_hour_truncated = w.weather_time
    LEFT JOIN zones z
        ON t.pickup_location_id = z.location_id
)

SELECT *,
CURRENT_TIMESTAMP() AS last_updated_at
FROM joined