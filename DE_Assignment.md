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

A **multi-layered Star Schema pipeline** (Bronze → Silver → Gold) that:

1. Ingests raw taxi, weather, and reference data.
2. **Silver Rule Engine**: Cleans data and implements "Anomaly Detection" (Rate auditing) and "Sustainability Logic" (CO2 calculation).
3. **Gold Star Schema**: Implements a Multi-Fact model with 3 Facts and 7 Conformed Dimensions.
4. **Hardened Orchestration**: Runs on a schedule via a custom-built Airflow environment in Docker with Task Groups and SLA monitoring.
5. **Quality**: Is fully tested via dbt and custom SQL "Quality Gates."

---

## 5. Core Concepts Per Tool

### 5.4 Apache Airflow — Elite Concepts
- **Concept 1: Task Groups**: Organizes DAG complexity into visual clusters (e.g., `ingestion_group`, `transformation_group`).
- **Concept 2: Dynamic Backfilling**: Using `{{ ds }}` and `{{ next_ds }}` macros to make scripts date-aware, allowing you to re-run any month in history without code changes.
- **Concept 3: SLAs & Callbacks**: Implementing `on_failure_callback` to trigger notification tasks (Email/Slack) or cleanup tasks.
- **Concept 4: ShortCircuitOperator**: Designing "Quality Gates" that stop the pipeline if critical data quality thresholds are not met (e.g., "Stop if > 50% of trips are anomalies").
- **Concept 5: Airflow Pools**: Managing concurrency to prevent your local machine from being overwhelmed by too many parallel ingestion tasks.

### 5.6 Docker — Elite Concepts
- **Concept 1: Multi-Service Orchestration**: Understanding how the Airflow Webserver, Scheduler, and Worker communicate via a shared network.
- **Concept 2: Custom Dockerfiles**: Building a specialized Airflow image that pre-installs `uv`, `dbt-snowflake`, and `pyarrow` for maximum reliability.
- **Concept 3: Volume Mounting Patterns**: Strategically mounting only the necessary directories (`dags`, `dbt`, `ingestion`) while protecting system-level configuration.
- **Concept 4: Docker Healthchecks**: Implementing automated checks to ensure the database and scheduler are healthy before starting DAGs.
- **Concept 5: Resource Management**: Using `deploy: resources` in Compose to set CPU and Memory limits (simulating a production Kubernetes environment).

---

## 8. Phase-by-Phase Implementation Guide

### Phase 4: Hardened Orchestration (Airflow & Docker)

**Goal:** Transform the pipeline into an autonomous, fault-tolerant system.

**Task 4.1: The Custom Infrastructure**
- **Action**: Create a `Dockerfile` that extends the official Airflow image.
- **Requirement**: Use `uv` to install dependencies for speed. Ensure `dbt-snowflake` is installed at the system level within the container.
- **Action**: Configure `docker-compose.yaml` with dedicated healthchecks for the Postgres metadata DB.

**Task 4.2: The "Elite" DAG Design**
File: `dags/dag_urbanflow_master.py`
- **Requirement**: Implement **Task Groups** to separate `ingestion_stage` from `transformation_stage`.
- **Requirement**: Use the **`ShortCircuitOperator`** after ingestion to verify that at least 1M rows were loaded before allowing dbt to run.
- **Requirement**: Implement a "Failure Notification" task that triggers only if any part of the pipeline fails.

**Task 4.3: Parameterization & Backfilling**
- **Action**: Ensure your Python ingestion scripts accept date parameters from Airflow's `{{ ds }}`.
- **Requirement**: Demonstrate a "Backfill" by triggering the DAG for a month in the past (e.g., Dec 2022) using the Airflow CLI.

---

## 10. Deliverables Checklist (Elite Infrastructure)

### Orchestration & Environment
- [ ] **Hardened Docker Stack**: Custom `Dockerfile` and `docker-compose.yml` with resource limits.
- [ ] **Master DAG**: Featuring **Task Groups**, **Short-Circuit logic**, and **SLA monitoring**.
- [ ] **Cross-Task Communication**: Use of **XComs** to pass record counts from Ingestion to Validation.
- [ ] **Automated Testing**: Airflow task that executes `dbt test` and halts the pipeline on any failure.

### Knowledge Deliverables
- [ ] **Failure Scenario Report**: A log of what happened when you deliberately broke the pipeline (e.g., disconnecting Snowflake) and how Airflow responded (Retries, Callbacks).
- [ ] **Infrastructure Map**: A brief diagram/text explaining how your Docker containers interact.
