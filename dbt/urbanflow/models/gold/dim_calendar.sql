{{ config(materialized='table') }}

WITH date_spine AS(
    SELECT
        DATEADD(day,seq4(),'2023-01-01') AS date_day
    FROM TABLE(GENERATOR(ROWCOUNT=>3650))
),

enriched AS(
    SELECT
        TO_CHAR(date_day, 'YYYYMMDD')::INT AS date_id,
        date_day,
        EXTRACT(YEAR FROM date_day) AS year,
        EXTRACT(MONTH FROM date_day) AS month,
        MONTHNAME(date_day) AS month_name,
        EXTRACT(DAY FROM date_day) AS day_of_month,
        EXTRACT(DAYOFWEEK FROM date_day) AS day_of_week,
        DAYNAME(date_day) AS day_name,
        EXTRACT(QUARTER FROM date_day) AS quarter,
        -- ISO week logic
        EXTRACT(WEEKISO FROM date_day) AS week_of_year
        FROM date_spine
),

business_logic AS(
    SELECT 
    *,
    -- Weekend Logic (0=Sun, 6=Sat)
    CASE
        WHEN day_of_week IN (0,6) THEN TRUE 
        ELSE FALSE
    END AS is_weekend,

    -- Fixed NYC/Federal Holiday Logic
    CASE
        WHEN month = 1 AND day_of_month = 1 THEN 'New Years Day'
        WHEN month = 7 AND day_of_month = 4 THEN 'Independence Day'
        WHEN month = 11 AND day_of_month = 11 THEN 'Veterans Day'
        WHEN month = 12 AND day_of_month = 25 THEN 'Christmas Day'
        ELSE NULL
    END AS holiday_name
    FROM enriched

)

SELECT *,
    CASE WHEN holiday_name IS NOT NULL THEN TRUE ELSE FALSE END AS is_holiday,
    CURRENT_TIMESTAMP() AS dbt_updated_at
FROM business_logic