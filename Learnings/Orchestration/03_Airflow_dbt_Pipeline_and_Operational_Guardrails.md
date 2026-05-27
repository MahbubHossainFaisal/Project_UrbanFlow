# 03 - Airflow dbt Pipeline and Operational Guardrails

## Session Focus
This note captures the transition from dbt readiness to a real Airflow-orchestrated dbt pipeline for UrbanFlow.

The goal was to prove that Airflow can run the UrbanFlow dbt workflow in ordered phases:

```text
start
  -> dbt_debug
  -> dbt_seed
  -> dbt_run_silver
  -> dbt_run_gold
  -> dbt_test
  -> end
```

This is still a manually triggered validation DAG, not a production schedule.

---

## Why Start With a dbt Smoke DAG
Before building the full pipeline DAG, we created a smaller dbt smoke DAG:

```text
dbt_debug -> dbt_ls
```

This answered one narrow question:

```text
Can Airflow run dbt commands from inside the Dockerized runtime?
```

`dbt_debug` proved the profile, project, adapter, Git dependency, and Snowflake connection were available inside the Airflow container.

`dbt_ls` proved Airflow could run a dbt project command and parse/list resources.

This avoided mixing orchestration validation with model build cost and downstream data quality concerns.

---

## Why Split the Real Pipeline Into Phases
The first real pipeline could have been a single task:

```text
dbt build
```

Instead, it was split into separate tasks:

```text
dbt_debug
dbt_seed
dbt_run_silver
dbt_run_gold
dbt_test
```

The operational reason is failure isolation.

If one `dbt build` task fails, Airflow only says the build task failed. The engineer must inspect a large log to discover whether the failure came from seeds, silver models, gold models, or tests.

With phased tasks, the Airflow graph shows the failure boundary directly:

```text
dbt_seed failed       -> seed/reference loading issue
dbt_run_silver failed -> staging/source/model issue
dbt_run_gold failed   -> downstream dimensional/fact issue
dbt_test failed       -> data quality issue
```

This makes the DAG easier to explain, operate, and debug.

---

## dbt Path Selectors
The DAG uses dbt path selectors:

```bash
dbt run --select path:models/silver
dbt run --select path:models/gold
```

These paths are relative to the dbt project root.

Inside the Airflow container, the dbt project root is:

```text
/opt/airflow/dbt/urbanflow
```

So this command:

```bash
cd /opt/airflow/dbt/urbanflow && dbt run --select path:models/silver
```

means:

```text
Go to the dbt project root.
Run every model under models/silver.
```

It does not point to a Windows path. It points to the dbt project folder as seen from inside the container.

---

## Duplicate-Load Validation
Before rerunning the pipeline against existing Snowflake data, we validated whether the DAG could duplicate silver or gold rows.

The materialization review showed:

```text
stg_taxi_trips       incremental, unique_key='trip_id'
stg_weather_hourly   view
stg_zone_lookup      table
gold models          table
```

The only realistic duplicate risk was `stg_taxi_trips`, because it is incremental.

That model uses:

```python
materialized='incremental'
unique_key='trip_id'
on_schema_change='fail'
```

The `unique_key` tells dbt how to match existing rows during incremental updates. This avoids blind append behavior for existing `trip_id` values.

The gold layer uses table materializations, so gold relations are rebuilt instead of appended.

We also ran the existing silver/gold dbt tests and confirmed:

```text
PASS=19 WARN=0 ERROR=0 SKIP=0 TOTAL=19
```

Important duplicate-related tests included:

```text
unique_stg_taxi_trips_trip_id
unique_gold_fact_trips_trip_id
unique_gold_agg_demand_weather_agg_id
unique_dim_calendar_date_id
```

---

## Audit Timestamp Lesson
The user noticed Snowflake displaying timestamps like:

```text
2026-05-27 03:14:28.936 -0700
```

The important interpretation is that this is a timestamp with a timezone offset, not a wrong pipeline time.

Bangladesh time is UTC+6. A value displayed as `-0700` is 13 hours behind Bangladesh time.

So:

```text
2026-05-27 03:14:28.936 -0700
```

corresponds to:

```text
2026-05-27 16:14:28.936 Asia/Dhaka
```

The production lesson:

```text
Store processing audit timestamps consistently.
Convert to local business time in the query or dashboard layer.
```

For dbt runs, we set the Snowflake session timezone in `profiles.yml`:

```yaml
session_parameters:
  TIMEZONE: UTC
```

This keeps dbt execution behavior stable without changing the existing incremental model column type.

---

## Incremental Schema Guardrail
During timestamp cleanup, a failed run exposed an important dbt guardrail:

```text
on_schema_change='fail'
```

The attempted timestamp expression changed the inferred type of `DBT_UPDATED_AT` in the incremental `stg_taxi_trips` model.

dbt stopped the run instead of silently changing the target table schema.

This was correct behavior.

The fix was not to force a full refresh or relax schema controls. The safer fix was:

```text
Keep the audit expression type compatible.
Set the dbt Snowflake session timezone to UTC.
```

After that, the failed silver command passed:

```text
dbt run --select stg_taxi_trips
SUCCESS 5567311
```

and then:

```text
dbt run --select path:models/silver
PASS=3 ERROR=0
```

---

## Airflow Log 403 Lesson
The Airflow UI showed:

```text
Could not read served logs: 403 FORBIDDEN
```

This was separate from the dbt failure.

Airflow task logs are served with signed URLs. If the webserver and scheduler use different generated secret keys, the webserver can reject scheduler-served log URLs.

The fix was to pin the same local development secret key across Airflow services:

```yaml
AIRFLOW__WEBSERVER__SECRET_KEY=urbanflow-local-dev-secret-key
```

This was added to:

```text
airflow-webserver
airflow-scheduler
airflow-init
```

The stack must be restarted for this setting to take effect.

---

## Final Validated State
The following DAGs now exist:

```text
urbanflow_smoke_test
urbanflow_dbt_smoke_test
urbanflow_dbt_pipeline
```

The main dbt pipeline DAG completed successfully:

```text
start
  -> dbt_debug
  -> dbt_seed
  -> dbt_run_silver
  -> dbt_run_gold
  -> dbt_test
  -> end
```

This proves:

```text
Airflow can orchestrate dbt.
dbt can transform Snowflake data from Airflow.
Seeds, silver models, gold models, and tests run in order.
The Dockerized orchestration foundation is complete.
```

---

## Deferred Hardening
The following items are intentionally deferred:

```text
Add retries and task timeouts.
Add a production schedule.
Remove the obsolete docker-compose.yml version key.
```

These are hardening tasks. They are not blockers for the current orchestration foundation milestone.
