# Learning Note 08: Financial Integrity & Multi-Fact Architecture

## 🎯 The Strategic Context
As we moved into the **Gold Layer**, we transitioned from a "Flat Model" to a **Multi-Fact Star Schema**. Our first specialized model, `gold_fact_financials`, was designed to audit revenue integrity specifically for high-value airport trips.

---

## 1. Data Profiling for Business Rules (Finding the Signal)
- **Concept**: Before building an audit model, you must find the "Ground Truth" in the data.
- **Implementation**: We used grouping and counting on `fare_amount` for specific `rate_code_id`s to identify the JFK flat rate of **$70.0**.
- **Learning**: JFK showed a clear "Signal" (a massive spike at $70), whereas Newark showed "Noise" (scattered pricing), indicating Newark is likely metered + surcharges rather than a flat rate.

## 2. Specialized Fact Tables (Financial Integrity)
- **Concept**: Instead of bloating a single fact table with every metric, we create specialized facts (Sustainability, Financials, Mobility).
- **Rationale**: This allows for modular expansion. If the TLC adds new financial rules, we only update the Financial Fact, leaving the Sustainability and Mobility models untouched.

## 3. The "Baseline of Zero" Logic
- **Pattern**: `Variance = Actual - Expected`.
- **Logic**: For trips where we don't have a known benchmark (like Standard trips), we set `Expected = Actual`.
- **Benefit**: This results in a variance of **0**, which prevents "Non-JFK" trips from skewing aggregate financial reports while keeping the formula consistent across all rows.

## 4. Dbt Lineage & Dependency Management
- **Rule**: Prefer Staging (`stg_`) models as sources for Gold models.
- **Avoidance**: We avoided selecting from `gold_fact_trips` to prevent **Circular Dependencies** and ensure the model is as fast and independent as possible.
- **Impact**: This keeps the dbt Directed Acyclic Graph (DAG) clean and professional.

## 5. Identifying High-Risk Offenders
- **Analysis**: By grouping variances by `vendor_id`, we discovered that while one vendor had more frequent errors, another had **higher dollar-value deviations**.
- **Business Value**: This allows the city to prioritize audits on "High-Impact" vendors rather than just "High-Frequency" ones.

---

## 🏗️ Architect's Tip
*“A great Data Warehouse doesn't just store data; it holds the business accountable. By building dedicated integrity models, you turn your pipeline into an automated financial auditor.”*
