{{ config(materialized='table') }}

WITH base_trips AS (
    SELECT * FROM {{ ref('stg_taxi_trips') }}
    WHERE is_distance_anomaly = FALSE and is_fare_anomaly = FALSE
),
environmental_metrics AS(
    SELECT
        trip_id,
        vendor_id,
        pickup_location_id,
        dropoff_location_id,
        rate_code_id,
        passenger_count,
        trip_distance,
        TO_CHAR(pickup_datetime,'YYYYMMDD')::INT AS pickup_date_id,
        co2_emission_grams,
        (co2_emission_grams/1000.0) AS co2_emission_kg,
        (co2_emission_grams/NULLIF(trip_distance * passenger_count,0)) AS co2_per_passenger_mile,
        CASE WHEN trip_distance < 1.5 THEN TRUE ELSE FALSE END AS is_short_efficiency_risk
    FROM base_trips
)

SELECT
      *,
      CURRENT_TIMESTAMP() AS dbt_updated_at
FROM environmental_metrics