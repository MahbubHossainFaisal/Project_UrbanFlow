# 05 - Gold Stage: Fact Trips and Demand Aggregate

## Purpose
This note explains the first Gold layer models:

```text
dbt/urbanflow/models/gold/gold_fact_trips.sql
dbt/urbanflow/models/gold/gold_agg_demand_weather.sql
```

Gold models convert trusted Silver data into business-facing tables.

---

## Gold Layer Mental Model

```text
Silver = clean and reusable row-level data
Gold   = business-ready facts, dimensions, and aggregates
```

Gold should answer business questions directly:

```text
How many trips happened?
Where was demand strongest?
How did weather affect demand?
How much revenue was generated?
What was the environmental footprint?
```

---

## `gold_fact_trips`

Configuration:

```sql
{{ config(materialized='table') }}
```

Meaning:

```text
Build a physical Snowflake table for the core trip fact.
```

Why table?

```text
Gold facts are queried repeatedly by dashboards and analysis.
Persisting them reduces repeated compute.
```

---

## Inputs

```sql
trips    -> ref('stg_taxi_trips')
weather  -> ref('stg_weather_hourly')
zones    -> ref('stg_zone_lookup')
calendar -> ref('dim_calendar')
```

This model combines:

```text
trip event data
hourly weather context
pickup geography context
calendar context
```

---

## Join Strategy

Taxi is the anchor table:

```text
one row in stg_taxi_trips = one valid trip
```

All joins are `LEFT JOIN`s:

```sql
LEFT JOIN weather
LEFT JOIN zones
LEFT JOIN calendar
```

Why left joins?

```text
Do not drop taxi trips just because context data is missing.
```

This preserves the primary business event while adding context when available.

---

## Context Added

`gold_fact_trips` adds:

```text
pickup_date_id
temperature_2m
is_precipitation
weather_category
pickup_borough
pickup_zone
is_holiday
is_weekend
holiday_name
last_updated_at
```

Important join keys:

```text
t.pickup_hour_truncated = w.weather_time
t.pickup_location_id    = z.location_id
TO_CHAR(t.pickup_datetime, 'YYYYMMDD')::INT = c.date_id
```

---

## Date Key Logic

```sql
TO_CHAR(t.pickup_datetime, 'YYYYMMDD')::INT AS pickup_date_id
```

This creates an integer date key such as:

```text
20230115
```

Why integer date key?

```text
It is compact, easy to join, and common in dimensional modeling.
```

---

## `gold_agg_demand_weather`

Configuration:

```sql
{{ config(materialized='table') }}
```

Purpose:

```text
Pre-aggregate trip demand, revenue, CO2, and distance metrics by hour, borough, and weather.
```

This model is dashboard-friendly because it reduces the amount of data Streamlit must scan.

---

## Clean Fact Filter

```sql
WITH facts AS (
    SELECT * FROM {{ ref('gold_fact_trips') }}
    WHERE is_distance_anomaly = FALSE
        AND is_fare_anomaly = FALSE
)
```

Purpose:

```text
Exclude known distance and fare anomalies from executive aggregate metrics.
```

We do not delete anomalies in Silver. We flag them. Gold aggregates can then decide whether to exclude them for clean reporting.

---

## Aggregate Grain

Grouped by:

```text
pickup_hour_truncated
pickup_day_of_week
pickup_borough
weather_category
is_precipitation
```

This means:

```text
one row = one hour + borough + weather slice
```

---

## Aggregate Metrics

```text
total_trips
total_passengers
total_revenue
total_co2_grams
avg_co2_grams_per_trip
avg_fare_amount
avg_trip_duration_minutes
avg_trip_distance
```

These are dashboard-ready measures.

---

## Aggregate Surrogate Key

```sql
MD5(
    COALESCE(CAST(pickup_hour_truncated AS STRING), '_null_') || '-' ||
    COALESCE(CAST(pickup_borough AS STRING), '_null_') || '-' ||
    COALESCE(CAST(weather_category AS STRING),'_null_')
) AS agg_id
```

Purpose:

```text
Create a deterministic identifier for each aggregate row.
```

`COALESCE` avoids null values breaking the hash pattern.

Note:

```text
The current agg_id includes hour, borough, and weather_category.
The GROUP BY also includes pickup_day_of_week and is_precipitation.
This is acceptable if those values are functionally determined by the included fields, but if not, agg_id grain should be reviewed.
```

---

## Tests

Current Gold tests:

```yaml
gold_fact_trips.trip_id:
  - unique
  - not_null

gold_agg_demand_weather.agg_id:
  - unique
  - not_null

gold_agg_demand_weather.total_trips:
  - not_null
```

What they protect:

```text
fact trip grain does not duplicate
aggregate grain does not overlap
dashboard metrics are populated
```

---

## Common Commands

Run from:

```bash
cd dbt/urbanflow
```

Build core Gold trip fact:

```bash
dbt build --select gold_fact_trips
```

Build demand aggregate:

```bash
dbt build --select gold_agg_demand_weather
```

Build both with dependencies:

```bash
dbt build --select +gold_fact_trips+ +gold_agg_demand_weather
```

---

## Staff Architect Summary

`gold_fact_trips` creates the core business event table.

`gold_agg_demand_weather` creates a fast dashboard-serving aggregate.

Design principles:

```text
Keep the fact grain stable.
Use left joins to preserve primary events.
Pre-aggregate expensive dashboard questions.
Filter anomalies intentionally, not accidentally.
```

---

## Next File To Study

```text
06_Seeds_and_dim_calendar.md
```
