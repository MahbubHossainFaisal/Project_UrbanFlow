# 06 - Seeds and dim_calendar

## Purpose
This note explains two foundational reference patterns in UrbanFlow:

```text
dbt/urbanflow/seeds/*
dbt/urbanflow/models/gold/dim_calendar.sql
```

Seeds provide version-controlled reference data. `dim_calendar` provides reusable date intelligence for facts and dashboards.

---

## Core Mental Model

```text
Seeds = small static reference tables stored as CSV
dim_calendar = generated date dimension for time-based analysis
```

These are not raw event facts. They are controlled reference structures that make analysis consistent.

---

## Current Seed Files

```text
seed_vendor_lookup.csv
seed_rate_codes.csv
seed_payment_types.csv
seed_emission_factors.csv
```

Current values:

```text
Vendors:
1 = Creative Mobile Technologies
2 = VeriFone Inc.

Rate codes:
1 = Standard
2 = JFK
3 = Newark
4 = Nassau or Westchester
5 = Negotiated
6 = Group ride

Payment types:
1 = Credit Card
2 = Cash
3 = No charge
4 = Dispute
5 = Unknown
6 = Voided trip

Emission factors:
vendor 1 = 400.0 g/mile
vendor 2 = 411.0 g/mile
```

---

## Seed Routing

In `dbt_project.yml`:

```yaml
seeds:
  urbanflow:
    +schema: silver
```

Meaning:

```text
dbt seeds are loaded into the SILVER schema.
```

Why Silver?

```text
Seeds are trusted reference inputs.
They are cleaner than Bronze raw data but still feed Gold dimensions and facts.
```

---

## Why Seeds Instead of Hardcoding

Do not hardcode reference mappings repeatedly in SQL.

Seeds are better because:

```text
they are version-controlled
they are visible to reviewers
they can be tested and referenced
they can be reused by multiple models
they avoid duplicated CASE expressions
```

Example:

```text
seed_emission_factors feeds stg_taxi_trips CO2 calculations.
seed_vendor_lookup feeds dim_vendors.
seed_rate_codes feeds dim_rate_codes.
seed_payment_types feeds dim_payment_types.
```

---

## Common Seed Commands

Run from:

```bash
cd dbt/urbanflow
```

Load all seeds:

```bash
dbt seed
```

Load one seed:

```bash
dbt seed --select seed_emission_factors
```

Build models depending on seeds:

```bash
dbt build --select seed_emission_factors+
```

---

## `dim_calendar`

Location:

```text
dbt/urbanflow/models/gold/dim_calendar.sql
```

Configuration:

```sql
{{ config(materialized='table') }}
```

Meaning:

```text
Build a physical date dimension table.
```

---

## Date Spine

```sql
WITH date_spine AS (
    SELECT
        DATEADD(day, seq4(), '2023-01-01') AS date_day
    FROM TABLE(GENERATOR(ROWCOUNT=>3650))
)
```

Purpose:

```text
Generate 3650 dates starting from 2023-01-01.
```

This is a Snowflake-native date spine.

Why useful?

```text
It creates a date dimension without reading from a source table.
```

---

## Date Attributes

`dim_calendar` adds:

```text
date_id
date_day
year
month
month_name
day_of_month
day_of_week
day_name
quarter
week_of_year
```

Important key:

```sql
TO_CHAR(date_day, 'YYYYMMDD')::INT AS date_id
```

Example:

```text
2023-01-15 -> 20230115
```

This is used by Gold facts as a foreign key.

---

## Business Calendar Logic

Weekend logic:

```sql
CASE
    WHEN day_of_week IN (0,6) THEN TRUE
    ELSE FALSE
END AS is_weekend
```

Holiday logic:

```text
New Years Day
Independence Day
Veterans Day
Christmas Day
```

Final flag:

```sql
CASE WHEN holiday_name IS NOT NULL THEN TRUE ELSE FALSE END AS is_holiday
```

---

## Why Calendar Dimension Matters

Without `dim_calendar`, every dashboard or model would repeatedly calculate:

```text
year
month
day of week
weekend
holiday
```

With `dim_calendar`, those definitions live once.

This improves:

```text
consistency
dashboard simplicity
query performance
business trust
```

---

## Tests

Current Gold tests:

```yaml
dim_calendar.date_id:
  - unique
  - not_null

dim_calendar.date_day:
  - unique
  - not_null
```

These protect the date dimension grain:

```text
one row per date
```

---

## Staff Architect Summary

Seeds and `dim_calendar` are reference foundations.

Seeds handle controlled business mappings:

```text
vendors
rate codes
payment types
emission factors
```

`dim_calendar` handles time intelligence:

```text
date keys
month/day attributes
weekends
holidays
```

The key idea:

```text
Reference logic should be centralized once, then reused everywhere.
```

---

## Next File To Study

```text
07_Feature_Engineering_and_Anomalies.md
```
