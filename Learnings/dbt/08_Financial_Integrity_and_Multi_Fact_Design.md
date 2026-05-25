# 08 - Financial Integrity and Multi-Fact Design

## Purpose
This note explains the financial integrity fact model:

```text
dbt/urbanflow/models/gold/gold_fact_financials.sql
```

This model audits fare behavior, especially airport-related pricing, without overloading the main trip fact.

---

## Core Mental Model

```text
gold_fact_trips          = core mobility event fact
gold_fact_financials     = financial audit fact
gold_fact_sustainability = environmental impact fact
```

This is multi-fact design.

Instead of forcing every metric into one giant table, each fact table serves a specific business process.

---

## Model Configuration

```sql
{{ config(materialized='table') }}
```

Meaning:

```text
Build a physical Snowflake table for repeated financial analysis.
```

---

## Inputs

```sql
WITH trips AS (
    SELECT * FROM {{ ref('stg_taxi_trips') }}
),

dim_calendar AS (
    SELECT * FROM {{ ref('dim_calendar') }}
)
```

Current note:

```text
dim_calendar is referenced but not used in the final query.
```

That is not harmful, but it is unnecessary. A future cleanup could remove it unless calendar fields are added.

Why use `stg_taxi_trips` directly?

```text
The financial fact can stay independent from gold_fact_trips and avoid circular Gold dependencies.
```

---

## Financial Integrity CTE

The model selects:

```text
trip_id
vendor_id
pickup_date_id
rate_code_id
payment_type_id
fare_amount
expected_fare
fare_variance
is_airport_trip
```

Important date key:

```sql
TO_CHAR(t.pickup_datetime, 'YYYYMMDD')::INT AS pickup_date_id
```

This connects the fact to `dim_calendar`.

---

## Expected Fare Logic

```sql
CASE
    WHEN t.rate_code_id = 2 THEN 70
    ELSE t.fare_amount
END AS expected_fare
```

Meaning:

```text
For JFK trips, expected fare is 70.
For other trips, expected fare equals actual fare.
```

Why set non-JFK expected fare to actual fare?

```text
We do not have a fixed benchmark for every rate type.
Setting expected = actual creates zero variance for non-benchmarked trips.
```

This keeps the formula consistent without falsely flagging unknown business rules.

---

## Fare Variance

```sql
t.fare_amount - CASE WHEN t.rate_code_id = 2 THEN 70 ELSE t.fare_amount END AS fare_variance
```

Meaning:

```text
fare_variance = actual fare - expected fare
```

For non-JFK trips:

```text
fare_variance = fare_amount - fare_amount = 0
```

For JFK trips:

```text
fare_variance = fare_amount - 70
```

---

## Airport Trip Flag

```sql
CASE
    WHEN rate_code_id IN (2,3) THEN TRUE
    ELSE FALSE
END AS is_airport_trip
```

Current business logic:

```text
rate_code_id = 2 -> JFK
rate_code_id = 3 -> Newark
```

So these are marked as airport trips.

---

## Price Anomaly Flag

```sql
CASE
    WHEN rate_code_id = 2 AND abs(fare_variance) > 0.5 THEN TRUE
    ELSE FALSE
END AS is_price_anomaly
```

Meaning:

```text
Only JFK trips are currently checked against the $70 benchmark.
Any JFK fare variance greater than 50 cents is flagged.
```

Why not Newark?

```text
The current benchmark logic only defines a reliable JFK expected fare.
Newark may include metered fares, tolls, and surcharges, so it is not treated as a fixed $70 rule here.
```

---

## Why This Is a Separate Fact

Financial integrity is a different business process from trip demand.

Separate fact benefits:

```text
keeps audit logic focused
avoids bloating gold_fact_trips
allows finance-specific tests and future rules
supports independent dashboard views
```

Future rules can be added here without destabilizing mobility or sustainability facts.

---

## Potential Cleanup

The model currently has a large commented planning block at the top.

Recommendation:

```text
Move planning notes into Learnings/ or session logs.
Keep production dbt SQL files concise.
```

The model also defines:

```sql
dim_calendar AS (...)
```

but does not use it. Remove it later unless calendar attributes are added to the financial fact.

---

## Common Commands

Run from:

```bash
cd dbt/urbanflow
```

Build this fact:

```bash
dbt build --select gold_fact_financials
```

Build with upstream dependencies:

```bash
dbt build --select +gold_fact_financials
```

---

## Staff Architect Summary

`gold_fact_financials` turns the warehouse into a financial audit tool.

It answers:

```text
Which trips are airport trips?
What was the expected fare?
What was the actual fare?
How large was the variance?
Which JFK trips violate the benchmark?
```

The key design lesson:

```text
Use specialized facts when a business process has its own rules, grain, and audit logic.
```

---

## Next File To Study

```text
09_Gold_Star_Schema_and_Dimension_Conforming.md
```
