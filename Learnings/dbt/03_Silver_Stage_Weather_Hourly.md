# 03 - Silver Stage Weather Hourly

## Purpose
This note explains the Silver weather staging model:

```text
dbt/urbanflow/models/silver/stg_weather_hourly.sql
```

and the weather classification macro:

```text
dbt/urbanflow/macros/classify_weather.sql
```

The model turns raw hourly weather API data into a clean hourly weather dimension-like staging table for downstream taxi and demand analysis.

---

## Core Mental Model

Taxi data is event-based:

```text
one row = one taxi trip
```

Weather data is time-series:

```text
one row = one weather hour
```

That difference matters because weather will be joined to taxi trips by hour. If weather has missing hours, trips lose context. If weather has duplicate hours, trip rows can multiply during joins.

The core rule:

```text
stg_weather_hourly must have exactly one row per weather_time.
```

---

## Model Configuration

Current config:

```sql
{{
    config(
        materialized='view'
    )
}}
```

Meaning:

```text
dbt creates this model as a Snowflake view.
```

Why a view?

Weather volume is small compared with taxi trips. The current weather dataset is hourly and lightweight. A view keeps development flexible and avoids storing another physical table until performance requires it.

Architectural rule:

```text
Start with a view when the data is small and the transformation is light.
Persist as a table only when performance or repeated compute becomes painful.
```

Comparison:

```text
Taxi staging   = high-volume, incremental table
Weather staging = low-volume, simple view
```

---

## Source CTE

```sql
with source as (
    select * from {{ source('bronze', 'raw_weather_hourly') }}
)
```

The model reads from the Bronze source declared in:

```text
dbt/urbanflow/models/sources.yml
```

Current source:

```yaml
sources:
  - name: bronze
    database: URBANFLOW_DB
    schema: BRONZE
    tables:
      - name: raw_weather_hourly
```

Why use `source()`?

```text
It gives dbt lineage and centralizes the physical raw table location.
```

---

## Renamed CTE

```sql
renamed as (
    select
        cast(time as timestamp_ntz) as weather_time,
        cast(temperature_2m as float) as temperature_2m,
        cast(precipitation as float) as precipitation,
        cast(snowfall as float) as snowfall,
        cast(windspeed_10m as float) as windspeed_10m,
        cast(weathercode as integer) as weather_code,
        source_url,
        loaded_at
    from source
)
```

Purpose:

```text
Standardize names and cast raw API fields into reliable analytical types.
```

Important fields:

```text
weather_time    = hourly timestamp grain
temperature_2m  = temperature feature
precipitation   = rainfall amount
snowfall        = snowfall amount
windspeed_10m   = wind feature
weather_code    = WMO weather code
source_url      = API audit trace
loaded_at       = ingestion audit timestamp
```

Why `weather_time` matters:

```text
Taxi trips use pickup_hour_truncated.
Weather uses weather_time.
Those two fields become the hourly join bridge.
```

---

## Final CTE

```sql
final as (
    select
        *,
        {{ classify_weather('weather_code') }} as weather_category,
        case
            when precipitation > 0 or snowfall > 0 then true
            else false
        end as is_precipitation,
        CURRENT_TIMESTAMP() as dbt_updated_at
    from renamed
)
```

Purpose:

```text
Add analyst-ready weather labels and reusable weather flags.
```

Added fields:

```text
weather_category = human-readable weather class
is_precipitation = true when rain or snow is present
dbt_updated_at   = dbt transformation audit timestamp
```

Why `is_precipitation` belongs in Silver:

```text
It creates one standard definition of precipitation for all downstream models.
```

Without this, analysts or Gold models may inconsistently check only rain, only snow, or use different thresholds.

---

## Weather Classification Macro

Macro location:

```text
dbt/urbanflow/macros/classify_weather.sql
```

Current macro:

```sql
{% macro classify_weather(weather_code_column) %}
    case
        when {{ weather_code_column }} in (0, 1, 2, 3) then 'Clear'
        when {{ weather_code_column }} in (45, 48) then 'Fog'
        when {{ weather_code_column }} between 51 and 67 then 'Rain'
        when {{ weather_code_column }} between 71 and 77 then 'Snow'
        when {{ weather_code_column }} between 80 and 82 then 'Showers'
        when {{ weather_code_column }} in (85, 86) then 'Snow Showers'
        when {{ weather_code_column }} >= 95 then 'Thunderstorm'
        else 'Unknown'
    end
{% endmacro %}
```

What the macro does:

```text
Converts numeric WMO weather codes into readable categories.
```

Why use a macro instead of writing the CASE expression directly in the model?

```text
The classification logic becomes reusable.
The model stays readable.
One future change updates all models that use the macro.
```

Mental model:

```text
macro = reusable SQL generator
```

Call site:

```sql
{{ classify_weather('weather_code') }} as weather_category
```

dbt compiles that into a Snowflake `CASE` expression before execution.

---

## Grain and Join Safety

Weather model grain:

```text
one row per weather_time
```

Taxi model join field:

```text
pickup_hour_truncated
```

Expected Gold join pattern:

```sql
taxi.pickup_hour_truncated = weather.weather_time
```

Why uniqueness matters:

```text
If one weather hour appears twice, every taxi trip in that hour can duplicate in the join.
```

That creates false results:

```text
trip counts inflated
revenue inflated
CO2 metrics inflated
demand metrics inflated
```

So the test on `weather_time` is not optional; it protects the entire Gold layer.

---

## Tests

Current tests in:

```text
dbt/urbanflow/models/silver/schema.yml
```

Tested column:

```yaml
- name: weather_time
  tests:
    - unique
    - not_null
```

What these protect:

```text
not_null = every weather row has a timestamp
unique   = one row per hour, preventing join fan-out
```

Potential future tests:

```text
accepted_values on weather_category
not_null on temperature_2m
not_null on precipitation
not_null on weather_code
range checks for physically plausible weather values
```

---

## Audit Fields

The model preserves:

```text
source_url
loaded_at
```

and adds:

```text
dbt_updated_at
```

Meaning:

```text
source_url      = which API request produced the weather data
loaded_at       = when ingestion loaded the record
dbt_updated_at  = when dbt transformed the record
```

This is useful for debugging API coverage and transformation freshness.

---

## Common Commands

Run from:

```bash
cd dbt/urbanflow
```

Run the weather model:

```bash
dbt run --select stg_weather_hourly
```

Build model and tests:

```bash
dbt build --select stg_weather_hourly
```

Build weather model plus dependencies:

```bash
dbt build --select +stg_weather_hourly
```

List compiled lineage:

```bash
dbt ls --select stg_weather_hourly
```

---

## Staff Architect Summary

`stg_weather_hourly` is a small but high-impact model.

It does four jobs:

```text
1. Reads raw hourly weather data through source().
2. Casts API fields into clean analytical types.
3. Converts WMO weather codes into readable categories with a macro.
4. Protects downstream taxi joins with one row per weather hour.
```

The most important idea:

```text
Weather data is small, but its grain controls the correctness of large taxi joins.
```

If weather grain is wrong, Gold metrics can become wrong at scale.

---

## Next File To Study

Next recommended learning note:

```text
04_Silver_Stage_Lookup_zone.md
```

That note should focus on:

```text
dbt/urbanflow/models/silver/stg_zone_lookup.sql
```
