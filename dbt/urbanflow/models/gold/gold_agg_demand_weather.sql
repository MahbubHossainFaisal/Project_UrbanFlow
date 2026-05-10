{{ config(materialized='table') }}

WITH facts AS (
    SELECT * FROM {{ ref('gold_fact_trips') }}
    WHERE is_distance_anomaly = FALSE 
        AND is_fare_anomaly = FALSE
),

final_agg AS(
    SELECT
        MD5(
            COALESCE(CAST(pickup_hour_truncated AS STRING), '_null_') || '-' ||
            COALESCE(CAST(pickup_borough AS STRING), '_null_') || '-' ||
            COALESCE(CAST(weather_category AS STRING),'_null_')
        ) AS agg_id,
        pickup_hour_truncated,
        pickup_day_of_week,
        pickup_borough,
        weather_category,
        is_precipitation,
        COUNT(*) AS total_trips,
        SUM(passenger_count) AS total_passengers,
        SUM(fare_amount) AS total_revenue,
        SUM(co2_emission_grams) AS total_co2_grams,
        AVG(co2_emission_grams) AS avg_co2_grams_per_trip,
        AVG(fare_amount) AS avg_fare_amount,
        AVG(trip_duration_minutes) AS avg_trip_duration_minutes,
        AVG(trip_distance) AS avg_trip_distance

    FROM facts
    GROUP BY
    pickup_hour_truncated,
    pickup_day_of_week,
    pickup_borough,
    weather_category,
    is_precipitation

)

SELECT *,
CURRENT_TIMESTAMP() AS last_aggregated_at
FROM final_agg