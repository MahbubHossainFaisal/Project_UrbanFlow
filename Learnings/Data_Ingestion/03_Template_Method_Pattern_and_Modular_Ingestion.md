# Learning: The Template Method Pattern & Modular Ingestion

## 🎭 The Concept: The Template Method Pattern
As projects grow, writing the same "Extract-Transform-Load" (ETL) logic in every script leads to **Maintenance Debt**. The **Template Method Pattern** solves this by defining the *skeleton* of an algorithm in a base class, while letting subclasses redefine certain steps without changing the algorithm's structure.

### 1. The "Base Class" Contract (The Brain)
We used Python's `abc` (Abstract Base Classes) module to create `BaseIngestor`.
*   **`run()`**: The "Template Method." It defines the sequence: `extract()` -> `transform()` -> `load()`.
*   **`@abstractmethod`**: Acts as a mandatory "to-do list" for any specific ingestor. If a child class doesn't implement `extract()`, Python will throw an error before the code even runs.

### 2. Benefits of Modular Inheritance
*   **Code Reduction**: Our `ZoneLookupIngestor` reduced boilerplate by ~60%. It no longer needs to know *how* to connect to Snowflake or *how* to log durations; it only cares about its specific data source.
*   **Observability**: Because the `run()` method is centralized, we can add timers, row counts, or Slack alerts in one place, and **every** ingestion job automatically gains those features.
*   **Explicit Parameters**: By passing "knobs" like `overwrite=True` through the `super().__init__` call, we maintain clear control over database behavior while keeping the code clean.

## 🛡️ Data Integrity: The "Epoch" Trap
During refactoring, we discovered that Pandas sometimes translates `datetime` objects into large integers (Epoch timestamps) when loading into Snowflake.

### The "Elite" Fix: Explicit Casting
*   **Junior Approach**: Fix it in Snowflake manually or ignore it.
*   **Senior Approach**: Enforce an ISO-standard format in the **Transform** step using `.strftime("%Y-%m-%d %H:%M:%S")`.
*   **Rationale**: Explicitly converting dates to strings before loading ensures the database correctly identifies the column as a `TIMESTAMP`, preventing "Data Type Chaos."

## 🧠 Architect's Insight: When to Refactor?
We don't refactor just to make code "pretty." We refactor when we identify **Shared Behavior**.
*   **Taxi Trips**: Large volume, Parquet source.
*   **Weather**: API source, JSON format.
*   **Zone Lookup**: Static CSV source.
*   **Shared Behavior**: All three need a connection, all three need logging, all three need a standard lifecycle. **This is why we built the Framework.**

**Key Takeaway**: "Consistency is the foundation of trust in data engineering. A framework ensures that every job, no matter how small, meets the team's production standards."
