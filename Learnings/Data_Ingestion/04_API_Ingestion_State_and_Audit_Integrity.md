# Learning: API Ingestion, State, & Audit Integrity

## 🛡️ The Challenge: Moving Beyond Static Files
While CSVs are simple, most production data flows from **APIs**. This introduces the challenge of **State**—parameters like dates, latitude, or API keys that change between runs.

## 🏗️ The "Elite" Solution: Parameterized Ingestors
We refactored the Weather Ingestor to handle dynamic state by passing parameters into the class constructor (`__init__`).

### 1. Managing State in Classes
Instead of hardcoding dates inside the script, we pass them during instantiation:
```python
weather_ingestor = WeatherIngestor(start_date="2023-01-01", end_date="2023-01-31")
```
*   **Strategic Rationale**: This makes the class **reusable**. The same class can now be used in a loop to ingest 10 years of data or in an Airflow DAG to ingest only yesterday's data.

### 2. Audit Integrity (The "Full URL" Rule)
In an "Elite" pipeline, you must be able to prove exactly what data was requested from a source 6 months later.
*   **The Issue**: Storing just the base URL (`https://api.weather.com`) is insufficient.
*   **The Solution**: Capture the **`response.url`** after the request is made. This includes all query parameters (dates, coordinates, etc.).
*   **Implementation**: Store this full URL in a class attribute (`self.actual_request_url`) during the `extract` phase and write it to the `SOURCE_URL` column during the `transform` phase.

## 🧠 Architect's Insight: Exception Propagation
In a modular framework, the **Base Class** is the "Brain" and the **Child Class** is the "Worker."
*   **The Trap**: Catching an error in the child class and returning `None`. This "silences" the error, causing the Brain to think everything is fine until the next step crashes.
*   **The Elite Way**: Use `raise` inside the child class. This ensures the error reaches the `BaseIngestor.run()` method, where it can be properly logged, timed, and flagged as a "Job Failure."

## ⚙️ The `auto_create_table` Nuance
We leveraged the `write_pandas` feature `auto_create_table=True`.
*   **When to use it**: In Bronze/Raw layers where schema flexibility is more important than strict control.
*   **Why to avoid it in Gold**: Auto-creation lacks support for constraints (NOT NULL, PK), specific precision for decimals, and documentation. 
*   **Senior Rule**: Trust but verify. Use Auto-Create as a fallback, but rely on **Explicit DDLs (SQL)** or **dbt** for production-grade schema enforcement.

**Key Takeaway**: "A production-grade ingestor is not just a data mover; it is a witness. It must record exactly what was requested, when it happened, and fail loudly if the contract is broken."
