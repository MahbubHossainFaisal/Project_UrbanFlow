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
- Visual layer target: Streamlit dashboard

## Latest Known Status
Source of truth used for this summary:
- [2026-05-26_Session_23.md](D:/Project_UrbanFlow/session_docs/session_logs/2026-05-26_Session_23.md)
- [2026-05-27_Session_24.md](D:/Project_UrbanFlow/session_docs/session_logs/2026-05-27_Session_24.md)

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

### Current Focus
- Phase 5: Orchestration & Visual Intelligence
- Sprint 5.2 orchestration foundation is complete.
- Next focus: Sprint 5.3 Streamlit executive dashboard.

### Next Concrete Tasks
- Start Sprint 5.3 Streamlit dashboard planning.
- Define dashboard audience, core KPIs, and first page layout.
- Build Snowflake-backed Streamlit views for demand, financial integrity, and sustainability.
- Keep orchestration hardening for later:
  - add retries and task timeouts
  - add a production schedule
  - remove obsolete `version` from `docker-compose.yml`

## Working Mandates

### Role and Collaboration
- Operate as a STAFF data engineering architect and mentor.
- Maintain a Socratic teaching role: guide the user with questions, prompts, and reasoning before giving direct answers when that helps learning.
- Optimize for production-grade design, clarity, and user growth.
- Use guided discovery where possible, but provide direct implementation when explicitly requested.
- Explain the architectural "why", not just the syntax.

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
