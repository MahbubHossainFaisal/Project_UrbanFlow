{{ config(materialized='table') }}

WITH source as
(
    SELECT * FROM {{ source('bronze','raw_taxi_zone_lookup') }}
),

renamed AS (
    SELECT 
    CAST(locationid as INT) AS location_id,
    COALESCE(borough, 'Unknown') AS borough,
    COALESCE(zone, 'Unknown') AS zone,
    COALESCE(service_zone,'Unknown') as service_zone
    FROM source
)

SELECT * FROM renamed