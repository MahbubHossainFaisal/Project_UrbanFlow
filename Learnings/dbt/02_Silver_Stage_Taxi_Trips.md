# Silver Layer Implementation: Staging Taxi Trips
*Date: May 7, 2026*

This document summarizes the architectural decisions and engineering patterns used to transform raw NYC Taxi data into a clean Silver layer model.

---

### 1. The Multi-Step Transformation Flow (CTE Strategy)
We adopted a modular approach using **Common Table Expressions (CTEs)**. This makes the SQL readable, debuggable, and maintainable.

*   **`source`**: The foundation. We always use the `{{ source() }}` function to maintain lineage and resilience.
*   **`casting`**: The translation layer. We ensure data types (INT, FLOAT, TIMESTAMP) are correct before processing.
*   **`deduplicated`**: The uniqueness layer. We use `ROW_NUMBER()` to ensure one record per real-world event.
*   **`filtered`**: The quality layer. We prune "Chaos Data" (negative fares, zero distances) based on empirical profiling.
*   **`enriched`**: The value layer. We add surrogate keys and derived time fields for easier analytics.

---

### 2. Solving the "Invalid Date" Crisis (Microsecond Precision)
**The Problem**: Raw Parquet timestamps were stored in **microseconds**, but were misinterpreted as **seconds**, pushing dates to the year 50,000+.
**The Intuition**: If a date is thousands of years in the future, the scale is likely off by $10^3$ (milliseconds) or $10^6$ (microseconds).
**The Fix**: 
1.  **Extract** the raw epoch seconds.
2.  **Divide** by 1,000,000 to correct the scale.
3.  **Re-cast** to a standard Timestamp.
`TO_TIMESTAMP_NTZ(EXTRACT(EPOCH_SECONDS FROM raw_timestamp) / 1000000)`

---

### 3. Identity & Uniqueness (The Surrogate Key)
**Concept: MD5 Hashing**
Instead of joining tables using 3 or 4 columns (Vendor, Time, Location), we generate a single, unique **Surrogate Key** using the MD5 algorithm.
*   **Intuition**: It acts as a "Social Security Number" for each trip.
*   **Pattern**: `MD5(col1 || '-' || col2 || '-' || col3)`
*   **Benefit**: Faster joins, cleaner code, and deterministic identification.

---

### 4. Deduplication Logic
**Pattern: The Window Function**
We identified that a single taxi (Vendor) cannot be in two places at the same time.
*   **Partition By**: `vendor_id`, `pickup_datetime`, `pickup_location_id`.
*   **Order By**: `loaded_at DESC` (Always keep the latest version of the data).
*   **Filter**: `WHERE row_num = 1`.

---

### 5. Business Rules & Quality Filtering
We defined "Dirty Data" as records that represent physical impossibilities or system errors:
*   **Financials**: `fare_amount > 0` (No free or negative rides).
*   **Physics**: `trip_distance > 0` (The car must have moved).
*   **Reality**: `passenger_count > 0` (A taxi requires at least one passenger to be a "trip").
*   **Temporal**: `pickup < dropoff` (Time cannot move backward) and `duration <= 180 mins` (Filtering out "infinite" trips where meters were left running).

---

### 🎓 The Architect's Takeaway
The Silver layer's primary goal is **Trust**. By the time the data leaves this model, every row must represent a valid, unique, and physically possible trip. We have successfully converted "Chaos Data" into "Trustworthy Assets."

---

### 🚀 Command Breakdown: Executing the Model
To materialize this logic into Snowflake, we used a specific dbt command. Here is the architectural breakdown:

**Command**: `uv run dbt run --select stg_taxi_trips --full-refresh`

1.  **`uv run`**: Ensures dbt runs inside our project's specific virtual environment with the correct dependencies installed.
2.  **`dbt run`**: The core dbt command that compiles your SQL and executes the `CREATE` or `INSERT` statements in Snowflake.
3.  **`--select stg_taxi_trips`**: Tells dbt to only run this specific model. In production, you rarely want to run the "whole world" if you are only fixing one table. This saves time and compute cost.
4.  **`--full-refresh`**: 
    - **Normal Run**: dbt would only look for "New" rows (incremental logic).
    - **Full Refresh**: dbt drops the existing table and rebuilds it from scratch. 
    - **When to use**: Use this when you change your logic (like our microsecond fix) or when you need to "Reset" the data due to a quality issue.

