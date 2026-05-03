# Phase 2: The Silver Layer (Transformation & Cleaning)
## Goal: Turn "Raw Garbage" into "Clean Data"

### Step 1: Establish the Connection (The Source)
- **Action**: Tell dbt where the raw data lives in Snowflake.
- **Why**: Instead of hardcoding "URBANFLOW.BRONZE.TABLE_NAME" everywhere, we create a central "phonebook" (sources.yml).
- **Outcome**: dbt can now "see" our three Bronze tables.

### Step 2: Build the Staging Models (The "Filter" House)
For each raw table, we create a corresponding "Staging" model. This is where the heavy lifting happens in 6 logical movements:

1.  **Selection**: Select everything from the Source.
2.  **Standardization**: 
    - Ensure dates are actually dates, and numbers are actually numbers.
    - Standardize column names if they are messy.
3.  **Deduplication**: 
    - Use a "Ranking" logic to find exact duplicates and keep only the first/latest one.
4.  **Cleaning (Business Rules)**:
    - **Taxi**: Throw away "impossible" data (negative fares, zero distances, trips from the year 2099).
    - **Weather**: Transform technical codes (e.g., Code 61) into human words (e.g., 'Rain').
5.  **Enrichment (Calculated Columns)**:
    - Calculate how many minutes a trip lasted.
    - Extract the "Hour" from the timestamp so we can join it to weather later.
6.  **Surrogate Keys**: 
    - Create a "Unique Fingerprint" for every row (a Trip ID) so we can track it.

### Step 3: Data Quality Testing (The Gatekeeper)
- **Action**: Write rules that the data MUST follow.
- **Rules**:
    - "No null values allowed in the Fare column."
    - "The Trip ID must be unique (no duplicates)."
    - "The Weather category must be one of our approved words."
- **Outcome**: If the data is "dirty," the test fails and warns us BEFORE we show it to the client.

### Step 4: Documentation (The User Manual)
- **Action**: Write plain-English descriptions for what every column means.
- **Outcome**: Anyone can run a command and see a beautiful website showing how the data flows from Bronze to Silver.

### Summary of Workflow:
**Source (Bronze)** -> **Cleaning/Deduplication (Silver Model)** -> **Testing (Validation)** -> **Documenting**
