# Learning: High-Volume Batching & Defensive Typing

## 🛡️ The Challenge: The "Boss Fight" of Ingestion
Ingesting millions of rows (like NYC Taxi data) introduces risks that simple APIs or CSVs don't have:
1.  **Memory Exhaustion (OOM)**: Loading 3M+ rows into a single DataFrame can crash the execution environment.
2.  **Serialization Drift**: Data types that look correct in Pandas can be "silently" converted during bulk upload (e.g., Timestamps becoming Integers).
3.  **SQl Identification**: Case sensitivity in column names can cause SQL compilation errors.

## 🏗️ The "Elite" Solution: Batch-Aware Ingestors
We refactored the Taxi Ingestor to use an iterative batching strategy while maintaining the "Elite Framework" standards.

### 1. Overriding the Template Method
While the `BaseIngestor` provides a standard `run()`, high-volume jobs may need to **override** it to implement a loop.
*   **Technique**: Use `pyarrow.parquet.ParquetFile.iter_batches()` to process data in chunks (e.g., 500,000 rows at a time).
*   **Result**: Constant memory usage regardless of total file size.

### 2. Defensive Type Casting (The "Nuclear Option")
To prevent the **Epoch Trap** (Timestamps becoming numbers), we implemented ISO string conversion.
```python
batch_df['TPEP_PICKUP_DATETIME'] = batch_df['TPEP_PICKUP_DATETIME'].dt.strftime("%Y-%m-%d %H:%M:%S")
```
*   **Architect's Insight**: While string conversion is slightly more CPU-intensive, it is the most resilient way to ensure Snowflake recognizes the data as a `TIMESTAMP_NTZ`. In production, reliability often trumps minor performance gains.

### 3. Defensive Casing
To avoid SQL Compilation errors (`invalid identifier '"airport_fee"'`), we forced all column names to uppercase:
```python
batch_df.columns = [c.upper() for c in batch_df.columns]
```
*   **Rationale**: Snowflake identifiers are case-insensitive when unquoted, but `write_pandas` often uses quotes. Forcing uppercase ensures the identification always matches Snowflake's default behavior.

## 🧠 Architect's Insight: Framework Evolution
The best frameworks are **Evolutionary**.
*   We updated our `database.py` and `base_ingestor.py` to **return row counts**.
*   This was a **Backward-Compatible** change—it helped the Taxi Ingestor track progress without breaking the simpler Zone or Weather ingestors.

**Key Takeaway**: "A senior architect doesn't just build a path for the easy data; they build a system that can handle the volume, variety, and velocity of the hardest data."

---

## 🔗 The Post-Ingestion Synchronicity (The dbt Handshake)
After "winning the boss fight" of ingestion, we discovered that **the dbt layer must also evolve to match the hardened source.**

### 1. The "Double Transformation" Trap
*   **The Scenario**: Our new ingestor was already casting timestamps to `YYYY-MM-DD`. However, our legacy dbt model was still applying "Epoch math" (dividing by 1,000,000) on top of the already-correct values.
*   **The Result**: 3.5 million trips were compressed into the first 30 minutes of January 1st, 1970.
*   **The Fix**: Simplify the dbt layer. If the ingestor is "Elite," the staging model should be a **Direct Cast**, not a logic re-implementation.

### 2. Hardening the Unique Key (Grain Refinement)
*   **The Discovery**: Using only `vendor_id`, `pickup_datetime`, and `pickup_location_id` as a hash resulted in 400,000+ collisions at high volumes.
*   **Architectural Intuition**: As data volume increases, the "Uniqueness Grain" must become finer. Adding `dropoff_datetime` to the MD5 hash provided the necessary cardinality to support millions of rows.
```sql
MD5(vendor_id || '-' || pickup_datetime || '-' || dropoff_datetime || '-' || pickup_location_id)
```

### 3. The "Verification Loop" Protocol
*   **Mandate**: Never automate a pipeline based on a "successful" script run alone.
*   **Verification**: Always run `dbt build` (Execution + Tests) before orchestration. In our case, this step caught the timestamp corruption and duplicate IDs **before** we automated them into Airflow.

**Architect's Note**: "Automating a validated pipeline is Architecture; automating an unverified one is just speeding up the chaos."
