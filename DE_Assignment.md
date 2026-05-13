# Data Engineering Assignment: End-to-End Real-World Pipeline
## "NYC Urban Mobility & Sustainability Datamart" (Elite Expansion)

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

You have just joined **UrbanFlow Analytics**, a mid-sized data consultancy that works with city transportation authorities. Their client, the **NYC Taxi & Limousine Commission (TLC)**, is evolving. They no longer just want to know "how many rides occurred." They are now focused on three critical pillars of urban management:

- **Demand Analytics**: How do weather conditions (rain, snow) affect pickup patterns?
- **Revenue Integrity**: Are drivers/vendors charging correct flat rates for airports? Are payment methods shifting?
- **Sustainability Mandate**: What is the carbon footprint of the NYC fleet, and how does it correlate with traffic and weather?

The client wants a **Multi-Fact Star Schema Datamart** and an **Interactive Executive Dashboard** to answer complex questions like: *"Which vendor had the highest CO2 emissions during Christmas week in Brooklyn using Credit Cards?"*

---

## 2. The Problem Statement

### What you are dealing with:

**Source 1 — NYC Taxi Trip Records (Structured, large Parquet files)**
- Contains millions of rows per month.
- Includes timestamps, locations, fares, payment types, and rate codes.
- **Complexity**: You must audit these for "Price Integrity" (e.g., JFK airport trips should have a flat rate).

**Source 2 — Open-Meteo Historical Weather API (Semi-structured JSON)**
- Hourly historical weather data.
- Essential for correlating demand with environmental factors.

**Source 3 — NYC TLC Zone Lookup Table (Small CSV)**
- Maps `LocationID` to Borough and Zone name.

**Source 4 — Reference Mappings (Static Seeds)**
- **Rate Codes**: Mapping IDs (1-6) to business types (Standard, JFK, Newark, etc.).
- **Payment Types**: Mapping IDs (1-6) to (Credit, Cash, Dispute, etc.).
- **Emission Factors**: Mapping CO2 grams-per-mile to specific fleet vendors.

### What you must build:

A **Full-Stack Data Infrastructure** that:

1. Ingests raw taxi, weather, and reference data.
2. **Silver Rule Engine**: Cleans data and implements "Anomaly Detection" and "Sustainability Logic."
3. **Gold Star Schema**: Implements a Multi-Fact model with 3 Facts and 7 Conformed Dimensions.
4. **Hardened Orchestration**: Runs on a schedule via Airflow/Docker with Quality Gates.
5. **Visual Intelligence**: An interactive **Streamlit Dashboard** connected to Snowflake for real-time executive reporting.

---

## 4. Tools Required

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.10+ | Ingestion scripts & Streamlit Dashboard |
| **SQL** | Standard | All transformations inside Snowflake |
| **dbt Core** | 1.7+ | Data transformation framework |
| **Apache Airflow** | 2.8+ | Pipeline orchestration |
| **Snowflake** | Free trial | Cloud data warehouse |
| **Docker** | Latest | Containerized environment |
| **Streamlit** | Latest | **Visual Intelligence Layer** |

---

## 5. Core Concepts Per Tool

### 5.7 Streamlit — The Visual Layer
- **Concept 1: Snowflake Connection**: Efficiently querying Snowflake from a web app using `st.connection`.
- **Concept 2: Cache Management**: Using `@st.cache_data` to ensure the dashboard is fast and doesn't waste Snowflake credits.
- **Concept 3: Reactive Filtering**: Building interactive toggles (Borough, Weather, Date) that update the underlying SQL queries.
- **Concept 4: Data Visualization**: Using Plotly or Altair to visualize mobility trends and CO2 intensity.

---

## 8. Phase-by-Phase Implementation Guide

### Phase 1: Ingestion & Infrastructure (Hardened)

**Goal:** Extract data from diverse sources and load them into the Snowflake Bronze layer using a **Modular Framework**.

**Task 1.1: The Elite Engine**
- **Action**: Build a `core/` module with a Singleton `config.py` for "Fail-Fast" validation and a `database.py` using Context Managers for Snowflake connection lifecycles.
- **Requirement**: Abstract common logic (Logging, Connections, Config) to prevent code duplication.

**Task 1.2: The Template Pattern**
- **Action**: Implement a `BaseIngestor` class that defines the standardized extraction/loading workflow.
- **Requirement**: Refactor `taxi`, `weather`, and `zone` scripts to inherit from the base engine.

**Task 1.3: Bronze Ingestion**
- **Action**: Load the following into `URBANFLOW_DB.BRONZE`:
    - `RAW_TAXI_TRIPS` (Parquet files)
    - `RAW_WEATHER_HOURLY` (API JSON)
    - `RAW_TAXI_ZONE_LOOKUP` (CSV)

### Phase 5: Visual Intelligence (Streamlit)

**Goal:** Provide a self-service analytics platform for TLC executives.

**Task 5.1: The Connection**
- **Action**: Create a `dashboard/app.py` file.
- **Requirement**: Establish a secure connection to the **Snowflake Gold Layer** (using secrets).

**Task 5.2: The KPI View**
- **Action**: Build three interactive "Value Tiles" for Total Revenue, Total CO2, and Trip Count.

**Task 5.3: The Mobility Map**
- **Action**: Use the `dim_zones` and `fact_taxi_trips` to visualize pickup density on a map or ranked bar chart.

**Task 5.4: The Weather Impact Chart**
- **Action**: Create a reactive chart that allows users to see how Demand and Fare change based on the weather category.

---

## 10. Deliverables Checklist (Full Stack)

### Visuals & Analytics
- [ ] **Streamlit App**: `dashboard/app.py` functioning and connected to Snowflake.
- [ ] **Interactive Filters**: Functioning toggles for Date, Borough, and Weather.
- [ ] **Sustainability Insights**: Visual representation of CO2 emissions per vendor.
- [ ] **Financial Auditing**: View showing "Price Anomalies" for airport trips.
