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

calendar AS (
    SELECT * FROM {{ ref('dim_calendar') }}
),

joined AS (
    SELECT
        t.*,
        -- Foreign Key for Calendar Dimension
        TO_CHAR(t.pickup_datetime, 'YYYYMMDD')::INT AS pickup_date_id,
        w.temperature_2m,
        w.is_precipitation,
        w.weather_category,
        z.borough AS pickup_borough,
        z.zone AS pickup_zone,
        -- Temporal Context from Calendar
        c.is_holiday,
        c.is_weekend,
        c.holiday_name
    FROM trips t
    LEFT JOIN weather w
        ON t.pickup_hour_truncated = w.weather_time
    LEFT JOIN zones z
        ON t.pickup_location_id = z.location_id
    LEFT JOIN calendar c
        ON TO_CHAR(t.pickup_datetime, 'YYYYMMDD')::INT = c.date_id
)

SELECT *,
CURRENT_TIMESTAMP() AS last_updated_at
FROM joined