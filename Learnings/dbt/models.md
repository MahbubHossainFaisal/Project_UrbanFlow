# dbt Models: From Discovery to Architectural Implementation

This document serves as a comprehensive guide for designing and building dbt models, covering the theoretical discovery phase and the practical implementation patterns.

---

## 1. The Art of Transformation Discovery
Before writing SQL, a Data Architect must discover the requirements through four pillars:

### I. Domain Knowledge (The "Physical World" Check)
*   **Definition**: Understanding the real-world system generating the data.
*   **Example**: Taxi trips cannot have negative fares or 0 miles.
*   **Result**: Hard filters (e.g., `WHERE fare_amount > 0`).

### II. Business Questions (Working Backwards)
*   **Definition**: Ensuring the data supports the final stakeholder requirements.
*   **Example**: To answer "Demand by Weather," we must truncate taxi timestamps to the hour to match weather data.
*   **Result**: Join keys (e.g., `DATE_TRUNC('hour', pickup_time)`).

### III. Data Profiling (The "Finding the Garbage" Phase)
*   **Definition**: Interrogating raw data for glitches, duplicates, and nulls.
*   **Example**: Finding duplicate records due to ingestion retries.
*   **Result**: Deduplication logic (e.g., `ROW_NUMBER()`).

### IV. Engineering Standards (Architectural Integrity)
*   **Definition**: Applying best practices for performance and maintainability.
*   **Example**: Using Surrogate Keys instead of multi-column joins.
*   **Result**: Surrogate Keys (e.g., `MD5(CONCAT(...))`) and Audit Columns.

---

## 2. Strategic Learning: The "T-Shaped" Approach
When learning a new tool like dbt, we follow the **T-Shaped Strategy**:
*   **Vertical Bar (Depth)**: Focus on the specific implementation needed for the task (e.g., Incremental loads for high-volume taxi data).
*   **Horizontal Bar (Breadth)**: Once the task is done, explore alternative methods (e.g., Views vs. Tables) to understand the trade-offs.

### The Representative Pattern
To achieve **100% dbt Core Coverage** within a single project, we deliberately apply different features to different models:
*   **Taxi**: Incremental (High Volume).
*   **Weather**: Table + Macros (Logic & Reusability).
*   **Zones**: View (Static Reference).

---

## 3. dbt Materialization Types
Materializations are strategies for persisting dbt models in the warehouse.

| Type | How it works | When to use it |
| :--- | :--- | :--- |
| **View** | Logic is stored; runs every time it's queried. | Small datasets, simple renames, or when you don't want to store data. |
| **Table** | Drops and recreates the physical table every run. | Medium datasets where logic changes often. |
| **Incremental** | Inserts only new rows since the last run. | **Large datasets** (like 6M taxi rows) to save time and compute cost. |
| **Ephemeral** | Code is "pasted" as a CTE into downstream models. | Internal code cleanup; never appears in the warehouse. |

---

## 4. The Silver Layer Blueprint (The CTE Pattern)
To ensure readability and modularity, every Silver model should follow a standardized CTE structure:

1.  **`source`**: The initial `SELECT *` from the `{{ source() }}` or `{{ ref() }}`.
2.  **`casting`**: Standardizing data types (e.g., `CAST(x AS FLOAT)`).
3.  **`deduplicated`**: Ensuring row uniqueness using Window Functions.
4.  **`filtered`**: Applying business rules and removing "garbage" records.
5.  **`enriched`**: Adding surrogate keys and derived features (e.g., durations, hours).
6.  **`final`**: The clean select of only the required columns.

---

## 5. Incremental Materialization Logic
Incremental models require two key components:
1.  **A Unique Key**: (e.g., `trip_id`) to tell dbt which rows to update vs. insert.
2.  **An Audit Filter**: `{% if is_incremental() %}` logic using an audit column (e.g., `loaded_at`) to only grab the newest data from the source.

---
*Created during Session 6: May 4, 2026*
