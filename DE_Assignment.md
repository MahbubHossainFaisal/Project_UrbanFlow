# Data Engineering Assignment: End-to-End Real-World Pipeline
## "NYC Taxi & Weather Analytics Platform"

---

> **A Note Before You Begin**
>
> This is not a tutorial. This is an assignment designed to make you *think*, *fail*, *debug*, and *understand* — exactly like a real data engineering job. You will be given context, guidance, constraints, and validation criteria. You will **not** be given code. Every decision you make — from folder structure to data modeling — you will own. That is what data engineers do.

---

## Table of Contents

1. [The Business Scenario](#1-the-business-scenario)
2. [The Problem Statement](#2-the-problem-statement)
3. [Architecture & Workflow Design](#3-architecture--workflow-design)
4. [Tools Required](#4-tools-required)
5. [Core Concepts Per Tool](#5-core-concepts-per-tool)
6. [Real World Raw Data Sources](#6-real-world-raw-data-sources)
7. [Project Structure & Directory Layout](#7-project-structure--directory-layout)
8. [Phase-by-Phase Implementation Guide](#8-phase-by-phase-implementation-guide)
9. [Validation & Verification Guidelines](#9-validation--verification-guidelines)
10. [Deliverables Checklist](#10-deliverables-checklist)

---

## 1. The Business Scenario

You have just joined **UrbanFlow Analytics**, a mid-sized data consultancy that works with city transportation authorities. Their client, the **NYC Taxi & Limousine Commission (TLC)**, wants to understand how **weather conditions** directly affect taxi demand patterns across New York City boroughs.

The client's business questions are:

- On rainy or snowy days, does taxi pickup demand spike in certain boroughs more than others?
- What time windows (morning rush, afternoon, night) show the highest weather-correlated demand shifts?
- Which pickup zones become "surge zones" under bad weather?
- How does trip duration and fare change under different weather conditions?

The client wants a **daily-refreshed analytics dashboard** backed by clean, modeled, tested data. They need to trust the data completely — meaning every number must be verifiable.

Your job as the data engineer: **Build the end-to-end data pipeline** from raw data ingestion to clean analytics-ready tables. The data scientists and analysts will query the final tables. You are responsible for everything before that.

---

## 2. The Problem Statement

### What you are dealing with:

**Source 1 — NYC Taxi Trip Records (Structured, large Parquet files)**
- Contains millions of rows per month
- Columns include: pickup/dropoff timestamps, location IDs, passenger count, trip distance, fare amount, payment type, tip, tolls, etc.
- Known data quality issues: null values, negative fares, trips with 0 distance, future timestamps, impossible coordinates, duplicates

**Source 2 — Open-Meteo Historical Weather API (Semi-structured JSON)**
- Free weather API with hourly historical weather data
- Contains: temperature, precipitation, wind speed, snowfall, weather code (WMO standard)
- You will need to fetch this programmatically and store it

**Source 3 — NYC TLC Zone Lookup Table (Small CSV)**
- Maps `LocationID` (integer) to Borough name and Zone name
- Essential for joining taxi data to geography

### What you must build:

A **multi-layered data pipeline** (Bronze → Silver → Gold architecture) that:

1. Ingests raw taxi data and weather data
2. Cleans and validates the data
3. Joins and enriches datasets
4. Models the data into analytics-ready tables
5. Runs on a schedule via Airflow
6. Is fully tested via dbt tests
7. Runs in a reproducible environment via Docker

---

## 3. Architecture & Workflow Design

### 3.1 The Medallion Architecture (Bronze → Silver → Gold)

This is the industry-standard layered architecture used by companies like Databricks, Snowflake, and most modern data teams. You **must** follow this. Here is what each layer means and why it exists:

```
RAW SOURCES
    │
    ▼
┌─────────────────────────────────────────┐
│              BRONZE LAYER               │
│  - Raw data, loaded as-is               │
│  - No transformations                   │
│  - Append-only                          │
│  - Acts as your source of truth         │
│  - If something breaks downstream,      │
│    you re-process from Bronze           │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│              SILVER LAYER               │
│  - Cleaned, validated, deduplicated     │
│  - Standardized column names/types      │
│  - Nulls handled, outliers flagged      │
│  - Still row-level (one row per trip)   │
│  - Business rules applied               │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│               GOLD LAYER                │
│  - Aggregated, analytics-ready          │
│  - Joined across sources                │
│  - Dimensional model (facts & dims)     │
│  - What analysts/dashboards query       │
│  - Optimized for read performance       │
└─────────────────────────────────────────┘
```

### 3.2 Why This Architecture Exists

In real data engineering, data sources break, APIs return garbage, upstream systems change schemas without warning. If you transform data in one step and something goes wrong, you lose everything. The medallion architecture gives you **recovery points**. Bronze is never touched after loading. If Silver breaks, you re-run from Bronze. If Gold breaks, you re-run from Silver.

### 3.3 Full System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATION LAYER                       │
│                     Apache Airflow (in Docker)                   │
│                                                                   │
│   DAG: ingest_taxi_data  ──►  DAG: ingest_weather_data           │
│              │                         │                          │
│              └──────────┬──────────────┘                          │
│                         ▼                                         │
│                 DAG: run_dbt_pipeline                             │
└───────────────────────────────────────────────────────────────────┘
         │               │               │
         ▼               ▼               ▼
  [Python Script]  [Python Script]  [dbt run + test]
  Download Taxi    Fetch Weather     Transform &
  Parquet → SF     JSON → Snowflake  Model Data
  (Bronze)         (Bronze)          (Silver → Gold)
         │               │               │
         └───────────────┴───────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │      SNOWFLAKE       │
              │                      │
              │  DB: URBANFLOW       │
              │  ├── SCHEMA: BRONZE  │
              │  ├── SCHEMA: SILVER  │
              │  └── SCHEMA: GOLD    │
              └──────────────────────┘
```

### 3.4 Workflow Execution Order

Every day (or in your case, when you trigger manually for a given month), the pipeline runs in this exact order:

```
Step 1: Airflow triggers DAG
Step 2: Python extracts NYC Taxi Parquet for target month → loads to Snowflake BRONZE schema
Step 3: Python fetches weather JSON for target month → loads to Snowflake BRONZE schema
Step 4: Airflow waits for Steps 2 & 3 to complete (dependency management)
Step 5: dbt runs Silver models (clean + validate data in Snowflake)
Step 6: dbt tests run on Silver models (fail fast if data is bad)
Step 7: dbt runs Gold models (aggregate + join in Snowflake)
Step 8: dbt tests run on Gold models
Step 9: Airflow marks DAG as SUCCESS or FAILURE and logs results
```

This is a real production workflow. Not simulated.

---

## 4. Tools Required

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.10+ | Data ingestion scripts, API calls, file handling |
| **SQL** | Standard | All transformations inside Snowflake |
| **dbt Core** | 1.7+ | Data transformation framework (Silver + Gold layers) |
| **Apache Airflow** | 2.8+ | Pipeline orchestration and scheduling |
| **Snowflake** | Free trial | Cloud data warehouse (all data lives here) |
| **Docker** | Latest | Containerized, reproducible environment for Airflow |

---

## 5. Core Concepts Per Tool

This section is critical. Before you write a single line of code for each tool, you must understand these concepts. These are the things interviewers test you on.

---

### 5.1 Python — What You Must Know For This Project

#### Concept 1: Working with large files without loading everything into memory

Taxi files are hundreds of megabytes. If you use `pd.read_parquet("file.parquet")` on a massive file, you might crash your local memory. You need to understand **chunked reading** (or reading by row groups in Parquet using `pyarrow`) — processing the file in pieces and loading each chunk to Snowflake before moving to the next.

*Why this matters:* In real pipelines, data is always too big to fit in memory. This is day-one knowledge.

#### Concept 2: Working with REST APIs and pagination

The Open-Meteo API returns JSON. You need to understand:
- How to make HTTP GET requests with parameters
- How to handle the response (status codes, parsing JSON)
- What happens when an API call fails (retry logic)
- How to structure your API call to get data for a date range

*Why this matters:* At least 40% of real data engineering work involves pulling data from APIs.

#### Concept 3: Environment variables and secrets management

You will never hardcode your Snowflake password, account identifier, or API keys in your Python files. Ever. You use environment variables loaded from a `.env` file (which is in `.gitignore`). You use the `python-dotenv` library.

*Why this matters:* It's a security fundamental. Any code review will fail you for hardcoded credentials.

#### Concept 4: Snowflake Connector for Python

Snowflake has an official Python connector (`snowflake-connector-python`). You need to understand:
- How to establish a connection
- How to execute SQL statements from Python
- How to use `write_pandas()` to bulk-load a DataFrame into Snowflake efficiently
- The concept of a **stage** in Snowflake (a temporary storage location used for bulk loading)

#### Concept 5: Logging (not print statements)

In production, no one uses `print()`. You use Python's `logging` module. This gives you log levels (DEBUG, INFO, WARNING, ERROR), timestamps, and the ability to write logs to files. Every ingestion script must log: when it started, how many rows it processed, whether it succeeded or failed.

*Why this matters:* When a pipeline fails at 3 AM, logs are how you diagnose what went wrong.

---

### 5.2 SQL — What You Must Know For This Project

#### Concept 1: Window Functions

You will heavily use window functions in your Silver and Gold models. Specifically:
- `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` — for deduplication
- `LAG()` / `LEAD()` — for comparing a row to the previous/next row
- `RANK()` — for ranking zones by demand

*Why this matters:* Window functions are the most tested SQL concept in data engineering interviews. Master them.

#### Concept 2: CTEs (Common Table Expressions)

All your dbt models will be structured as CTEs. A CTE is a named subquery defined at the top of a SQL statement using `WITH`. They make complex SQL readable and debuggable. Every professional data engineer writes SQL as a chain of CTEs.

Structure your SQL like:
```
WITH source AS (...),
     cleaned AS (...),
     deduplicated AS (...),
     final AS (...)
SELECT * FROM final
```

#### Concept 3: Date/Time Manipulation in Snowflake

You'll need to:
- Extract hour, day of week, month from timestamps
- Truncate timestamps to the hour (for joining weather data, which is hourly)
- Convert between timezones (taxi data is in UTC, you'll present in Eastern Time)
- Use `DATE_TRUNC()`, `TO_TIMESTAMP()`, `CONVERT_TIMEZONE()`, `EXTRACT()`

#### Concept 4: Joining Strategies

You'll join taxi trips to weather using `pickup_datetime` truncated to the hour. You need to understand:
- When to use INNER JOIN vs LEFT JOIN and why (hint: LEFT JOIN is almost always safer in analytics pipelines)
- How to handle fan-out (one-to-many joins creating duplicate rows — a common bug)
- How to validate that your join didn't multiply rows unexpectedly

#### Concept 5: Incremental vs Full Refresh Loading

- **Full refresh**: Truncate the table and reload everything every run. Simple but slow for large data.
- **Incremental**: Only process new data since the last run. Uses a "watermark" (like `max(loaded_at)`) to know where to start.

*Why this matters:* In production with terabytes of data, you cannot full-refresh daily. Incremental loading is a core skill.

---

### 5.3 dbt — What You Must Know For This Project

#### Concept 1: What dbt Actually Does

dbt does NOT move data. It only runs SQL `SELECT` statements inside your warehouse and materializes the results into tables or views. Think of it as a framework for organizing, running, and testing your SQL transformations. Your Python scripts move data into Bronze. dbt transforms Bronze → Silver → Gold using SQL that runs *inside Snowflake*.

#### Concept 2: Materializations

Every dbt model has a materialization type:
- `view` — runs the SQL every time someone queries it; no data is stored; cheapest
- `table` — runs the SQL and stores the result as a physical table; queried directly
- `incremental` — like table, but only processes new rows on subsequent runs
- `ephemeral` — like a CTE injected into other models; never materialized

For this project:
- Bronze tables: loaded by Python (dbt doesn't touch Bronze)
- Silver models: `incremental` (process only new trips)
- Gold models: `table` (re-aggregate daily)

#### Concept 3: Sources and Refs

In dbt, you reference raw tables using `{{ source('schema_name', 'table_name') }}`. You reference other dbt models using `{{ ref('model_name') }}`. **Never hardcode schema or table names in your SQL.** This is how dbt builds its dependency graph (DAG) and knows the order to run models.

#### Concept 4: dbt Tests — Generic and Singular

dbt has two types of tests:

**Generic tests** (defined in YAML):
- `not_null` — column cannot have nulls
- `unique` — column values must be unique
- `accepted_values` — column can only contain a list of specified values
- `relationships` — foreign key integrity (e.g., every `location_id` in trips must exist in the zone lookup)

**Singular tests** (custom SQL files in `tests/` folder):
- You write a SQL query that returns rows that FAIL the test
- If 0 rows are returned, the test passes
- Example: "Find all trips where fare is negative" — should return 0 rows in Silver

#### Concept 5: dbt Documentation and Lineage

Every model and column should have a description in YAML files. `dbt docs generate` + `dbt docs serve` creates an interactive documentation site with a full lineage graph showing how data flows. This is what professional teams use to understand their data.

#### Concept 6: Jinja Templating in dbt

dbt models support Jinja templating. Key uses:
- `{{ ref() }}` and `{{ source() }}` as covered above
- `{{ config(...) }}` to set materialization per model
- `{% if is_incremental() %}` to add WHERE clauses only when doing incremental runs
- `{{ var('execution_date') }}` to pass variables from Airflow

---

### 5.4 Apache Airflow — What You Must Know For This Project

#### Concept 1: What is a DAG?

DAG stands for **Directed Acyclic Graph**. In Airflow, a DAG is a Python file that defines:
- What tasks to run
- In what order (dependencies between tasks)
- On what schedule
- What to do on failure (retry? alert? skip?)

The "Directed" means tasks flow in one direction. "Acyclic" means no circular dependencies (Task A cannot depend on Task B if Task B depends on Task A).

#### Concept 2: Operators

Each task in a DAG is defined by an Operator. Key operators for this project:
- `PythonOperator` — runs a Python function
- `BashOperator` — runs a shell command (you'll use this to run `dbt run`)
- `SnowflakeOperator` — runs SQL directly in Snowflake (optional but useful)

#### Concept 3: Task Dependencies

You set dependencies using `>>` (bitshift operator):
```python
task_ingest_taxi >> task_ingest_weather >> task_run_dbt
```
This means: run taxi ingestion first, then weather ingestion, then dbt. Airflow will not start dbt until both ingestion tasks succeed.

#### Concept 4: The Execution Date / Logical Date

Airflow passes an `execution_date` (or `logical_date` in newer versions) to each DAG run. This is the date the DAG *logically* represents — not necessarily today. This is critical for **backfilling** (re-running past dates). Your ingestion scripts must accept this date as a parameter so they process the correct month's data.

#### Concept 5: XComs (Cross-Task Communication)

Sometimes Task B needs information produced by Task A (e.g., "how many rows were loaded?"). Airflow provides XComs — a key-value store that tasks can push to and pull from. For this project, your ingestion task can push the row count to XCom, and a validation task can pull it and verify it's above zero.

#### Concept 6: Connections and Variables

Airflow has a secrets store for connections (database credentials) and variables (configuration values). You should never hardcode Snowflake credentials in your DAG file. Instead, configure a Snowflake connection in Airflow's UI and reference it by connection ID.

---

### 5.5 Snowflake — What You Must Know For This Project

#### Concept 1: Snowflake Object Hierarchy

```
Account
  └── Database (URBANFLOW)
        ├── Schema (BRONZE)
        │     ├── Table (RAW_TAXI_TRIPS)
        │     └── Table (RAW_WEATHER)
        ├── Schema (SILVER)
        │     ├── Table (TAXI_TRIPS_CLEAN)
        │     └── Table (WEATHER_HOURLY)
        └── Schema (GOLD)
              ├── Table (FACT_TRIPS)
              └── Table (AGG_DEMAND_BY_WEATHER)
```

#### Concept 2: Virtual Warehouses (Compute)

In Snowflake, compute is separated from storage. A **virtual warehouse** is a cluster of compute nodes. You choose the size (XS, S, M, L, etc.). For development, always use `X-SMALL`. This controls cost. You must understand how to suspend a warehouse when not in use (to avoid burning credits).

#### Concept 3: Stages and COPY INTO

For bulk loading data into Snowflake, the most efficient method is:
1. Upload file to a Snowflake **internal stage** (a temporary storage area)
2. Use `COPY INTO table FROM @stage` to load it in bulk

This is far faster than inserting row by row via the Python connector. The `snowflake-connector-python` library's `write_pandas()` function handles this for you under the hood — but you need to know what it's doing.

#### Concept 4: Time Travel

Snowflake keeps historical versions of your tables for up to 90 days (configurable). You can query data as it existed at a past point in time using `AT (TIMESTAMP => ...)`. This is useful for debugging — if a bad pipeline run overwrites data, you can recover it.

#### Concept 5: Zero-Copy Cloning

You can clone an entire database, schema, or table instantly without duplicating storage. This is how teams create development environments. You clone production Snowflake schemas for your dev environment.

#### Concept 6: Snowflake Roles and Permissions

You will create:
- A role for ingestion (can write to Bronze)
- A role for dbt transformations (can read Bronze, write Silver and Gold)
- A role for analysts (can only read Gold)

This is called **least privilege** — each component only has the permissions it needs.

---

### 5.6 Docker — What You Must Know For This Project

#### Concept 1: What Docker Solves

"It works on my machine" is the classic developer problem. Docker packages your application and all its dependencies into a **container** — an isolated, reproducible unit that runs identically on any machine. You will run Airflow inside Docker so that anyone on your team (or a CI/CD system) can run the same Airflow environment.

#### Concept 2: Key Concepts

- **Image**: A blueprint/template (like a class in OOP). Read-only.
- **Container**: A running instance of an image (like an object). You can have many containers from one image.
- **Dockerfile**: A text file with instructions to build a custom image.
- **docker-compose.yml**: A YAML file that defines multiple containers and how they connect to each other.

#### Concept 3: Airflow on Docker

The official Airflow Docker setup uses `docker-compose.yml` to spin up multiple containers:
- `airflow-webserver` — the UI
- `airflow-scheduler` — monitors and triggers DAGs
- `airflow-worker` — executes tasks (if using Celery executor)
- `postgres` — Airflow's metadata database
- `redis` — message broker between scheduler and workers

You will use the official `docker-compose.yaml` from the Airflow documentation (Apache provides it).

#### Concept 4: Volumes

Containers are ephemeral — they lose all data when stopped. **Volumes** persist data outside the container. For Airflow:
- `./dags` folder (your machine) maps to `/opt/airflow/dags` (in the container) — so your DAG files are available inside the container
- Same for `./logs` and `./plugins`

#### Concept 5: Environment Variables in Docker

Your `.env` file contains secrets. The `docker-compose.yml` references these using `${VARIABLE_NAME}` syntax. The secrets never go into the image itself. This is proper secret management in containerized environments.

---

## 6. Real World Raw Data Sources

### Source 1: NYC TLC Yellow Taxi Trip Records
**Download URL:** https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

**What to download:**
- Yellow Taxi Trip Records for **January 2023 and February 2023** (two months — large enough to be real, small enough to be manageable)
- Files are in **Parquet format** (not CSV — this is a bonus learning: you'll need `pyarrow` or `fastparquet` to read them)
- Each file is approximately 40–50 MB, contains ~3 million rows

**Direct Parquet file links (stable S3 links):**
```
January 2023:
https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet

February 2023:
https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-02.parquet
```

**Zone Lookup Table:**
```
https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv
```

**Column Reference:**
The data dictionary is here: https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf

Key columns you'll use:
- `tpep_pickup_datetime` — trip start time
- `tpep_dropoff_datetime` — trip end time
- `PULocationID` — pickup location ID (join to zone lookup)
- `DOLocationID` — dropoff location ID
- `passenger_count` — number of passengers
- `trip_distance` — miles
- `fare_amount` — base fare in USD
- `tip_amount` — tip in USD
- `total_amount` — total charged
- `payment_type` — 1=Credit card, 2=Cash, 3=No charge, 4=Dispute, 5=Unknown, 6=Voided

### Source 2: Open-Meteo Historical Weather API
**Documentation:** https://open-meteo.com/en/docs/historical-weather-api

This is a **free API** that requires no API key. You will make HTTP requests to it programmatically.

**API Endpoint:**
```
https://archive-api.open-meteo.com/v1/archive
```

**Parameters you'll use:**
```
latitude=40.7128        (New York City)
longitude=-74.0060
start_date=2023-01-01
end_date=2023-02-28
hourly=temperature_2m,precipitation,snowfall,windspeed_10m,weathercode
timezone=America/New_York
```

**Full example URL to test in browser:**
```
https://archive-api.open-meteo.com/v1/archive?latitude=40.7128&longitude=-74.0060&start_date=2023-01-01&end_date=2023-02-28&hourly=temperature_2m,precipitation,snowfall,windspeed_10m,weathercode&timezone=America/New_York
```

**What comes back:** A JSON object with an `hourly` key containing arrays — one value per hour for the date range. You'll need to parse this into a tabular format (one row per hour).

**Weather Code Reference (WMO standard):**
- 0: Clear sky
- 1-3: Mainly clear / partly cloudy / overcast
- 45, 48: Fog
- 51-57: Drizzle
- 61-67: Rain
- 71-77: Snow
- 80-82: Rain showers
- 85-86: Snow showers
- 95: Thunderstorm

---

## 7. Project Structure & Directory Layout

This is the exact folder structure you will build. Every folder has a purpose. Don't deviate from it.

```
urbanflow-analytics/
│
├── .env                          # ← NEVER commit this to git. Holds secrets.
├── .gitignore                    # ← Must include .env, __pycache__, etc.
├── README.md                     # ← Project overview and how to run it
├── requirements.txt              # ← All Python dependencies
│
├── docker/
│   ├── docker-compose.yml        # ← Spins up Airflow + Postgres + Redis
│   └── Dockerfile                # ← Custom Airflow image with your dependencies
│
├── ingestion/
│   ├── __init__.py
│   ├── ingest_taxi.py            # ← Downloads parquet, loads to Snowflake Bronze
│   ├── ingest_weather.py         # ← Calls Open-Meteo API, loads to Snowflake Bronze
│   ├── ingest_zone_lookup.py     # ← Loads static CSV to Snowflake Bronze
│   └── snowflake_utils.py        # ← Shared Snowflake connection helper
│
├── dags/
│   ├── dag_daily_pipeline.py     # ← Main Airflow DAG definition
│   └── dag_backfill.py           # ← (Optional) DAG for re-running past months
│
├── dbt/
│   ├── dbt_project.yml           # ← dbt project config
│   ├── profiles.yml              # ← Snowflake connection for dbt (DO NOT COMMIT)
│   ├── packages.yml              # ← dbt packages (e.g., dbt-utils)
│   │
│   ├── models/
│   │   ├── sources.yml           # ← Declares Bronze tables as sources
│   │   │
│   │   ├── silver/
│   │   │   ├── silver_taxi_trips.sql       # ← Cleaned trips
│   │   │   ├── silver_weather_hourly.sql   # ← Cleaned weather
│   │   │   ├── silver_zone_lookup.sql      # ← Cleaned zone lookup
│   │   │   └── schema.yml                  # ← Column descriptions + tests
│   │   │
│   │   └── gold/
│   │       ├── gold_fact_trips.sql         # ← Enriched trip-level fact table
│   │       ├── gold_agg_demand_weather.sql # ← Aggregated analytics table
│   │       ├── gold_dim_zones.sql          # ← Zone dimension table
│   │       └── schema.yml                  # ← Column descriptions + tests
│   │
│   ├── tests/
│   │   ├── assert_no_negative_fares.sql
│   │   ├── assert_trip_duration_valid.sql
│   │   ├── assert_weather_join_coverage.sql
│   │   └── assert_gold_row_count_matches_silver.sql
│   │
│   ├── seeds/
│   │   └── (empty — you load zone lookup via Python, not dbt seed)
│   │
│   └── macros/
│       └── classify_weather.sql  # ← Jinja macro to classify WMO code to category
│
├── tests/
│   └── test_ingestion.py         # ← Unit tests for your Python scripts
│
└── docs/
    └── architecture.png          # ← Screenshot of your dbt lineage graph
```

---

## 8. Phase-by-Phase Implementation Guide

### Phase 0: Environment Setup (Day 1)

**Goal:** Get all tools installed and connected before writing any pipeline code.

**Steps:**
1. Sign up for a free Snowflake trial account (30 days, $400 credits — more than enough)
2. In Snowflake, manually create: Database `URBANFLOW`, Schemas `BRONZE`, `SILVER`, `GOLD`
3. Create a dedicated Snowflake user and role for this project (do not use ACCOUNTADMIN for everything)
4. Install Python 3.10+, create a virtual environment
5. Install: `snowflake-connector-python[pandas]`, `pandas`, `pyarrow`, `requests`, `python-dotenv`, `dbt-snowflake`, `apache-airflow`
6. Create your `.env` file with Snowflake credentials
7. Run `dbt init urbanflow` inside your `dbt/` folder and configure `profiles.yml` to point to Snowflake
8. Run `dbt debug` — if it says "All checks passed," your dbt → Snowflake connection works
9. Run `dbt deps` to install any required packages (like dbt-utils) specified in `packages.yml`

**Validation checkpoint:** `dbt debug` returns "All checks passed." You can run a `SELECT CURRENT_USER()` from Python against Snowflake.

---

### Phase 1: Bronze Layer — Data Ingestion (Days 2–4)

**Goal:** Load raw taxi data and weather data into Snowflake Bronze schema, as-is.

**Task 1.1 — Download and Load Taxi Parquet Files**

Write `ingestion/ingest_taxi.py`. This script must:
- Accept a year and month as command-line arguments (so you can run it for any month)
- Download the parquet file from the TLC S3 URL (or use a pre-downloaded file)
- Read it in chunks (use `pandas` with `chunksize` or read the parquet in row groups using `pyarrow`)
- Add two extra columns to every row: `source_file` (the filename) and `loaded_at` (current timestamp) — this is called **audit columns** and is standard practice
- Load each chunk to `BRONZE.RAW_TAXI_TRIPS` in Snowflake using `write_pandas()`
- Log progress: rows loaded, time taken, any errors

**Critical design decision:** Your Bronze table uses `loaded_at` as a partition/filter key. Future incremental Silver runs will filter Bronze rows WHERE `loaded_at > last_silver_run_timestamp`. This is how incremental pipelines know what's new.

**Task 1.2 — Fetch and Load Weather Data**

Write `ingestion/ingest_weather.py`. This script must:
- Accept start_date and end_date as parameters
- Call the Open-Meteo API
- Parse the JSON response — the `hourly` object has keys like `time`, `temperature_2m`, `precipitation`, etc., all as arrays. You need to zip these arrays into rows (each row = one hour)
- Add `source` and `loaded_at` audit columns
- Load to `BRONZE.RAW_WEATHER_HOURLY` in Snowflake

**Task 1.3 — Load Zone Lookup**

Write `ingestion/ingest_zone_lookup.py` to download the zone lookup CSV and load it to `BRONZE.RAW_ZONE_LOOKUP`. This is a tiny file (~265 rows), so you can load it in one shot — no chunking needed. *(Note: This is a static table, so you only need to run this script once manually. It does not need to be in your daily Airflow DAG).*

**What Bronze tables look like:**

`BRONZE.RAW_TAXI_TRIPS`
- All original columns from the parquet file
- Plus: `source_file VARCHAR`, `loaded_at TIMESTAMP_NTZ`
- No cleaning — nulls preserved, bad values preserved

`BRONZE.RAW_WEATHER_HOURLY`
- Columns: `time TIMESTAMP_NTZ`, `temperature_2m FLOAT`, `precipitation FLOAT`, `snowfall FLOAT`, `windspeed_10m FLOAT`, `weathercode INTEGER`, `loaded_at TIMESTAMP_NTZ`

`BRONZE.RAW_ZONE_LOOKUP`
- Columns: `locationid INTEGER`, `borough VARCHAR`, `zone VARCHAR`, `service_zone VARCHAR`

**Validation checkpoint:**
- Query `SELECT COUNT(*) FROM BRONZE.RAW_TAXI_TRIPS` — January 2023 should have ~3 million rows
- Query `SELECT MIN(tpep_pickup_datetime), MAX(tpep_pickup_datetime) FROM BRONZE.RAW_TAXI_TRIPS` — should span January
- Query `SELECT COUNT(*) FROM BRONZE.RAW_WEATHER_HOURLY` — Jan+Feb = 59 days × 24 hours = 1,416 rows

---

### Phase 2: Silver Layer — Cleaning and Validation (Days 5–7)

**Goal:** Create clean, reliable, analysis-ready row-level data using dbt SQL models.

This is where dbt takes over. You write SQL models that read from Bronze and write to Silver.

**Task 2.1 — Declare Sources**

In `dbt/models/sources.yml`, declare all three Bronze tables as dbt sources. This tells dbt where the raw data lives and enables the `{{ source() }}` reference in your models.

**Task 2.2 — Build `silver_taxi_trips.sql`**

This model must apply these cleaning rules (implement as CTEs):

**CTE 1 — `source`**: Select all columns from `{{ source('bronze', 'raw_taxi_trips') }}`

**CTE 2 — `cast_types`**: Ensure all columns have correct data types. Cast pickup/dropoff to `TIMESTAMP_NTZ`. Cast numeric columns to `FLOAT` or `INTEGER` as appropriate.

**CTE 3 — `remove_duplicates`**: Use `ROW_NUMBER() OVER (PARTITION BY all_columns ORDER BY loaded_at)` to identify and keep only the first occurrence of exact duplicates.

**CTE 4 — `apply_business_rules`**: Filter out rows where ANY of the following are true:
- `fare_amount <= 0` (invalid)
- `trip_distance <= 0` (ghost trips)
- `passenger_count <= 0 OR passenger_count > 8` (impossible)
- `tpep_pickup_datetime >= tpep_dropoff_datetime` (time goes backwards)
- `DATEDIFF('minute', tpep_pickup_datetime, tpep_dropoff_datetime) > 180` (trips over 3 hours — likely data error)
- `tpep_pickup_datetime < '2023-01-01'` (data from wrong period)
- `tpep_pickup_datetime >= '2023-03-01'` (future data leaked in)
*(Pro-tip: Hardcoding 2023 dates here is fine for a V1 MVP, but a truly production-grade model would use Jinja variables `{{ var('start_date') }}` passed from Airflow to make this dynamic for any month).*

**CTE 5 — `add_derived_columns`**: Add calculated columns:
- `trip_id` = generate a unique surrogate key (e.g., using `MD5()` on a concatenation of key columns, or `dbt_utils.generate_surrogate_key`)
- `trip_duration_minutes` = `DATEDIFF('minute', pickup, dropoff)`
- `pickup_hour` = `EXTRACT(HOUR FROM pickup)`
- `pickup_day_of_week` = `DAYOFWEEK(pickup)` (0=Sunday, 6=Saturday)
- `pickup_date` = `DATE(pickup)`
- `pickup_hour_truncated` = `DATE_TRUNC('hour', pickup)` (for joining to weather)
- `speed_mph` = `trip_distance / (trip_duration_minutes / 60.0)` — add a filter to remove speeds > 100 mph (data errors)

**CTE 6 — `final`**: Select only the columns you need (no more star selects in Silver+).

**Incremental config:** This model should be `incremental`. On full refresh, process all Bronze data. On incremental runs, only process rows where `loaded_at > (SELECT MAX(loaded_at) FROM {{ this }})`.

**Task 2.3 — Build `silver_weather_hourly.sql`**

Cleaning rules:
- Remove any rows with null timestamps
- Add `weather_category` column: use a CASE statement to map WMO codes to human-readable categories:
  - 0–3: 'Clear'
  - 45–48: 'Fog'
  - 51–67: 'Rain'
  - 71–77: 'Snow'
  - 80–86: 'Showers'
  - 95+: 'Thunderstorm'
  - else: 'Unknown'
- Add `is_precipitation` boolean: 1 if `precipitation > 0` OR `snowfall > 0`, else 0
- Deduplicate on `time` column (keep latest loaded_at)

**Task 2.4 — Write Schema YAML with dbt Tests**

In `dbt/models/silver/schema.yml`, define tests for every Silver model:

For `silver_taxi_trips`:
- `trip_id` (you'll generate a surrogate key): `not_null`, `unique`
- `fare_amount`: `not_null`
- `pulocationid`: `not_null`, `relationships` (must exist in silver_zone_lookup)
- `trip_duration_minutes`: `not_null`

For `silver_weather_hourly`:
- `time`: `not_null`, `unique`
- `weather_category`: `accepted_values: ['Clear', 'Fog', 'Rain', 'Snow', 'Showers', 'Thunderstorm', 'Unknown']`

**Validation checkpoint:**
- `dbt run --models silver` — runs without errors
- `dbt test --models silver` — all tests pass
- `SELECT COUNT(*) FROM SILVER.TAXI_TRIPS_CLEAN` — should be ~2.8-3M (some filtered out from 3M raw)
- `SELECT weather_category, COUNT(*) FROM SILVER.WEATHER_HOURLY GROUP BY 1` — verify distribution looks realistic for NYC in January/February

---

### Phase 3: Gold Layer — Analytics Modeling (Days 8–10)

**Goal:** Create aggregated, joined, analytics-ready tables that answer the business questions.

**Task 3.1 — Build `gold_dim_zones.sql`**

A dimension table for geographic zones. Select from `{{ ref('silver_zone_lookup') }}`. Add a surrogate key. This is a small reference table that other Gold models will join to.

**Task 3.2 — Build `gold_fact_trips.sql`**

This is your fact table — one row per trip, enriched with weather context and zone names.

Key joins to perform:
- Join `silver_taxi_trips` to `silver_weather_hourly` ON `silver_taxi_trips.pickup_hour_truncated = silver_weather_hourly.time` (LEFT JOIN — keep all trips even if weather data is missing)
- Join to `silver_zone_lookup` on `pulocationid` to get borough and zone name for pickup

Columns to include: all cleaned trip columns + `temperature_2m`, `precipitation`, `snowfall`, `weather_category`, `is_precipitation`, `pickup_borough`, `pickup_zone`

**Important:** After this join, validate that your row count matches `silver_taxi_trips`. If it's higher, you have a fan-out problem (duplicated rows from a bad join). This is the most common Gold layer bug.

**Task 3.3 — Build `gold_agg_demand_weather.sql`**

This is the final analytics table that directly answers the business questions. Aggregate from `gold_fact_trips`.

Build aggregations at the grain of: `pickup_date` + `pickup_hour` + `pickup_borough` + `weather_category`

Include these metrics:
- `total_trips` = COUNT(*)
- `avg_fare` = AVG(fare_amount)
- `avg_duration_minutes` = AVG(trip_duration_minutes)
- `avg_trip_distance` = AVG(trip_distance)
- `total_passengers` = SUM(passenger_count)
- `pct_cash_payment` = SUM(CASE WHEN payment_type = 2 THEN 1 ELSE 0 END) / COUNT(*) * 100
- `avg_precipitation` = AVG(precipitation)
- `avg_temperature` = AVG(temperature_2m)

**This table is the answer to the business questions.** An analyst can query it directly to see: "On rainy mornings in Manhattan, how many trips were there vs. clear mornings?"

**Task 3.4 — Write a Custom dbt Macro**

In `dbt/macros/classify_weather.sql`, write a Jinja macro called `classify_weather(weathercode_col)` that takes a column name and returns the CASE statement for weather classification. Then use `{{ classify_weather('weathercode') }}` in your silver_weather model instead of the inline CASE statement. This demonstrates how macros reduce code duplication.

**Validation checkpoint:**
- `dbt run --models gold` — runs without errors
- `dbt test --models gold` — all tests pass
- Query `gold_agg_demand_weather`: On days with weather_category = 'Snow', total_trips should be LOWER than on 'Clear' days (NYC taxis get fewer rides in blizzards — people stay home or use the subway)
- Row count of `gold_fact_trips` must exactly equal row count of `silver_taxi_trips`

---

### Phase 4: Orchestration with Airflow (Days 11–13)

**Goal:** Automate the entire pipeline using Airflow running in Docker.

**Task 4.1 — Set Up Airflow with Docker**

Download the official Airflow `docker-compose.yaml`:
```
https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html
```

Customize it:
- Add your Snowflake environment variables to the `environment` section (pulled from your `.env`)
- Mount your `ingestion/` folder and `dbt/` folder as volumes so Airflow containers can access them
- Add dbt and snowflake-connector-python to the custom Dockerfile so they're available inside containers

Run `docker-compose up airflow-init` first (one-time setup), then `docker-compose up -d`.

Access the Airflow UI at `http://localhost:8080`.

**Task 4.2 — Write the Main DAG**

File: `dags/dag_daily_pipeline.py`

This DAG should:
- Run on a monthly schedule (use a cron expression: `0 6 1 * *` = 6 AM on the 1st of every month)
- Accept `year` and `month` as Airflow Variables (configurable from the UI)
- Have these tasks in order:

```
Task 1: ingest_taxi_data
   - PythonOperator
   - Calls ingest_taxi.py with year/month parameters
   - On failure: retry 3 times with 5 minute delay

Task 2: ingest_weather_data
   - PythonOperator
   - Calls ingest_weather.py with date range parameters
   - Runs in PARALLEL with Task 1 (both can run at the same time)

Task 3: validate_bronze_counts
   - PythonOperator
   - Queries Snowflake to check row counts are above minimum thresholds
   - Fails the DAG if counts are zero (means ingestion silently failed)
   - Depends on Tasks 1 AND 2

Task 4: run_dbt_silver
   - BashOperator
   - Command: `dbt run --models silver --profiles-dir /path/to/profiles`
   - Depends on Task 3

Task 5: test_dbt_silver
   - BashOperator
   - Command: `dbt test --models silver`
   - Depends on Task 4

Task 6: run_dbt_gold
   - BashOperator
   - Command: `dbt run --models gold`
   - Depends on Task 5

Task 7: test_dbt_gold
   - BashOperator
   - Command: `dbt test --models gold`
   - Depends on Task 6
```

**Task 4.3 — Configure Airflow Connection**

In the Airflow UI, create a Snowflake connection with your credentials. Reference it by connection ID in your DAG rather than reading from environment variables directly.

**Validation checkpoint:**
- Trigger the DAG manually from the Airflow UI
- All 7 tasks turn green
- The Airflow logs for each task show the expected output (row counts, dbt model run summaries)
- If you deliberately break the Bronze ingestion (e.g., pass a bad date), Task 3 should fail and Tasks 4–7 should not run

---

### Phase 5: Singular Tests and Data Quality (Day 14)

**Goal:** Write custom SQL tests that go beyond what generic dbt tests can check.

Write these SQL files in `dbt/tests/`:

**Test 1: `assert_no_negative_fares.sql`**
Write a SQL query against `silver_taxi_trips` that returns rows where `fare_amount < 0`. Expected result: 0 rows.

**Test 2: `assert_trip_duration_valid.sql`**
Write a SQL query that returns trips where `trip_duration_minutes` is 0, negative, or greater than 300. Expected result: 0 rows.

**Test 3: `assert_weather_join_coverage.sql`**
Write a SQL query that counts trips in `gold_fact_trips` where `weather_category IS NULL`. You expect this to be very low (some edge cases at midnight boundaries). Assert it's below 1% of total trips.

**Test 4: `assert_gold_row_count_matches_silver.sql`**
Write a SQL query that compares COUNT(*) of `gold_fact_trips` vs `silver_taxi_trips`. They must be equal. If not, your join created duplicates.

Run all tests with `dbt test` and verify all pass.

---

## 9. Validation & Verification Guidelines

This section is your **acceptance criteria**. Use this as a checklist before considering the project complete.

### 9.1 Bronze Layer Validation

| Check | Query | Expected Result |
|-------|-------|-----------------|
| Row count — taxi Jan 2023 | `SELECT COUNT(*) FROM BRONZE.RAW_TAXI_TRIPS WHERE source_file LIKE '%2023-01%'` | ~3,066,766 rows |
| Row count — taxi Feb 2023 | `SELECT COUNT(*) FROM BRONZE.RAW_TAXI_TRIPS WHERE source_file LIKE '%2023-02%'` | ~2,913,955 rows |
| No data loss on load | Compare Python-logged row count vs Snowflake COUNT | Must match exactly |
| Date range correct | `SELECT MIN(tpep_pickup_datetime), MAX(tpep_pickup_datetime) FROM BRONZE.RAW_TAXI_TRIPS` | Jan 1 to Feb 28 |
| Weather rows | `SELECT COUNT(*) FROM BRONZE.RAW_WEATHER_HOURLY` | 1,416 (59 days × 24 hours) |
| Audit columns present | Check `source_file` and `loaded_at` are not null | 0 nulls |

### 9.2 Silver Layer Validation

| Check | Query | Expected Result |
|-------|-------|-----------------|
| No negative fares | `SELECT COUNT(*) FROM SILVER.TAXI_TRIPS_CLEAN WHERE fare_amount <= 0` | 0 |
| No zero distances | `SELECT COUNT(*) FROM SILVER.TAXI_TRIPS_CLEAN WHERE trip_distance <= 0` | 0 |
| No impossible durations | `SELECT COUNT(*) FROM SILVER.TAXI_TRIPS_CLEAN WHERE trip_duration_minutes <= 0 OR trip_duration_minutes > 180` | 0 |
| Filter rate reasonable | Silver count / Bronze count | Should be 90–98% (small fraction filtered out) |
| Weather categories | `SELECT DISTINCT weather_category FROM SILVER.WEATHER_HOURLY` | Only values from accepted list |
| Weather deduplication | `SELECT COUNT(*) vs COUNT(DISTINCT time) FROM SILVER.WEATHER_HOURLY` | Must be equal |
| Zone lookup completeness | `SELECT COUNT(*) FROM SILVER.ZONE_LOOKUP` | 265 rows |
| dbt tests | `dbt test --models silver` | All tests pass, 0 failures |

### 9.3 Gold Layer Validation

| Check | Query | Expected Result |
|-------|-------|-----------------|
| Fact table row count | `SELECT COUNT(*) FROM GOLD.FACT_TRIPS` vs Silver | Must be identical |
| No duplicated trips | `SELECT trip_id, COUNT(*) FROM GOLD.FACT_TRIPS GROUP BY 1 HAVING COUNT(*) > 1` | 0 rows |
| Weather join rate | `SELECT COUNT(*) FROM GOLD.FACT_TRIPS WHERE weather_category IS NULL` | < 1% of total |
| Business logic check | Trips on Clear days vs Snow days | Clear days should have significantly more trips |
| Borough coverage | `SELECT DISTINCT pickup_borough FROM GOLD.FACT_TRIPS` | Should include Manhattan, Brooklyn, Queens, Bronx, Staten Island, EWR |
| Aggregation check | SUM(total_trips) from gold_agg_demand_weather vs COUNT from gold_fact_trips | Must match |
| dbt tests | `dbt test --models gold` | All tests pass, 0 failures |

### 9.4 Pipeline Validation

| Check | Expected Behavior |
|-------|------------------|
| DAG visible in Airflow UI | Yes, within 30 seconds of file creation |
| All 7 tasks complete green | Yes, on a fresh triggered run |
| Task 3 fails when Bronze is empty | Yes — force this by disabling Tasks 1 & 2 and verifying Task 3 catches it |
| dbt logs visible in Airflow task logs | Yes — dbt output captured by BashOperator |
| Backfill works | Manually trigger DAG with different year/month variables, pipeline runs for that month |

### 9.5 Data Quality Sanity Checks (Business Logic)

These are checks to verify your data makes sense in the real world:

```sql
-- Check 1: More trips in Manhattan than Staten Island (always true for NYC)
SELECT pickup_borough, COUNT(*) as trips
FROM GOLD.FACT_TRIPS
GROUP BY 1
ORDER BY 2 DESC;
-- Expected: Manhattan >> Brooklyn > Queens > Bronx > Staten Island

-- Check 2: Rush hour (8-9 AM and 5-7 PM) should have highest trip counts
SELECT pickup_hour, COUNT(*) as trips
FROM GOLD.FACT_TRIPS
GROUP BY 1
ORDER BY 1;
-- Expected: peaks at hours 8, 17, 18

-- Check 3: Rainy days should show higher average fares (longer wait times, surge)
SELECT weather_category, AVG(fare_amount) as avg_fare, COUNT(*) as trips
FROM GOLD.FACT_TRIPS
GROUP BY 1
ORDER BY 2 DESC;
-- Expected: Rain/Snow categories show higher avg_fare than Clear

-- Check 4: Credit card payments should dominate (65-70% of trips in NYC)
SELECT payment_type, COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as pct
FROM GOLD.FACT_TRIPS
GROUP BY 1;
-- Expected: payment_type 1 (credit card) ~65-70%
```

---

## 10. Deliverables Checklist

Before you consider this project complete, every item below must be true:

### Code Deliverables
- [ ] `ingestion/ingest_taxi.py` — accepts year/month params, loads to Bronze with audit columns, uses chunked loading, logs progress
- [ ] `ingestion/ingest_weather.py` — calls Open-Meteo API, parses JSON, loads to Bronze
- [ ] `ingestion/ingest_zone_lookup.py` — loads the static CSV lookup table
- [ ] `ingestion/snowflake_utils.py` — shared connection helper with env variable loading
- [ ] `dags/dag_daily_pipeline.py` — 7-task DAG with proper dependencies, retry logic, and parameterization
- [ ] `dbt/models/sources.yml` — all Bronze tables declared as sources
- [ ] `dbt/models/silver/silver_taxi_trips.sql` — incremental model with all 6 CTEs
- [ ] `dbt/models/silver/silver_weather_hourly.sql` — with weather_category macro
- [ ] `dbt/models/silver/silver_zone_lookup.sql`
- [ ] `dbt/models/silver/schema.yml` — all generic tests defined
- [ ] `dbt/models/gold/gold_fact_trips.sql` — enriched fact table
- [ ] `dbt/models/gold/gold_agg_demand_weather.sql` — analytics aggregate
- [ ] `dbt/models/gold/gold_dim_zones.sql` — zone dimension
- [ ] `dbt/models/gold/schema.yml` — all generic tests defined
- [ ] `dbt/tests/` — all 4 singular test SQL files
- [ ] `dbt/macros/classify_weather.sql` — reusable Jinja macro
- [ ] `docker/docker-compose.yml` — Airflow stack with volume mounts
- [ ] `docker/Dockerfile` — custom Airflow image with dbt + snowflake deps

### Quality Deliverables
- [ ] All Bronze validation queries return expected row counts
- [ ] All Silver dbt tests pass (0 failures)
- [ ] All Gold dbt tests pass (0 failures)
- [ ] All 4 singular tests pass (0 rows returned)
- [ ] All business logic sanity checks return reasonable results
- [ ] Airflow DAG completes end-to-end with all green tasks

### Documentation Deliverables
- [ ] `README.md` — how to set up the environment, configure credentials, run the pipeline
- [ ] `dbt docs generate && dbt docs serve` — lineage graph shows all model dependencies
- [ ] All dbt models have descriptions in schema YAML files
- [ ] All columns in Gold models have descriptions

---

## Final Notes From Your Interviewer

You are building what data engineers actually build in production. Not a simulation. The NYC taxi dataset is real data that Uber, Lyft, and academic researchers use. The Open-Meteo API is a real production API. Snowflake is what 80% of companies use as their cloud warehouse today.

When you are done, you will have built:
- A **real ELT pipeline** (Extract → Load → Transform, the modern standard)
- A **medallion architecture** used by Databricks, Airflow's own data team, and companies like Airbnb
- A **tested, documented, orchestrated pipeline** that won't collapse when data is bad
- A project you can **explain confidently in an interview** because you built every part of it

The most important lesson: **data engineering is not about writing fancy code. It is about making data trustworthy, reproducible, and usable.** Every decision in this project — the audit columns, the incremental loads, the dbt tests, the Airflow retry logic — exists for that single purpose.

Good luck. Debug patiently. Read the logs.

---

*Assignment created for mid-level data engineering candidate evaluation. Expected completion: 2–3 weeks for a first-time end-to-end project.*
