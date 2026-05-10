{{
    config(
        materialized='incremental',
        unique_key='trip_id',
        on_schema_change='fail'
    )
}}

WITH source AS (
    SELECT * FROM {{ source('bronze', 'raw_taxi_trips') }}
),

casting AS (
    
    SELECT
    CAST(VENDORID AS INT) AS vendor_id,
    TO_TIMESTAMP_NTZ(EXTRACT(EPOCH_SECONDS FROM TPEP_PICKUP_DATETIME) / 1000000) AS pickup_datetime,
    TO_TIMESTAMP_NTZ(EXTRACT(EPOCH_SECONDS FROM TPEP_DROPOFF_DATETIME) / 1000000) AS dropoff_datetime,
    CAST(PASSENGER_COUNT AS INT) AS passenger_count,
    CAST(TRIP_DISTANCE AS FLOAT) AS trip_distance,
    CAST(PULOCATIONID AS INT) AS pickup_location_id,
    CAST(DOLOCATIONID AS INT) AS dropoff_location_id,
    CAST(RATECODEID AS INT) AS rate_code_id,
    CAST(PAYMENT_TYPE AS INT) AS payment_type_id,
    CAST(FARE_AMOUNT AS FLOAT) AS fare_amount,
    SOURCE_FILE,
    LOADED_AT
    FROM source
),

deduplicated AS (
    SELECT 
    *, ROW_NUMBER() OVER(
        PARTITION BY vendor_id, pickup_datetime, pickup_location_id
        ORDER BY LOADED_AT DESC
    ) AS row_num

    FROM casting
),

filtered AS (
    SELECT * FROM deduplicated
    WHERE row_num = 1
    AND fare_amount>0
    AND trip_distance>0
    AND passenger_count>0
    AND pickup_datetime < dropoff_datetime
    AND DATEDIFF('minute', pickup_datetime, dropoff_datetime) <= 180
),

enriched AS (
    SELECT
    MD5(vendor_id || '-' || pickup_datetime || '-' || pickup_location_id) AS trip_id,
    *,
    DATEDIFF('minute',pickup_datetime,dropoff_datetime) AS trip_duration_minutes,
    EXTRACT(HOUR FROM pickup_datetime) AS pickup_hour,
    DAYOFWEEK(pickup_datetime) AS pickup_day_of_week,
    DATE_TRUNC('hour', pickup_datetime) AS pickup_hour_truncated,
    CURRENT_TIMESTAMP() as dbt_updated_at
    FROM filtered
),

emission_factors AS(
    SELECT * FROM {{ ref('seed_emission_factors') }}
),

feature_engineering AS(
    SELECT
    e.*,
    -- For unknown vendors
    COALESCE(ef.emission_factor_g_mile,406.0) AS emission_factor,
    -- CO2 grams
    (e.trip_distance * COALESCE(ef.emission_factor_g_mile,406.0)) AS co2_emission_grams,
    --Anomaly Detection
    CASE WHEN e.trip_distance > 100 THEN TRUE ELSE FALSE END AS is_distance_anomaly,
    CASE WHEN e.fare_amount > 500 THEN TRUE ELSE FALSE END AS is_fare_anomaly
    FROM enriched e
    LEFT JOIN emission_factors ef
        ON e.vendor_id = ef.vendor_id
)

SELECT * FROM feature_engineering