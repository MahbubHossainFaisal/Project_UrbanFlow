# Codex Memory: Project UrbanFlow

## Purpose
This file is the Codex-side working memory for the `Project_UrbanFlow` repository. It captures the active project context, architectural rules, collaboration expectations, and latest known delivery status so future sessions can resume quickly and consistently.

## Current Project State
- Project: `UrbanFlow Analytics`
- Domain: End-to-end urban mobility analytics platform for NYC TLC data
- Architecture: Medallion architecture (`Bronze -> Silver -> Gold`)
- Warehouse: Snowflake
- Transformations: dbt
- Orchestration: Dockerized Airflow
- Visual layer: Streamlit executive dashboard
- Delivery status: Portfolio-grade MVP complete

## Latest Known Status
Source of truth used for this summary:
- [2026-05-26_Session_23.md](D:/Project_UrbanFlow/session_docs/session_logs/2026-05-26_Session_23.md)
- [2026-05-27_Session_24.md](D:/Project_UrbanFlow/session_docs/session_logs/2026-05-27_Session_24.md)
- [2026-05-30_Session_25.md](D:/Project_UrbanFlow/session_docs/session_logs/2026-05-30_Session_25.md)
- [PROJECT_COMPLETION_SUMMARY.md](D:/Project_UrbanFlow/session_docs/PROJECT_COMPLETION_SUMMARY.md)

### Completed
- Modular OOP ingestion framework is complete.
- High-volume ingestion has processed and validated `5,567,311` records.
- Gold layer is production-grade with `36/36` dbt tests passing.
- The legacy timestamp "Epoch Trap" in dbt staging was fixed by removing redundant conversion logic and using direct casting.
- `trip_id` hash grain was hardened by adding `dropoff_datetime`, resolving large-scale key collisions.
- Dockerized Airflow foundation is complete with:
  - `Dockerfile`
  - `docker-compose.yml`
  - Airflow webserver, scheduler, and Postgres services
- Docker Compose hardening pass is complete:
  - Persistent Postgres metadata volume
  - Postgres healthcheck
  - `airflow-init` waits for healthy Postgres
  - webserver and scheduler wait for successful `airflow-init`
  - idempotent `airflow-init` using `airflow db migrate`
  - explicit `.env` injection through `env_file`
- `docker compose config` passed structural validation.
- `requirements.txt` was optimized by removing redundant `apache-airflow`, dramatically reducing build time.
- Dockerized Airflow runtime validation is complete:
  - Postgres is healthy
  - `airflow-init` completes successfully
  - webserver and scheduler run
  - Airflow UI login works at `localhost:8080`
  - Airflow metadata DB connectivity passed
- `urbanflow_smoke_test` DAG succeeded.
- `urbanflow_dbt_smoke_test` DAG succeeded with `dbt_debug -> dbt_ls`.
- `urbanflow_dbt_pipeline` DAG succeeded with:
  - `start`
  - `dbt_debug`
  - `dbt_seed`
  - `dbt_run_silver`
  - `dbt_run_gold`
  - `dbt_test`
  - `end`
- Duplicate-load risk was validated before rerunning the pipeline:
  - `stg_taxi_trips` is incremental with `unique_key='trip_id'`
  - `stg_weather_hourly` is a view
  - `stg_zone_lookup` is a table
  - gold models are table materializations
  - silver/gold tests passed with `PASS=19 WARN=0 ERROR=0 SKIP=0 TOTAL=19`
- Airflow UI task log 403 risk was fixed by pinning `AIRFLOW__WEBSERVER__SECRET_KEY` across Airflow services.
- dbt Snowflake sessions now set `TIMEZONE: UTC` in `profiles.yml` for stable audit timestamp behavior.
- Orchestration learning note added: `Learnings/Orchestration/03_Airflow_dbt_Pipeline_and_Operational_Guardrails.md`.
- `urbanflow_dbt_pipeline` hardening added:
  - one retry per task
  - 5-minute retry delay
  - task-specific execution timeouts
  - `max_active_runs=1`
- Obsolete top-level `version` key removed from `docker-compose.yml`.
- `urbanflow_ingestion_pipeline` DAG added with:
  - `start`
  - `ingest_zone_lookup`
  - `ingest_weather`
  - `ingest_taxi`
  - `trigger_dbt_pipeline`
  - `end`
- `urbanflow_ingestion_pipeline` uses `TriggerDagRunOperator` to trigger `urbanflow_dbt_pipeline` only after ingestion succeeds.
- `ingestion_taxi_class.py` now re-raises exceptions so Airflow correctly fails the task if taxi ingestion fails.
- Taxi raw ingestion idempotency is now guarded:
  - `SnowflakeClient.count_rows_by_value()` checks existing rows by `SOURCE_FILE`
  - `TaxiIngestor.should_load_source_file()` skips fully loaded source files
  - partial source-file loads raise an error instead of appending more rows
  - validated against Snowflake for `yellow_tripdata_2023-02.parquet`: existing row count `2,913,955`; guard returned `False`
- Taxi ingestion source period is parameterized:
  - `ingestion_taxi_class.py` supports `--year` and `--month`
  - month values are normalized to two digits
  - invalid years/months raise validation errors
  - `urbanflow_ingestion_pipeline` exposes `taxi_year` and `taxi_month` params
  - automatic scheduled command uses the Airflow `logical_date` year/month
  - rendered example for `2026-06-15`: `python -m scripts.data_ingestion.ingestion_taxi_class --year 2026 --month 06`
- Production schedule applied:
  - `urbanflow_ingestion_pipeline` schedule is `0 6 15 * *`
  - the ingestion DAG is unpaused
  - `urbanflow_dbt_pipeline` remains `schedule=None` and is triggered by the ingestion DAG
- Streamlit executive dashboard foundation added:
  - file: `streamlit_app.py`
  - dependency: `streamlit`
  - command: `uv run streamlit run streamlit_app.py`
  - local URL: `http://localhost:8501`
  - Snowflake-backed overview KPIs: trips, revenue, average fare, CO2, price anomalies, distance, duration, precipitation share, and short-efficiency-risk trips
  - overview visuals: demand by borough, hourly demand, weather demand mix, airport fare watchlist
  - default date bounds use meaningful daily trip volume to avoid stray historical timestamp outliers
- Project close-out docs added:
  - `session_docs/PROJECT_COMPLETION_SUMMARY.md`
  - `session_docs/session_logs/2026-05-30_Session_25.md`
- Final portfolio presentation package added:
  - `session_docs/final_presentation/README.md`
  - `session_docs/final_presentation/PROJECT_ONE_PAGER.md`
  - `session_docs/final_presentation/PRESENTATION_OUTLINE.md`
  - `session_docs/final_presentation/ARCHITECTURE_WALKTHROUGH.md`
  - `session_docs/final_presentation/DEMO_SCRIPT.md`
- New ingestion DAG validation passed:
  - `airflow dags list-import-errors`: no data found
  - `airflow tasks list urbanflow_ingestion_pipeline --tree`: expected task chain
  - container `py_compile` check passed for the ingestion DAG and ingestion scripts

### Current Focus
- Project mastery phase.
- Portfolio-grade MVP is complete.
- Final portfolio presentation package is prepared.
- The current goal is to understand the project deeply enough to explain the architecture, code, data relationships, operational decisions, and tradeoffs without relying on new implementation work.

### Next Concrete Tasks
- Learn the project from first principles, layer by layer.
- Review each major concept, file, relationship, and execution path.
- Practice explaining the system through interview-style and architecture-review questions.
- Build confidence through oral/written reconstruction rather than adding new code.
- Defer new feature work unless the user explicitly asks to resume implementation.

## Working Mandates

### Role and Collaboration
- Operate as a STAFF data engineering architect and mentor.
- Maintain a Socratic teaching role: guide the user with questions, prompts, and reasoning before giving direct answers when that helps learning.
- Optimize for production-grade design, clarity, and user growth.
- Use guided discovery where possible, but provide direct implementation when explicitly requested.
- Explain the architectural "why", not just the syntax.
- During the project mastery phase, default to teaching and questioning instead of coding.
- Help the user learn every concept, code path, model relationship, and operational decision until they can defend the project independently.
- Prefer first-principles explanations, diagrams, mental models, and interview-style practice.
- If the user asks for an answer, give the answer, then ask one strong follow-up question to test understanding.

### Core Engineering Rules
- Always think architecture-first before implementation.
- Every technical decision should have a business, trust, or performance rationale.
- Prefer explicit behavior over implicit behavior.
- Be cost-aware, especially for Snowflake compute.
- Treat documentation as part of delivery, not an afterthought.

### Verification Loop
- No task is complete until it is validated.
- Preferred validation includes commands like `dbt build`, tests, or runtime verification relevant to the change.
- Trust results only after execution and checks pass at realistic scale.

### Ingestion Standards
- Ingestion logic should live in classes inheriting from `BaseIngestor`.
- Database work should use the `SnowflakeClient` context manager.
- Data typing and quality enforcement belong in the `transform()` step.
- Ingestion changes should be verified against downstream dbt behavior, not only local script success.

### Orchestration Standards
- Scheduled jobs should run inside the Dockerized Airflow environment.
- Use volume mounts for `dags/`, `scripts/`, and `dbt/` to keep dev and runtime synchronized.

### Documentation Standards
- Capture reusable patterns and architectural lessons in `Learnings/`.
- Keep project status synchronized when major milestones shift.
- Avoid duplicating detailed learning content in session logs. Session logs should capture operational handoff only: work completed, files changed, validation result, current status, and exact resume point. Detailed explanations belong in `Learnings/`.

### Naming and Diagram Rules
- Snowflake objects should be `UPPERCASE`.
- dbt model names should be lowercase.
- Mermaid technical diagrams should stay readable, minimal, and aligned with the current project documentation style.

## Session-End Protocol To Follow
When the user is wrapping up for the day:
- Generate/update the session log
- Capture new learnings in `Learnings/`
- Synchronize project memory files such as `README.md` and `MEMORY.md` as needed
- Keep session logs concise and non-redundant with `Learnings/`

## Codex Operating Notes
- This file is repository memory, not global model memory.
- If project direction changes, update this file alongside the relevant session log.
- Prefer reading this file first at the start of future UrbanFlow sessions.
