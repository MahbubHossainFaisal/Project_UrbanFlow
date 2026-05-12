{{ config(materialized='table') }}

WITH base AS(
    SELECT * FROM {{ ref('stg_zone_lookup') }}
),
enriched AS(
    SELECT 
        location_id,
        borough,
        zone,
        service_zone,
        CASE 
            WHEN zone ILIKE '%AIRPORT%' THEN TRUE
            ELSE FALSE 
        END AS is_airport,
        CASE
            WHEN borough = 'Manhattan' THEN 'Core'
            WHEN borough = 'Unknown' THEN 'Unknown'
        ELSE 'Outer Boroughs'
        END AS borough_group
    FROM base
)

SELECT *,
    CURRENT_TIMESTAMP() AS dbt_updated_at
FROM enriched
