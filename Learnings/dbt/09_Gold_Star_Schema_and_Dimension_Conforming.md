# Learning Note 09: Gold Star Schema & Dimension Conforming

## 🎯 The Strategic Context
Today we completed the transition from a "Clean Data Layer" (Silver) to a "Business Intelligence Engine" (Gold). By finalizing the **Multi-Fact Star Schema**, we’ve ensured that the data is not just clean, but "Ready for the Mayor."

---

## 1. The Sustainability KPI Engine
- **Concept**: Moving from raw counts to **Efficiency Ratios**.
- **Implementation**: We built `gold_fact_sustainability` using `CO2 Grams / (Distance * Passengers)` to calculate **CO2 per Passenger Mile**.
- **Policy Intelligence**: We added the `is_short_efficiency_risk` flag (trips < 1.5mi) to identify areas where mobility could be shifted to more sustainable modes (bikes/walking).
- **Architecture Tip**: Always use `NULLIF(..., 0)` when dividing by metrics like passenger counts to prevent "Division by Zero" crashes.

## 2. Conforming the Dimensions
- **Strategy**: A dimension is "Conformed" when it is the single source of truth for multiple facts.
- **Promotion Pattern**: We promoted Silver/Seed tables (Zones, Vendors, Payment Types) to Gold.
- **Added Value**: 
    - **Geographical Grouping**: In `dim_zones`, we added `is_airport` and `borough_group` (Core vs. Outer).
    - **Weather Categorization**: In `dim_weather_lookup`, we used a macro to turn raw codes into business categories (Clear, Rain, Snow).

## 3. Normalization for Storage, Denormalization for Analysis
- **The Balance**:
    - **Facts (Normalized)**: Store small integers/IDs (e.g., `weather_code`, `vendor_id`) to keep the table size manageable.
    - **Dimensions (Denormalized)**: Store the human-readable descriptions and analytical groupings.
- **Benefit**: This architecture makes the dashboard fast (joining small keys) while being user-friendly (displaying names instead of IDs).

## 4. The "Data Guard" Principles
- **Robustness**: Using `ILIKE '%AIRPORT%'` instead of `LIKE` to handle case-sensitivity issues in source data.
- **Idempotency**: Using `materialized='table'` in Gold ensures that a `dbt run` completely rebuilds the truth, allowing for safe logic updates.
- **Isolation**: Keeping Gold models dependent only on other Gold/Silver models, avoiding direct links to "Raw" seeds.

## 5. Technical Troubleshooting (The "Aha!" Moments)
- **Snowflake Syntax**: Remember that `TO_CHAR(datetime, 'YYYYMMDD')` is the required syntax for temporal ID conversion.
- **Dbt Precedence**: Global dbt profiles (`~/.dbt/profiles.yml`) can sometimes override local project profiles. Always use `--profiles-dir .` or specific environment variables when working with multiple Snowflake accounts.

---

## 🏗️ Architect's Tip
*“A Star Schema is more than just a join; it is a contract with the business. Every dimension you conform is a promise that the answer will be the same regardless of which Fact table they query.”*
