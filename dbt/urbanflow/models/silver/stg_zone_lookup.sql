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
    COALESCE(service_zone,'Unknown') as service_zone,
    SOURCE_URL as source_file,
    LOADED_AT as loaded_at_bronze,
    CURRENT_TIMESTAMP() as dbt_updated_at
    FROM source
)

SELECT * FROM renamed