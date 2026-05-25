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
- [2026-05-24_Session_21.md](D:/Project_UrbanFlow/session_docs/session_logs/2026-05-24_Session_21.md)
- [2026-05-25_Session_22.md](D:/Project_UrbanFlow/session_docs/session_logs/2026-05-25_Session_22.md)

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
- Next runtime validation is pending: start the stack and verify Airflow UI at `localhost:8080`.
- `requirements.txt` was optimized by removing redundant `apache-airflow`, dramatically reducing build time.

### Current Focus
- Phase 5: Orchestration & Visual Intelligence
- Sprint 5.2: Dockerized Airflow runtime validation, then DAG development and scheduling

### Next Concrete Tasks
- Run `docker compose up --build`
- Verify `airflow-init`, webserver, scheduler, and Airflow UI login
- Create a minimal proof DAG
- Build `dags/urbanflow_master_dag.py`
- Configure Airflow connections for Snowflake and API credentials
- Implement dependency chain: `Ingest -> dbt build`
- Start Sprint 5.3 Streamlit dashboard work after DAG orchestration is stable

## Working Mandates

### Role and Collaboration
- Operate as a STAFF data engineering architect and mentor.
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
