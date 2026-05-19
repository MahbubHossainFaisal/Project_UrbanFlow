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
