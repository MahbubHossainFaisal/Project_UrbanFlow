# UrbanFlow Analytics: Full-Stack Urban Intelligence Platform

## 🏙️ Project Overview
UrbanFlow Analytics is an end-to-end, production-grade data intelligence platform built for the **NYC Taxi & Limousine Commission (TLC)**. Moving beyond simple orchestration, this platform is a **Full-Stack Data Factory** designed to provide deep insights into urban mobility, financial integrity, and environmental sustainability.

By unifying millions of taxi trip records with high-resolution weather data and business reference mappings, we answer critical questions:
- **Demand Intelligence**: How do extreme weather events shift pickup density and rider behavior?
- **Financial Integrity**: Auditing fare patterns and airport flat rates for revenue protection.
- **Sustainability Mandate**: Calculating the carbon footprint of the NYC fleet and its correlation with traffic patterns.

## 🏗️ Architecture & Workflow
The platform follows an "Elite" implementation of the **Medallion Architecture**, hardened with audit metadata and production-grade guardrails.

### 🗺️ Full-Stack System Workflow
```mermaid
graph TD
    subgraph "1. DATA INGESTION (Python + Airflow)"
        A[External Sources] -->|S3 Parquet| B(ingest_taxi.py)
        A -->|API JSON| C(ingest_weather.py)
        A -->|Static CSV| D(ingest_zone_lookup.py)
        A -->|dbt Seeds| DS[Reference Mappings]
    end

    subgraph "2. BRONZE LAYER (Raw Data)"
        B -->|Bulk Load| E[(RAW_TAXI_TRIPS)]
        C -->|Bulk Load| F[(RAW_WEATHER_HOURLY)]
        D -->|Bulk Load| G[(RAW_TAXI_ZONE_LOOKUP)]
    end

    subgraph "3. SILVER LAYER (Cleaned & Hardened)"
        E & F & G & DS --> S_H{Elite Refactor}
        S_H --> S1[stg_taxi_trips]
        S_H --> S2[stg_weather_hourly]
        S_H --> S3[stg_zone_lookup]
        S_H --> S4[ref_mappings]
    end

    subgraph "4. GOLD LAYER (7-Dimension Star Schema)"
        S1 & S2 & S3 & S4 --> G1[gold_fact_trips]
        G1 --> G2[gold_agg_demand_weather]
        G1 --> G3[gold_fact_sustainability]
    end

    subgraph "5. VISUAL INTELLIGENCE (Streamlit)"
        G2 & G3 --> STR[Streamlit Dashboard]
    end

    subgraph "6. ORCHESTRATION"
        Airflow((Apache Airflow))
        Airflow -.->|Dockerized Tasks| B & C & S_H & G1
    end

    style Airflow fill:#00d2ff,stroke:#333,stroke-width:2px
    style STR fill:#ff4b2b,stroke:#333,color:#fff
    style S_H fill:#f9d423,stroke:#333
```

## 🛠️ Tech Stack
- **Orchestration**: Apache Airflow (Dockerized)
- **Data Warehouse**: Snowflake
- **Transformation**: dbt Core (1.7+)
- **Visual Intelligence**: **Streamlit**
- **Ingestion**: Python (Pandas, Requests, Snowflake-Connector)
- **Environment**: Docker, Python 3.12, `uv`

---

## 🚀 Project Progress (The Elite Sprints)

### Sprint 1: Dimensional Foundation - ✅ 100% Complete (Hardened)
- [x] **Temporal Backbone**: Built `dim_calendar.sql` using Snowflake generator logic (Zero-IO).
- [x] **Relational Fact Pivot**: Refactored `gold_fact_trips` to link with Calendar and Zone dimensions.
- [x] **Reference Ingestion (Seeds)**: Implemented version-controlled mappings for Vendors, Payments, Rate Codes, and Emissions.

### Sprint 2: Silver Feature Engineering - ✅ 100% Complete
- [x] **Sustainability Engine**: Implemented CO2 calculations in `stg_taxi_trips` using vendor emission factors.
- [x] **Anomaly Detection**: Successfully flagged 81 outliers (Distance > 100mi, Fare > $500).
- [x] **Silver Quality Gates**: Hardened staging models with robust dbt tests.
- [x] **The Clean Aggregate**: Refactored `gold_agg_demand_weather` to exclude anomalies and include CO2 metrics.

### Sprint 3: The Multi-Fact Gold Layer - 🔄 In Progress
- [x] **Financial Integrity Fact**: Dedicated table for airport flat-rate auditing (Successfully identified JFK $70 signal).
- [ ] **Sustainability Fact**: Specialized grain for carbon emission analysis.
- [ ] **Multi-Fact Star Schema**: Finalizing the 7-Dimension, 3-Fact relationship model.

### Sprint 4: Hardened Orchestration & Visuals - 📅 Planned
- [ ] Dockerized Airflow DAGs with Short-Circuit Quality Gates.
- [ ] **Streamlit Executive Dashboard**: Interactive KPI reporting for TLC leadership.

---

## ⚙️ Project Setup & Commands Used

### 1. Python Environment Setup (using `uv`)
*   `uv venv --python 3.12`
*   `uv add requirements.txt`

### 2. dbt Elite Commands
*   `uv run dbt seed` - Loads the Reference Layer into Snowflake.
*   `uv run dbt run --select silver` - Materializes the Hardened Silver layer.
*   `uv run dbt run --select gold` - Finalizes the Analytics Star Schema.

### 📚 Learning Resources
Detailed architectural deep-dives are documented in the following repository:
*   [`Learnings/dbt/`](Learnings/dbt/) - dbt configuration intuition and design patterns.
*   [`Learnings/Snowflake/`](Learnings/Snowflake/) - RBAC and performance optimization patterns.
