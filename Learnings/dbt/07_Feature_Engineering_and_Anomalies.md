# Learning Note 07: Feature Engineering & Financial Integrity

## 🎯 The Strategic Context
In this phase, we moved from "Cleaning" to "Enriching." We transitioned the Silver layer from a simple staging area into an **Intelligence Engine** capable of calculating environmental impact and identifying financial outliers.

---

## 1. The Sustainability Engine (Feature Engineering)
- **Concept**: Injecting domain-specific business logic (CO2 emissions) directly into the transformation pipeline.
- **Implementation**: 
    - Used a `LEFT JOIN` with `seed_emission_factors` to ensure no trip records were lost (transparency).
    - Used `COALESCE(..., 406.0)` to handle unknown vendors, ensuring our sustainability metrics are never `NULL`.
- **Architectural Why**: By calculating CO2 in the Silver layer, we make it a "first-class citizen" for any downstream model or analyst.

## 2. Anomaly Detection (Defensive Engineering)
- **Problem**: Raw data often contains "noise" (e.g., $5,000 fares or 500-mile trips in a city).
- **Elite Solution**: Instead of deleting these rows, we **flagged** them (`is_distance_anomaly`, `is_fare_anomaly`).
- **Rationale**: This maintains **Data Lineage**. We keep the "trash" for auditors to see, but we give the Gold layer the power to filter it out for executive reporting.
- **Impact**: In our current dataset, we successfully isolated 81 anomalies, preventing them from skewing our business averages.

## 3. The "Clean" Aggregate Pattern
- **Concept**: Creating a Gold-layer aggregate specifically designed for high-speed dashboard consumption.
- **Pattern**: 
    - **Filter Early**: We filtered out anomalies in the first CTE of the aggregate model.
    - **Pre-calculate**: We summed and averaged CO2 and Revenue at the Borough/Weather grain.
- **Performance**: This reduces the dashboard's query time from seconds to milliseconds, as Snowflake only has to read the pre-aggregated results.

---

## 🏗️ Architect's Tip
*“Data Engineering is 20% cleaning and 80% building trust. By flagging anomalies instead of hiding them, and by baking sustainability into your staging layer, you provide both transparency and value to the business.”*
