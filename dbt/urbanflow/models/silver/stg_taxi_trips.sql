{{
    config(
        materialized='incremental',
        unique_key='trip_id',
        on_schema_change='fail'
    )
}}

WITH source AS (
    SELECT * FROM {{ source('bronze','raw_taxi_trips') }}
    {% if is_incremental() %}
    -- Only process new rows based on audit column
    WHERE loaded_at > (SELECT MAX(loaded_at) FROM {{ this }})
    {% endif %}
),

casting AS (
    SELECT
        CAST(VENDORID AS INT) AS vendor_id,
        -- Fix timestamp precision: Convert from microseconds to seconds
        TO_TIMESTAMP_NTZ(EXTRACT(EPOCH_SECONDS FROM TPEP_PICKUP_DATETIME) / 1000000) AS pickup_datetime,
        TO_TIMESTAMP_NTZ(EXTRACT(EPOCH_SECONDS FROM TPEP_DROPOFF_DATETIME) / 1000000) AS dropoff_datetime,
        CAST(PASSENGER_COUNT AS INT) AS passenger_count,
        CAST(TRIP_DISTANCE AS FLOAT) AS trip_distance,
        CAST(RATECODEID AS INT) AS rate_code_id,
        CAST(PULOCATIONID AS INT) AS pickup_location_id,
        CAST(DOLOCATIONID AS INT) AS dropoff_location_id,
        CAST(PAYMENT_TYPE AS INT) AS payment_type,
        CAST(FARE_AMOUNT AS FLOAT) AS fare_amount,
        CAST(TIP_AMOUNT AS FLOAT) AS tip_amount,
        CAST(TOTAL_AMOUNT AS FLOAT) AS total_amount,
        SOURCE_FILE,
        LOADED_AT
    FROM source
 ),

 deduplicated AS (
    SELECT
    *,
    ROW_NUMBER() OVER(
        PARTITION BY vendor_id, pickup_datetime, pickup_location_id
        ORDER BY loaded_at DESC
    ) AS row_num
    FROM casting
 ),

 filtered AS (
    SELECT *
    FROM deduplicated
    WHERE row_num = 1
        AND fare_amount > 0
        AND trip_distance > 0
        AND passenger_count > 0 AND passenger_count <= 8
        AND pickup_datetime < dropoff_datetime
 ),

 enriched AS (
    SELECT 
        -- Use Snowflake standard concatenation || for surrogate key
        MD5(vendor_id || '-' || pickup_datetime || '-' || pickup_location_id) AS trip_id,
        *,
        DATEDIFF('minute', pickup_datetime, dropoff_datetime) AS trip_duration_minutes,
        EXTRACT(HOUR FROM pickup_datetime) AS pickup_hour,
        DAYOFWEEK(pickup_datetime) AS pickup_day_of_week,
        DATE_TRUNC('hour', pickup_datetime) AS pickup_hour_truncated
    FROM filtered
    WHERE DATEDIFF('minute', pickup_datetime, dropoff_datetime) <= 180 
 )

 SELECT
    trip_id,
    vendor_id,
    pickup_datetime,
    dropoff_datetime,
    pickup_hour_truncated,
    pickup_hour,
    pickup_day_of_week,
    trip_duration_minutes,
    passenger_count,
    trip_distance,
    pickup_location_id,
    dropoff_location_id,
    fare_amount,
    tip_amount,
    total_amount,
    source_file,
    loaded_at
FROM enriched