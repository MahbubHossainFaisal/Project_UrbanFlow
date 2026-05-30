# 01 - Executive Dashboard Foundation

## Session Focus
This note captures the first Streamlit dashboard layer for UrbanFlow.

The goal was to create a usable executive overview backed by Snowflake gold tables, not a landing page or mock dashboard.

---

## Dashboard Entry Point
The app entry point is:

```text
streamlit_app.py
```

Run it with:

```bash
uv run streamlit run streamlit_app.py
```

Local URL:

```text
http://localhost:8501
```

---

## Data Source Pattern
The dashboard connects directly to Snowflake using environment variables from `.env`.

It reads from the gold schema by default:

```text
URBANFLOW_DB.GOLD
```

The schema can be overridden with:

```text
SNOWFLAKE_GOLD_SCHEMA
```

The app uses cached Streamlit functions:

```python
@st.cache_resource
@st.cache_data(ttl=600)
```

This keeps the Snowflake connection reusable and avoids rerunning every query on every widget interaction.

---

## Executive Overview KPIs
The first dashboard view includes:

```text
Trips
Revenue
Average fare
CO2 kg
Price anomalies
Average distance
Average duration
Precipitation trip share
Short-efficiency-risk trips
```

These metrics come from:

```text
gold_fact_trips
gold_fact_financials
gold_fact_sustainability
gold_agg_demand_weather
```

---

## Visuals
The first page includes:

```text
Demand by borough
Hourly demand
Weather demand mix
Airport fare watchlist
```

These are intended for scanning by leadership and operations users.

---

## Date Bound Guardrail
The initial date-bound query exposed a stray historical timestamp in the fact table.

The dashboard now derives its default date range from daily trip volume:

```text
only dates with at least 1,000 non-anomalous trips
```

This keeps the default executive view focused on meaningful operating periods.

---

## Validation
Validation completed:

```text
uv sync
uv run python -m py_compile streamlit_app.py
Streamlit import: 1.58.0
Snowflake date bounds: 2023-01-01 to 2023-02-28
Overview query path returned February KPI data
Streamlit server responded with HTTP 200 at localhost:8501
```

The in-app Browser skill was unavailable in this environment, so visual browser verification could not be completed from Codex. The server is running and reachable locally.

---

## Next Step
Expand from the executive overview into dedicated pages:

```text
Demand and weather
Financial integrity
Sustainability
Pipeline health
```
