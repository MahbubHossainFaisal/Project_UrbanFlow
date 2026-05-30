# 04 - Ingestion DAG and DAG-to-DAG Triggering

## Session Focus
This note captures the next orchestration step after the dbt pipeline DAG: separating raw ingestion from dbt transformations.

The chosen production pattern is:

```text
urbanflow_ingestion_pipeline
  -> triggers urbanflow_dbt_pipeline only after ingestion succeeds
```

This keeps ingestion and transformation responsibilities separate while preserving a strict dependency between them.

---

## Why Separate Ingestion and dbt DAGs
Ingestion and dbt have different operational responsibilities.

Ingestion handles:

```text
external sources
downloads and API calls
raw Snowflake table writes
large file behavior
source-specific retry/idempotency concerns
```

dbt handles:

```text
seeds
silver transformations
gold transformations
data tests
```

Keeping them as separate DAGs makes each workflow easier to reason about and operate.

---

## Why dbt Should Be Triggered by Ingestion
Scheduling ingestion and dbt independently can create timing drift.

Example:

```text
ingestion scheduled at 1:00 AM
dbt scheduled at 1:05 AM
```

If ingestion runs slowly and finishes at 1:30 AM, dbt may start too early and transform stale or partial data.

The safer pattern is:

```text
ingestion succeeds
  -> trigger dbt
```

This makes dbt event-driven from the ingestion result instead of clock-driven from an assumed finish time.

---

## Ingestion DAG Shape
The new DAG is:

```text
urbanflow_ingestion_pipeline
```

Current task order:

```text
start
  -> ingest_zone_lookup
  -> ingest_weather
  -> ingest_taxi
  -> trigger_dbt_pipeline
  -> end
```

The first version is sequential on purpose. The jobs write to different raw tables, but sequential ordering keeps the operational story simple while the DAG is still new.

---

## TriggerDagRunOperator
The bridge from ingestion to dbt is Airflow's `TriggerDagRunOperator`.

Conceptually:

```text
When ingestion has succeeded, ask Airflow to create a run of urbanflow_dbt_pipeline.
```

The dbt DAG remains:

```python
schedule=None
```

because it should not run on its own clock. It should run when the ingestion DAG tells it to run.

---

## Failure Propagation Guardrail
The taxi ingestion class has a custom `run()` method for batch processing.

That method previously logged exceptions but did not re-raise them. In Airflow, that is dangerous because a failed ingestion process could exit successfully from the scheduler's point of view.

The fix was to re-raise the exception:

```python
except Exception:
    logger.exception("Snowflake operation failed!")
    raise
```

This ensures Airflow marks `ingest_taxi` as failed if the taxi ingestion process fails.

---

## Current Scheduling Decision
The ingestion DAG is scheduled monthly:

```python
schedule="0 6 15 * *"
```

This means:

```text
Run on the 15th day of each month at 06:00 UTC.
```

The taxi raw loader now checks `SOURCE_FILE` before appending, so rerunning the same file skips the load instead of duplicating data.

Manual trigger params:

```text
taxi_year
taxi_month
```

---

## Parameterized Taxi Source Period
The taxi ingestion script now accepts source-period arguments:

```bash
python -m scripts.data_ingestion.ingestion_taxi_class --year 2023 --month 02
```

The Airflow DAG exposes matching params:

```python
params={
    "taxi_year": "auto",
    "taxi_month": "auto",
}
```

For scheduled runs, `auto` resolves from Airflow's `logical_date`.

Example rendered command:

```bash
cd /opt/airflow && python -m scripts.data_ingestion.ingestion_taxi_class --year 2026 --month 06
```

This lets the operator choose a different taxi source month when manually triggering the ingestion DAG.

The script also normalizes one-digit months:

```text
2 -> 02
```

and rejects invalid years or months before building the source filename.

---

## Taxi Raw Idempotency Guard
The taxi raw table uses append-style loading because the source file is processed in large batches.

To prevent duplicate raw rows, the taxi ingestor now checks whether the file is already present in Snowflake before loading:

```text
RAW_TAXI_TRIPS.SOURCE_FILE = yellow_tripdata_2023-02.parquet
```

If the existing row count is zero:

```text
continue ingestion
```

If the existing row count matches the parquet source row count:

```text
skip ingestion for that file
```

If the existing row count is nonzero but does not match the parquet source row count:

```text
fail the task
```

That final case protects against partial raw loads. It is safer to stop and investigate than to append more rows onto a partially loaded file.

The supporting Snowflake helper is:

```python
SnowflakeClient.count_rows_by_value(...)
```

The taxi ingestor uses:

```python
TaxiIngestor.should_load_source_file(...)
```

Validation against Snowflake showed:

```text
yellow_tripdata_2023-02.parquet existing rows: 2,913,955
should_load_source_file(...): False
```

Meaning:

```text
The file is already loaded and will be skipped on rerun.
```

---

## Validation
The new DAG passed Airflow and container validation:

```text
airflow dags list-import-errors
No data found
```

The registered task tree is:

```text
start
  ingest_zone_lookup
    ingest_weather
      ingest_taxi
        trigger_dbt_pipeline
          end
```

The ingestion DAG and ingestion scripts also passed container-side Python syntax checks.

---

## Next Hardening Step
Monitor whether the source file is available by the scheduled run date:

```text
15th day of the month
06:00 UTC
```

If TLC source availability lags, move the schedule later in the month or adjust the automatic source-period rule.
