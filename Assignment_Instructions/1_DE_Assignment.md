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

The client wants a **Multi-Fact Star Schema Datamart** that can answer complex cross-cutting questions like: *"Which vendor had the highest CO2 emissions during Christmas week in Brooklyn using Credit Cards?"*

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

A **Medallion Star Schema** (Bronze → Silver → Gold) that:

1. Ingests raw taxi, weather, and reference data.
2. **Silver Rule Engine**: Cleans data and implements "Anomaly Detection" (Rate auditing) and "Sustainability Logic" (CO2 calculation).
3. **Gold Star Schema**: Implements a Multi-Fact model with 3 Facts and 7 Conformed Dimensions.
4. Orchestrates the entire lifecycle via Airflow/Docker.

---

## 3. Architecture & Workflow Design

### 3.1 The Star Schema Evolution (Gold Layer)

In the Elite version of this project, we move from a "Flat Join" to a **Star Schema**. This allows us to share dimensions across multiple business processes (Facts).

```
          DIM_CALENDAR        DIM_WEATHER        DIM_ZONES
               │                  │                  │
               └──────────┬───────┴────────┬─────────┘
                          │                │
          ┌───────────────▼──────────┐     │     ┌────────────────────────┐
          │     FACT_TAXI_TRIPS      │     ├─────▶   FACT_EMISSIONS       │
          │ (Demand & Volume events) │     │     │ (Sustainability events)│
          └───────────────▲──────────┘     │     └────────────────────────┘
                          │                │
               ┌──────────┴────────┬───────┴─────────┐
               │                   │                 │
          DIM_VENDORS       DIM_RATE_CODES     DIM_PAYMENT_TYPES
```

---

## 4. Tools Required
*(Unchanged: Python, SQL, dbt Core, Airflow, Snowflake, Docker)*

---

## 7. Project Structure & Directory Layout

```
urbanflow-analytics/
├── ingestion/ ...
├── dags/ ...
├── dbt/
│   ├── seeds/
│   │   ├── seed_rate_codes.csv       # ← NEW: Rate code mappings
│   │   ├── seed_payment_types.csv    # ← NEW: Payment type mappings
│   │   └── seed_emissions.csv        # ← NEW: CO2 grams/mile per vendor
│   ├── models/
│   │   ├── silver/
│   │   │   ├── stg_taxi_trips.sql     # ← ENRICHED: With Anomaly & CO2 logic
│   │   │   └── stg_weather_hourly.sql
│   │   └── gold/
│   │       ├── dim_calendar.sql       # ← NEW: SQL-generated date dimension
│   │       ├── fact_taxi_trips.sql    # ← FACT 1: Demand
│   │       ├── fact_financials.sql    # ← FACT 2: Revenue/Auditing
│   │       ├── fact_emissions.sql     # ← FACT 3: Sustainability
│   │       └── mart_mobility_360.sql  # ← NEW: Wide view for analysts
```

---

## 8. Phase-by-Phase Implementation Guide (Elite)

### Phase 1: The Dimensional Foundation
**Task**: Ingest reference data using `dbt seed`.
**Task**: Build `dim_calendar.sql` using a SQL generator to handle NYC holidays and peak/off-peak windows.
**Task**: Map Rate Codes and Payment Types to human-readable labels.

### Phase 2: Silver Layer — Feature Engineering
**Task**: Update `stg_taxi_trips` to include:
- **Financial Anomaly Flag**: If `rate_code = 2` (JFK) but `fare_amount != $70`, flag it.
- **Sustainability Calculation**: Calculate `estimated_co2_grams` using `trip_distance * emission_factor`.
- **Temporal Slicing**: Identify "Peak Hours" (Rush hour) vs "Off-Peak."

### Phase 3: Gold Layer — Multi-Fact Modeling
**Task**: Build 3 Fact tables sharing the same 7 dimensions (The Kimball "Bus Matrix").
- `fact_taxi_trips`: Grain: One row per trip. Metrics: volume, duration, distance.
- `fact_financial_performance`: Grain: One row per trip. Metrics: fare, tips, tolls, and "Price Integrity" flags.
- `fact_environmental_impact`: Grain: One row per trip. Metrics: CO2 grams, emission intensity.

### Phase 4: The Denormalized Data Mart
**Task**: Create `mart_mobility_360.sql`. 
- Join all Facts and Dimensions into a single "Wide Table" for the final business report.

---

## 9. Validation & Verification (Elite)

| Check | Expected Result |
|-------|-----------------|
| **Financial Audit** | Trips to JFK (`rate_code=2`) should show high "Price Anomaly" flags if fare != $70. |
| **Sustainability** | Total CO2 in `fact_emissions` should correlate with `trip_distance`. |
| **Conformed Dimensions** | The `dim_calendar` must result in 0 null joins across all 3 facts. |
| **Star Schema Integrity** | No "Fan-out" (duplicates) when joining dimensions to facts. |

---

## 10. Deliverables Checklist (Elite)
- [ ] `dbt seed` data for Rate Codes, Payment Types, and Emissions.
- [ ] `dim_calendar.sql` with holiday/peak-hour flags.
- [ ] `stg_taxi_trips.sql` with CO2 and Anomaly logic.
- [ ] 3 separate Fact tables (`trips`, `financials`, `emissions`).
- [ ] `mart_mobility_360` wide view.
- [ ] Airflow DAG orchestrating the multi-fact build.

---
**Lead Architect's Note**: You are no longer building a script; you are building an **Urban Operating System**. Every join and calculation now serves a specific city-wide policy goal (Sustainability, Revenue, Demand).
