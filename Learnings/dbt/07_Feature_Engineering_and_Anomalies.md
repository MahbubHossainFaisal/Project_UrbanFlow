# 07 - Feature Engineering and Anomalies

## Purpose
This note explains how UrbanFlow adds reusable business features and anomaly flags in the transformation layer.

Primary model involved:

```text
dbt/urbanflow/models/silver/stg_taxi_trips.sql
```

Downstream model using the flags:

```text
dbt/urbanflow/models/gold/gold_agg_demand_weather.sql
```

---

## Core Mental Model

```text
Cleaning = make records valid
Feature engineering = make records useful
Anomaly flagging = make records transparent
```

UrbanFlow does not simply delete every strange record. It flags important anomalies so downstream models can decide whether to include or exclude them.

---

## Sustainability Feature Engineering

In `stg_taxi_trips`, emission factors are loaded from:

```text
seed_emission_factors
```

Join:

```sql
LEFT JOIN emission_factors ef
    ON e.vendor_id = ef.vendor_id
```

Feature logic:

```sql
COALESCE(ef.emission_factor_g_mile, 406.0) AS emission_factor,
(e.trip_distance * COALESCE(ef.emission_factor_g_mile, 406.0)) AS co2_emission_grams
```

Meaning:

```text
emission_factor    = grams of CO2 per mile
co2_emission_grams = trip distance * emission factor
```

Why `LEFT JOIN`?

```text
Do not lose taxi trips if a vendor is missing from the reference seed.
```

Why `COALESCE(..., 406.0)`?

```text
Use a default emissions factor when vendor-specific data is missing.
```

This keeps CO2 metrics populated and testable.

---

## Distance Anomaly Flag

```sql
CASE WHEN e.trip_distance > 100 THEN TRUE ELSE FALSE END AS is_distance_anomaly
```

Purpose:

```text
Flag trips over 100 miles as distance anomalies.
```

This does not delete the row. It marks it for downstream handling.

---

## Fare Anomaly Flag

```sql
CASE WHEN e.fare_amount > 500 THEN TRUE ELSE FALSE END AS is_fare_anomaly
```

Purpose:

```text
Flag trips with fare amount over $500 as fare anomalies.
```

Again, this preserves the row while protecting executive aggregates from distortion.

---

## Why Flag Instead of Delete

Deleting anomalies in Silver would hide information.

Flagging gives us both:

```text
transparency for audit
clean metrics for reporting
```

Pattern:

```text
Silver keeps valid rows and flags unusual values.
Gold decides whether a specific use case should filter them.
```

---

## Gold Aggregate Uses the Flags

In `gold_agg_demand_weather`:

```sql
WITH facts AS (
    SELECT * FROM {{ ref('gold_fact_trips') }}
    WHERE is_distance_anomaly = FALSE
        AND is_fare_anomaly = FALSE
)
```

Meaning:

```text
Executive demand/weather metrics exclude known distance and fare anomalies.
```

This keeps averages and totals from being skewed by extreme records.

---

## Tests

Current Silver tests:

```yaml
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

What they protect:

```text
CO2 metrics are always populated.
Anomaly flags are always true/false, not null.
Gold models can filter safely.
```

---

## Staff Architect Summary

Feature engineering turns clean data into reusable business data.

In UrbanFlow:

```text
CO2 features support sustainability analytics.
distance anomaly flags protect mobility metrics.
fare anomaly flags protect revenue metrics.
```

The key principle:

```text
Do not hide unusual data. Label it clearly, then let downstream models use it intentionally.
```

---

## Next File To Study

```text
08_Financial_Integrity_and_Multi_Fact_Design.md
```
