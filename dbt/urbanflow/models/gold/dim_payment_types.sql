{{ config(materialized='table') }}

WITH base AS(
    SELECT * FROM {{ ref('seed_payment_types') }}
)
SELECT
    CAST(payment_type_id AS INT) AS payment_type_id,
    payment_type_name,
    CURRENT_TIMESTAMP() AS dbt_updated_at
FROM base