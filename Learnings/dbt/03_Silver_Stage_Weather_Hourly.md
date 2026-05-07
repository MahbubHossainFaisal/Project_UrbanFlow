# Silver Layer: Staging Weather Hourly Data

## 1. Architectural Intuition: Time-Series Integrity
Unlike event-based data (Taxi Trips), weather data is **Time-Series** data at a fixed grain (hourly). This requires a specific profiling mindset:

- **Continuity Check**: Verified row counts against the expected timeframe (59 days × 24 hours = 1,416 rows). A gap of even one hour leads to null weather context for thousands of trips in the Gold layer.
- **Grain Integrity**: Confirmed uniqueness of the `TIME` column. Duplicates in weather data would cause "fan-out" in joins, artificially multiplying trip counts and financial metrics.
- **Completeness**: Verified zero nulls in critical columns (`TEMPERATURE_2M`, `PRECIPITATION`, `WEATHERCODE`).

## 2. The Power of dbt Macros (`classify_weather`)
To handle the WMO (World Meteorological Organization) weather codes, we implemented a **Jinja Macro**.

- **Strategic Rationale**:
    - **DRY (Don't Repeat Yourself)**: Classification logic is defined in one place (`macros/classify_weather.sql`) and reused across models.
    - **Abstraction**: Keeps the SQL models clean and readable.
    - **Maintainability**: Changing a category definition (e.g., merging 'Fog' into 'Clear') requires updating only one file.

## 3. Strategic Materialization: Why a `View`?
For the weather data, we chose `materialized='view'` instead of `table` or `incremental`.

| Feature | Taxi Staging (`incremental`) | Weather Staging (`view`) |
| :--- | :--- | :--- |
| **Volume** | ~6 Million Rows | 1,416 Rows |
| **Compute Cost** | High (Heavy deduplication/casting) | Low (Light transformation) |
| **Storage** | Persisted to save compute | Calculated on-the-fly (Metadata only) |
| **Agility** | Changes require `--full-refresh` | Changes are instant via the macro |

**The Architect's Rule**: "Start with a View, persist when it hurts." For small datasets, views are cost-efficient and easier to maintain.

## 4. Feature Engineering for "Analyst-Readiness"
We added the `is_precipitation` boolean flag in the Silver layer.

- **The Logic**: `precipitation > 0 or snowfall > 0`.
- **The Value**:
    - Reduces complexity for downstream analysts.
    - Standardizes the definition of "Bad Weather" across the company.
    - Prevents accidental errors in dashboard queries where analysts might forget to check both rain and snow columns.

## 5. Model Structure
The `stg_weather_hourly.sql` follows the standard dbt CTE pattern:
1.  **`source`**: Reference raw data via `{{ source() }}`.
2.  **`renamed`**: Standardize types and names.
3.  **`final`**: Apply macro-based classification and feature engineering.
