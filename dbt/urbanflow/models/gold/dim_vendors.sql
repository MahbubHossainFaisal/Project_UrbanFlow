{{ config(materialized='table') }}

WITH base AS(
    SELECT * FROM {{ ref('seed_vendor_lookup') }}
)
SELECT
    CAST(vendor_id AS INT) AS vendor_id,
    vendor_name,
    CURRENT_TIMESTAMP() AS dbt_updated_at
FROM base