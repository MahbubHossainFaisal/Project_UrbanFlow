{{
    config(
        materialized='incremental',
        unique_key='trip_id',
        on_schema_change='fail'
    )
}}

/*
   GUIDED TRANSFORMATION: STG_TAXI_TRIPS
   
   Your journey to a clean Silver table begins here. 
   Follow the CTE structure below to transform raw data into analytics-ready rows.
*/

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
    DATE_TRUNC('hour', pickup_datetime) AS pickup_hour_truncated
    FROM filtered
)

SELECT
    trip_id,
    vendor_id,
    pickup_datetime,
    dropoff_datetime,
    pickup_hour,
    pickup_hour_truncated,
    pickup_day_of_week,
    trip_duration_minutes,
    passenger_count,
    trip_distance,
    pickup_location_id,
    dropoff_location_id,
    fare_amount,
    source_file,
    loaded_at
FROM enriched