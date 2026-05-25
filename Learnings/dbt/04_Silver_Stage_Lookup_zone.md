# 04 - Silver Stage Zone Lookup

## Purpose
This note explains the Silver zone lookup model:

```text
dbt/urbanflow/models/silver/stg_zone_lookup.sql
```

This model turns the raw NYC taxi zone lookup table into a clean geographic reference table for downstream joins.

---

## Core Mental Model

```text
Taxi trips contain location IDs.
Zone lookup translates those IDs into borough, zone, and service zone names.
```

The zone lookup is small, but it is high-impact. If it is wrong or duplicated, Gold joins can inflate trip counts, revenue, and demand metrics.

---

## Model Configuration

```sql
{{ config(materialized='table') }}
```

Meaning:

```text
Build this model as a physical Snowflake table.
```

Why table?

```text
The zone lookup is small, stable reference data.
It is joined repeatedly to millions of taxi trips.
Persisting it avoids recalculating the same cleanup logic repeatedly.
```

---

## Source CTE

```sql
WITH source as (
    SELECT * FROM {{ source('bronze','raw_taxi_zone_lookup') }}
)
```

The model reads the raw lookup table declared in:

```text
dbt/urbanflow/models/sources.yml
```

Using `source()` gives dbt lineage and avoids hardcoded physical table references.

---

## Rename and Cleanup

```sql
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
```

Purpose:

```text
Standardize column names.
Type the location key.
Protect downstream models from null geography labels.
Preserve audit fields.
```

Important fields:

```text
location_id       = taxi zone key
borough           = borough name
zone              = zone/neighborhood name
service_zone      = TLC service zone
source_file       = source/audit reference from ingestion
loaded_at_bronze  = Bronze ingestion timestamp
dbt_updated_at    = dbt transformation timestamp
```

---

## Why `COALESCE`

```sql
COALESCE(borough, 'Unknown')
```

Meaning:

```text
If borough is null, replace it with 'Unknown'.
```

Why this matters:

```text
Dashboards and Gold models should not show blank geography categories.
```

Known TLC lookup values such as unknown/N/A zones can appear in source data. Silver should label them clearly instead of passing nulls downstream.

---

## Join Fan-Out Risk

The most important rule for this model:

```text
location_id must be unique.
```

Why?

If `location_id = 100` appears twice in the lookup table, then every taxi trip with pickup location 100 can duplicate after the join.

That creates false business metrics:

```text
trip count inflated
revenue inflated
CO2 inflated
demand inflated
```

Small reference tables can break large fact tables.

---

## Tests

Current tests in:

```text
dbt/urbanflow/models/silver/schema.yml
```

```yaml
- name: location_id
  tests:
    - unique
    - not_null

- name: borough
  tests:
    - not_null
```

What they protect:

```text
location_id unique   = one row per zone key
location_id not_null = every row can join to facts
borough not_null     = reporting geography is labeled
```

---

## Downstream Usage

Used by:

```text
gold_fact_trips
dim_zones
gold_agg_demand_weather
```

Important join:

```sql
t.pickup_location_id = z.location_id
```

In `gold_fact_trips`, this adds:

```text
pickup_borough
pickup_zone
```

---

## Common Commands

Run from:

```bash
cd dbt/urbanflow
```

Build model and tests:

```bash
dbt build --select stg_zone_lookup
```

Build downstream models too:

```bash
dbt build --select stg_zone_lookup+
```

---

## Staff Architect Summary

`stg_zone_lookup` is the geographic gatekeeper.

It does three jobs:

```text
1. Converts raw zone lookup fields into clean typed columns.
2. Replaces missing geography labels with explicit 'Unknown' values.
3. Protects downstream joins by enforcing one row per location_id.
```

The key lesson:

```text
Reference data may be small, but its uniqueness controls the correctness of large fact-table joins.
```

---

## Next File To Study

```text
05_Gold_Stage.md
```
