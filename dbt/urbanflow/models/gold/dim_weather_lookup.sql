{{ config(materialized='table') }}

WITH base AS(
    SELECT 
        DISTINCT weather_code
        FROM {{ ref('stg_weather_hourly') }}
),
classified AS(   
    SELECT *,
    {{ classify_weather('weather_code') }} as weather_category
    FROM base
)

SELECT 
    weather_code,
    weather_category
FROM classified