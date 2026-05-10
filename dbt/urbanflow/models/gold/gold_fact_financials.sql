/*
-- STEPS
-- 1. Import the config syntax
-- 2. Add trips CTE 
-- 3. add dim calender CTE
-- 4. Create new CTE financial_integrity CTE that has 
trip id, vendor id , pickup date id (conver actual date from timestamp using CHAR func), rate code id, payment type id, fareamount,
Create a logic For JFK like if rate code id = 2 (JFK) then $70 otherwise, we trust the meter which is fareamount. Column name would be expected_fare,
Do Variance calculation same logic for JFK have to be applied , Formula is = fare_amount - switch case fareamount,
Flag airport Trips column -> is_airport_trip (For only rate code id 2,3 it's an airport trip else not.)
Select all values from trips

Finally select *, CREATE a fkag called is_price_anomaly using ratecodeid = 2 and abs(fare_variance) > 0.5 CASE,
dbt_updated_at column finish!
*/

{{ config(materialized='table') }}

WITH trips AS (
    SELECT * FROM {{ ref('stg_taxi_trips') }}
),

dim_calendar AS (
    SELECT * FROM {{ ref('dim_calendar') }}
),

financial_integrity AS (
    SELECT
    t.trip_id,
    t.vendor_id,
    TO_CHAR(t.pickup_datetime, 'YYYYMMDD')::INT AS pickup_date_id,
    t.rate_code_id,
    t.payment_type_id,
    t.fare_amount,
    CASE
        WHEN t.rate_code_id=2 THEN 70
        ELSE t.fare_amount
    END AS expected_fare,
    --Calculating Variance
    t.fare_amount - CASE WHEN t.rate_code_id=2 THEN 70 ELSE t.fare_amount END AS fare_variance,
    -- Flag for only Airport Trips
    CASE
        WHEN rate_code_id IN (2,3) THEN TRUE
        ELSE FALSE 
    END AS is_airport_trip

    FROM trips t
)

SELECT *,
    CASE WHEN rate_code_id=2 AND abs(fare_variance) > 0.5 THEN TRUE
        ELSE FALSE
    END AS is_price_anomaly,
    CURRENT_TIMESTAMP() AS dbt_updated_at
FROM financial_integrity