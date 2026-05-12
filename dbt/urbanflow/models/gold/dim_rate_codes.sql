{{ config(materialized='table') }}

WITH base AS(
    SELECT * FROM {{ ref('seed_rate_codes') }}
)
SELECT
    CAST(rate_code_id AS INT) AS rate_code_id,
    rate_code_name,
    CURRENT_TIMESTAMP() AS dbt_updated_at
FROM base