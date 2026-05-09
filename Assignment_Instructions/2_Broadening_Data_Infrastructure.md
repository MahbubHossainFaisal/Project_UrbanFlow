# Broadening Data Infrastructure: The UrbanFlow Elite Expansion

## 1. 🔍 Current State Assessment (Phase 3 Baseline)
We have successfully implemented a functional **Medallion Architecture** that solves a foundational "Demand vs. Weather" problem.

*   **Bronze**: Raw ingestion of Taxi, Weather, and Zone data.
*   **Silver**: Cleaned staging models with microsecond corrections, deduplication, and weather classification.
*   **Gold**: A single Fact table (`gold_fact_trips`) and one summary aggregation (`gold_agg_demand_weather`).
*   **Status**: Technically sound but "Flat." It lacks the relational complexity of a true enterprise-grade Data Mart.

---

## 2. 🎯 The Business Problem: Beyond Simple Demand
The **NYC Taxi & Limousine Commission (TLC)** is moving beyond "how many rides did we do?" They now face three critical challenges:
1.  **Revenue Integrity**: Are drivers/vendors charging the correct flat rates for airports? Are tips declining?
2.  **Sustainability Mandate**: What is the carbon footprint of the NYC taxi fleet, and which boroughs are the "dirtiest"?
3.  **Operational Seasonality**: How do holidays, peak hours, and specific payment methods affect fleet efficiency?

To answer these, we must evolve from a "Simple Pipeline" to a **"Multi-Fact Star Schema."**

---

## 3. 🏗️ New Arrangement Requirements (The "Elite" Blueprint)

### A. Dimensional Expansion (The Context)
We will move from 2 dimensions to **7 Core Dimensions**:
1.  **`dim_zones`**: (Existing) Geographic context.
2.  **`dim_weather`**: (Existing) Environmental context.
3.  **`dim_calendar`**: (NEW) Temporal context including Holidays, Weekends, and "Business vs. Leisure" flags.
4.  **`dim_rate_codes`**: (NEW) Mapping numeric IDs (1-6) to business logic (JFK Flat Rate, Negotiated, etc.).
5.  **`dim_payment_types`**: (NEW) Mapping IDs (1-6) to Credit, Cash, Dispute, etc.
6.  **`dim_vendors`**: (NEW) Analyzing the performance of different fleet operators (VeriFone vs. CMT).
7.  **`dim_vehicle_emissions`**: (NEW) Mapping emission factors (CO2 grams/mile) to vehicle types.

### B. Multi-Fact Implementation (The Events)
We will build three distinct Fact tables at different grains:
1.  **`fact_taxi_trips`**: Focuses on **Demand and Volume** (Grain: One row per trip).
2.  **`fact_financial_performance`**: Focuses on **Money Flow** (Fare, Tips, Tolls, Surcharges, and "Price Integrity" flags).
3.  **`fact_environmental_impact`**: Focuses on **Sustainability** (Calculated CO2 emissions per trip).

---

## 4. 🛠️ The Detailed Solution & Roadmap

### Phase 1: Dimensional Foundation (The "Kimball" Strategy)
*   **Action**: Use `dbt seeds` for static data (Rate Codes, Payment Types, Emission Factors).
*   **Action**: Build a SQL-based `dim_calendar` generator in Snowflake to handle NYC-specific holidays.
*   **Goal**: Create a rich set of "Adjectives" to describe our ride data.

### Phase 2: Silver Layer Logic Expansion (The "Business Rule" Engine)
We will refactor `stg_taxi_trips` to move beyond cleaning and into **Feature Engineering**:
*   **Anomaly Detection**: Flag trips where `rate_code = 2` (JFK) but `fare_amount != $70` (or current flat rate).
*   **Emission Logic**: Join with emission factors at the Silver level to calculate `estimated_co2_grams` per trip.
*   **Financial Slicing**: Separate base fare from surcharges and tips for granular reporting.

### Phase 3: The Multi-Fact Gold Layer
We will build the **Star Schema** by joining our Enriched Silver data with our 7 Dimensions.
*   Implementation of the **Kimball Bus Matrix** to ensure "Conformed Dimensions" (e.g., the same `dim_calendar` is used by all facts).

### Phase 4: The Denormalized "Data Mart" View
*   **Action**: Create a "Wide Table" (Mart) for end-users that joins all facts and dimensions.
*   **Goal**: Allow a "One-Click" analysis: *"Which vendor had the highest CO2 emissions during Christmas week in Brooklyn using Credit Cards?"*

---

## 🎓 Why This Is "Industry Grade"
1.  **Complex Joins**: You are managing a 7-way join, requiring high-performance SQL.
2.  **Data Quality (DQ) as a Feature**: You aren't just cleaning data; you are creating "Flags" (e.g., `is_airport_flat_rate_violation`) that provide immediate value to auditors.
3.  **Sustainability Focus**: This reflects modern ESG (Environmental, Social, and Governance) reporting requirements in the corporate world.
4.  **Star Schema Mastery**: You are proving you can design a system where dimensions are shared across multiple facts.

---
**Next Step**: We begin **Phase 1: Dimensional Foundation**. We will start by generating the `dim_calendar` and ingesting the Reference Mappings for Rate Codes and Payment Types.
