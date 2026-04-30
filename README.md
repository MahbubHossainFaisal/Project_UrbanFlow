# UrbanFlow Analytics: NYC Taxi & Weather Platform

## 🏙️ Project Overview
This project is an end-to-end data engineering pipeline built for **UrbanFlow Analytics**. The goal is to help the **NYC Taxi & Limousine Commission (TLC)** understand how weather conditions (rain, snow, temperature) affect taxi demand patterns across New York City boroughs.

By combining millions of taxi trip records with historical weather data, we aim to answer key business questions:
- How does demand spike in specific boroughs during bad weather?
- What are the highest weather-correlated demand shifts?
- How do fares and trip durations change under different weather conditions?

## 🏗️ Architecture (Medallion)
The project follows the industry-standard **Medallion Architecture**, ensuring data quality and reproducibility at every step:

1.  **Bronze (Raw)**: Ingesting raw data from source systems (S3, Open-Meteo API) as-is.
2.  **Silver (Cleaned)**: Cleaning, validating, and standardizing data using **dbt**.
3.  **Gold (Curated)**: Creating analytics-ready facts and dimensions for business reporting.

## 🛠️ Tech Stack
- **Orchestration**: Apache Airflow (Dockerized)
- **Data Warehouse**: Snowflake
- **Transformation**: dbt Core
- **Ingestion**: Python (Pandas, Requests, Snowflake-Connector)
- **Environment**: Docker, Python 3.12, `uv`

---

## 🚀 Project Progress

### Phase 1: Bronze Layer (Ingestion) - 🔄 In Progress (~90%)
- [x] **NYC Taxi Data**: Ingested Jan/Feb 2023 Parquet files (~5.9M rows).
- [🟡] **Weather Data**: API connection verified. Ingestion script (`ingest_weather.py`) in development.
- [ ] **Zone Lookup**: Pending ingestion of static CSV.

### Phase 2: Silver Layer (Transformation) - ❌ Not Started
- [ ] dbt Source Declarations
- [ ] Data Cleaning & Deduplication
- [ ] Schema Validation & dbt Tests

### Phase 3: Gold Layer (Analytics) - ❌ Not Started
- [ ] Weather & Taxi Join logic
- [ ] Aggregated Demand Analytics
- [ ] Data Lineage & Documentation

---

## ⚙️ Project Setup & Commands Used

Below is a list of the unique commands that have been used to initialize and set up this project.

### 1. Python Environment Setup (using `uv`)

We use [`uv`](https://github.com/astral-sh/uv) to manage our Python virtual environment and dependencies because of its speed.

*   `uv venv --python 3.12` - Creates an isolated Python virtual environment.
*   `.venv\Scripts\activate` - Activates the virtual environment.
*   `uv add requirements.txt` - Installs project dependencies.

### 2. dbt (Data Build Tool) Initialization

*   `dbt init urbanflow` - Initializes the dbt project structure.

### 3. Custom dbt Wrapper (Environment Variable Management)

We use a custom PowerShell script (`run_dbt.ps1`) to inject `.env` variables before running dbt.

*   `dbt debug` - Verifies the Snowflake connection (via the wrapper).
