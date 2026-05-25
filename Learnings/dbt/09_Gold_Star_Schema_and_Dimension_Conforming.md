# 09 - Gold Star Schema and Dimension Conforming

## Purpose
This note explains the final Gold architecture in UrbanFlow:

```text
multiple fact tables
shared conformed dimensions
business-ready aggregates
```

Key models:

```text
gold_fact_trips
gold_fact_financials
gold_fact_sustainability
gold_agg_demand_weather
dim_calendar
dim_zones
dim_vendors
dim_rate_codes
dim_payment_types
dim_weather_lookup
```

---

## Core Mental Model

```text
Facts = measurable business events or processes
Dimensions = descriptive context shared across facts
Aggregates = precomputed summaries for dashboards
```

UrbanFlow Gold layer turns cleaned data into a dimensional analytics model.

---

## Fact Tables

### `gold_fact_trips`

Core mobility fact.

Grain:

```text
one row per taxi trip
```

Adds context:

```text
weather
pickup geography
calendar flags
```

### `gold_fact_financials`

Financial audit fact.

Purpose:

```text
evaluate fare variance and airport pricing anomalies
```

### `gold_fact_sustainability`

Environmental impact fact.

Purpose:

```text
track trip-level CO2 metrics and efficiency risk
```

### `gold_agg_demand_weather`

Dashboard aggregate.

Purpose:

```text
precompute demand, revenue, distance, and CO2 metrics by hour, borough, and weather
```

---

## `gold_fact_sustainability`

Input:

```text
stg_taxi_trips
```

Filter:

```sql
WHERE is_distance_anomaly = FALSE
  AND is_fare_anomaly = FALSE
```

Purpose:

```text
Exclude known extreme anomalies from environmental KPI calculations.
```

Metrics:

```text
co2_emission_grams
co2_emission_kg
co2_per_passenger_mile
is_short_efficiency_risk
```

Important formula:

```sql
co2_emission_grams / NULLIF(trip_distance * passenger_count, 0)
```

Why `NULLIF`?

```text
Prevent division-by-zero errors.
```

Short trip flag:

```sql
CASE WHEN trip_distance < 1.5 THEN TRUE ELSE FALSE END AS is_short_efficiency_risk
```

Business meaning:

```text
Very short taxi trips may be candidates for walking, biking, or transit alternatives.
```

---

## Conformed Dimensions

A conformed dimension is shared by multiple fact tables.

Meaning:

```text
The same vendor_id means the same vendor everywhere.
The same date_id means the same date everywhere.
The same location_id means the same zone everywhere.
```

This makes cross-fact analysis consistent.

---

## `dim_zones`

Input:

```text
stg_zone_lookup
```

Adds:

```text
is_airport
borough_group
dbt_updated_at
```

Airport logic:

```sql
CASE WHEN zone ILIKE '%AIRPORT%' THEN TRUE ELSE FALSE END AS is_airport
```

Why `ILIKE`?

```text
Case-insensitive matching is safer for messy source labels.
```

Borough grouping:

```text
Manhattan -> Core
Unknown   -> Unknown
else      -> Outer Boroughs
```

---

## Seed-Based Dimensions

### `dim_vendors`

Input:

```text
seed_vendor_lookup
```

Output:

```text
vendor_id
vendor_name
dbt_updated_at
```

### `dim_rate_codes`

Input:

```text
seed_rate_codes
```

Output:

```text
rate_code_id
rate_code_name
dbt_updated_at
```

### `dim_payment_types`

Input:

```text
seed_payment_types
```

Output:

```text
payment_type_id
payment_type_name
dbt_updated_at
```

These models promote seed mappings into Gold dimensions.

---

## `dim_weather_lookup`

Input:

```text
distinct weather_code from stg_weather_hourly
```

Logic:

```sql
{{ classify_weather('weather_code') }} as weather_category
```

Purpose:

```text
Create a compact weather code dimension with business-readable categories.
```

Current output:

```text
weather_code
weather_category
```

Note:

```text
This model currently does not add dbt_updated_at, unlike other dimensions.
Add it later if audit consistency is required.
```

---

## Normalization vs Denormalization

Facts should carry keys and measures:

```text
trip_id
vendor_id
rate_code_id
payment_type_id
pickup_date_id
fare_amount
trip_distance
co2 metrics
```

Dimensions should carry descriptions:

```text
vendor_name
rate_code_name
payment_type_name
borough
zone
weather_category
holiday_name
```

Gold can selectively denormalize high-use fields when it reduces dashboard compute, such as:

```text
pickup_borough
pickup_zone
weather_category
is_weekend
is_holiday
```

The tradeoff:

```text
small storage increase
less repeated dashboard joining
lower Snowflake compute for common questions
```

---

## Current Tests

Current Gold tests cover:

```text
gold_fact_trips.trip_id unique/not_null
gold_agg_demand_weather.agg_id unique/not_null
gold_agg_demand_weather.total_trips not_null
dim_calendar.date_id unique/not_null
dim_calendar.date_day unique/not_null
```

Potential future tests:

```text
unique/not_null on dimension keys
relationships from facts to dimensions
accepted_values for categorical flags
not_null on key business metrics
```

---

## Staff Architect Summary

UrbanFlow Gold is a multi-fact star schema:

```text
mobility fact
financial integrity fact
sustainability fact
demand/weather aggregate
shared dimensions
```

The key business contract:

```text
Every fact should answer a specific business process.
Every dimension should mean the same thing wherever it is used.
```

That is what makes the warehouse trustworthy for analytics and dashboards.
