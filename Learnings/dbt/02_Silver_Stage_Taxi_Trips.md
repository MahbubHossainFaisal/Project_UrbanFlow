# 02 - Silver Stage Taxi Trips

## Purpose
This note explains the Silver taxi staging model:

```text
dbt/urbanflow/models/silver/stg_taxi_trips.sql
```

This is the most important Silver model in UrbanFlow because it turns high-volume raw taxi records into trusted, typed, deduplicated, enriched trip data.

---

## Core Mental Model

```text
Bronze taxi data = loaded facts from source files
Silver taxi data = valid trip events ready for analytics
Gold taxi facts  = business-facing models built on trusted Silver rows
```

The Silver layer is where we decide:

```text
Is this row a real trip?
Is the row typed correctly?
Is it duplicated?
Is the business grain clear?
What features should downstream Gold models reuse?
```

---

## Model Configuration

Current config:

```sql
{{
    config(
        materialized='incremental',
        unique_key='trip_id',
        on_schema_change='fail'
    )
}}
```

Meaning:

```text
materialized='incremental' = dbt can update this model without rebuilding all rows every time
unique_key='trip_id'       = trip_id identifies the row grain for incremental logic
on_schema_change='fail'    = fail loudly if upstream schema changes unexpectedly
```

Why incremental?

Taxi data is high-volume. Rebuilding millions of rows every time is expensive and slow. Incremental materialization is a Snowflake cost-control decision.

Why `on_schema_change='fail'`?

If raw taxi columns change unexpectedly, we want the pipeline to stop instead of silently producing wrong analytics.

---

## Source CTE

```sql
WITH source AS (
    SELECT * FROM {{ source('bronze', 'raw_taxi_trips') }}
)
```

`source()` points dbt to the physical Bronze table defined in:

```text
dbt/urbanflow/models/sources.yml
```

Current source mapping:

```yaml
sources:
  - name: bronze
    database: URBANFLOW_DB
    schema: BRONZE
    tables:
      - name: raw_taxi_trips
```

Why use `source()` instead of hardcoding?

```text
source() gives lineage, centralizes raw table location, and makes the DAG understandable.
```

---

## Casting CTE

```sql
casting AS (
    SELECT
        CAST(VENDORID AS INT) AS vendor_id,
        CAST(TPEP_PICKUP_DATETIME AS TIMESTAMP_NTZ) AS pickup_datetime,
        CAST(TPEP_DROPOFF_DATETIME AS TIMESTAMP_NTZ) AS dropoff_datetime,
        CAST(PASSENGER_COUNT AS INT) AS passenger_count,
        CAST(TRIP_DISTANCE AS FLOAT) AS trip_distance,
        CAST(PULOCATIONID AS INT) AS pickup_location_id,
        CAST(DOLOCATIONID AS INT) AS dropoff_location_id,
        CAST(RATECODEID AS INT) AS rate_code_id,
        CAST(PAYMENT_TYPE AS INT) AS payment_type_id,
        CAST(FARE_AMOUNT AS FLOAT) AS fare_amount,
        SOURCE_FILE,
        LOADED_AT
    FROM source
)
```

Purpose:

```text
Convert raw source columns into clean, typed, analytics-friendly columns.
```

Important naming pattern:

```text
VENDORID              -> vendor_id
TPEP_PICKUP_DATETIME  -> pickup_datetime
PULOCATIONID          -> pickup_location_id
DOLOCATIONID          -> dropoff_location_id
PAYMENT_TYPE          -> payment_type_id
```

Why direct timestamp casting now?

Earlier project versions had timestamp precision issues. The current modular ingestion framework already normalizes timestamp handling before dbt. Therefore, this model now uses direct casting:

```sql
CAST(TPEP_PICKUP_DATETIME AS TIMESTAMP_NTZ)
```

Architectural lesson:

```text
Do not duplicate brittle correction logic in dbt if the ingestion layer already produces normalized values.
```

---

## Deduplication CTE

```sql
deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER(
            PARTITION BY vendor_id, pickup_datetime, dropoff_datetime, pickup_location_id
            ORDER BY LOADED_AT DESC
        ) AS row_num
    FROM casting
)
```

Purpose:

```text
Keep one row for each real-world taxi trip grain.
```

Business grain used:

```text
vendor_id
pickup_datetime
dropoff_datetime
pickup_location_id
```

Why include `dropoff_datetime`?

Earlier hash logic had large key collisions. Adding `dropoff_datetime` made the trip grain more specific and reduced false duplicates.

Why `ORDER BY LOADED_AT DESC`?

If duplicates exist, keep the newest loaded version.

Mental model:

```text
ROW_NUMBER() labels possible duplicates.
row_num = 1 keeps the winning row.
```

---

## Filtering CTE

```sql
filtered AS (
    SELECT * FROM deduplicated
    WHERE row_num = 1
    AND fare_amount > 0
    AND trip_distance > 0
    AND passenger_count > 0
    AND pickup_datetime < dropoff_datetime
    AND DATEDIFF('minute', pickup_datetime, dropoff_datetime) <= 180
)
```

Purpose:

```text
Remove rows that do not represent valid taxi trips.
```

Rules:

```text
row_num = 1                    -> remove duplicate rows
fare_amount > 0                -> remove free/negative fare records
trip_distance > 0              -> remove no-movement records
passenger_count > 0            -> require at least one passenger
pickup_datetime < dropoff      -> time must move forward
duration <= 180 minutes        -> remove extreme meter/session issues
```

This is the core trust layer.

Architectural intuition:

```text
Bronze keeps raw truth.
Silver applies quality rules.
Gold should not repeatedly defend against basic invalid trip records.
```

---

## Enrichment CTE

```sql
enriched AS (
    SELECT
        MD5(vendor_id || '-' || pickup_datetime || '-' || dropoff_datetime || '-' || pickup_location_id) AS trip_id,
        *,
        DATEDIFF('minute', pickup_datetime, dropoff_datetime) AS trip_duration_minutes,
        EXTRACT(HOUR FROM pickup_datetime) AS pickup_hour,
        DAYOFWEEK(pickup_datetime) AS pickup_day_of_week,
        DATE_TRUNC('hour', pickup_datetime) AS pickup_hour_truncated,
        CURRENT_TIMESTAMP() as dbt_updated_at
    FROM filtered
)
```

Purpose:

```text
Add reusable fields that downstream Gold models need.
```

Added fields:

```text
trip_id                 = deterministic surrogate key
trip_duration_minutes   = trip duration metric
pickup_hour             = hour-of-day analysis
pickup_day_of_week      = weekday analysis
pickup_hour_truncated   = weather-hour join key
dbt_updated_at          = dbt transformation audit timestamp
```

Why `trip_id`?

Joining and testing one key is cleaner than repeatedly using several columns.

Current `trip_id` grain:

```text
vendor_id + pickup_datetime + dropoff_datetime + pickup_location_id
```

The grain must match the real-world uniqueness of a trip. If the grain is too weak, unrelated records collide.

---

## Emission Factors CTE

```sql
emission_factors AS (
    SELECT * FROM {{ ref('seed_emission_factors') }}
)
```

Purpose:

```text
Bring curated emission factors into the taxi staging model.
```

`ref()` points to another dbt resource and creates lineage.

Here:

```text
seed_emission_factors -> stg_taxi_trips
```

This connects seed reference data to trip-level feature engineering.

---

## Feature Engineering CTE

```sql
feature_engineering AS (
    SELECT
        e.*,
        COALESCE(ef.emission_factor_g_mile, 406.0) AS emission_factor,
        (e.trip_distance * COALESCE(ef.emission_factor_g_mile, 406.0)) AS co2_emission_grams,
        CASE WHEN e.trip_distance > 100 THEN TRUE ELSE FALSE END AS is_distance_anomaly,
        CASE WHEN e.fare_amount > 500 THEN TRUE ELSE FALSE END AS is_fare_anomaly
    FROM enriched e
    LEFT JOIN emission_factors ef
        ON e.vendor_id = ef.vendor_id
)
```

Purpose:

```text
Add reusable business features before Gold.
```

Features:

```text
emission_factor       = grams per mile factor by vendor
co2_emission_grams    = estimated trip emissions
is_distance_anomaly   = trip distance > 100 miles
is_fare_anomaly       = fare amount > 500 dollars
```

Why `COALESCE(..., 406.0)`?

If a vendor does not match an emission factor, the model uses a default factor instead of producing null CO2 values.

Why `LEFT JOIN`?

Taxi trips should not disappear just because a reference seed is missing a vendor. A `LEFT JOIN` preserves the trip and applies the fallback.

Architectural lesson:

```text
Feature engineering in Silver lets multiple Gold models reuse the same trusted calculations.
```

---

## Final Select

```sql
SELECT * FROM feature_engineering
```

The final output includes:

```text
typed raw fields
audit fields
deduplicated valid trips
time features
surrogate key
emissions metrics
anomaly flags
```

---

## Tests

Current tests in:

```text
dbt/urbanflow/models/silver/schema.yml
```

Important tests:

```yaml
- name: trip_id
  tests:
    - unique
    - not_null

- name: co2_emission_grams
  tests:
    - not_null

- name: is_distance_anomaly
  tests:
    - not_null

- name: is_fare_anomaly
  tests:
    - not_null
```

What these protect:

```text
trip_id unique      -> one row per modeled trip grain
trip_id not_null    -> every trip has an identifier
co2 not_null        -> sustainability feature is populated
anomaly flags       -> downstream Gold logic can filter safely
```

---

## Common Commands

Run from:

```bash
cd dbt/urbanflow
```

Run only this model:

```bash
dbt run --select stg_taxi_trips
```

Rebuild from scratch:

```bash
dbt run --select stg_taxi_trips --full-refresh
```

Run model and tests:

```bash
dbt build --select stg_taxi_trips
```

Build the model and its upstream dependencies:

```bash
dbt build --select +stg_taxi_trips
```

When to use `--full-refresh`:

```text
Use it when model logic changes in a way that old incremental rows must be recalculated.
```

Examples:

```text
trip_id grain changes
filtering logic changes
CO2 formula changes
anomaly thresholds change
timestamp casting logic changes
```

---

## Staff Architect Summary

`stg_taxi_trips` is the Silver trust layer for taxi events.

It does five jobs:

```text
1. Reads raw Bronze taxi data through source().
2. Casts source columns into correct analytical types.
3. Deduplicates records at the trip grain.
4. Filters invalid or physically unrealistic trips.
5. Adds reusable features for Gold analytics.
```

The core design principle:

```text
Gold should receive valid, unique, feature-ready trip rows.
```

This model is also a good example of Snowflake-aware engineering:

```text
incremental materialization reduces rebuild cost
explicit filtering protects downstream quality
surrogate key tests protect grain
precomputed features reduce repeated Gold/dashboard logic
```

---

## Next File To Study

Next recommended learning note:

```text
03_Silver_Stage_Weather_Hourly.md
```

That note should focus on:

```text
dbt/urbanflow/models/silver/stg_weather_hourly.sql
dbt/urbanflow/macros/classify_weather.sql
```
