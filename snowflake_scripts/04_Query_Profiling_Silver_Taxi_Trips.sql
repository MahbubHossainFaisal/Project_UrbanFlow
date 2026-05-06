/*
Query profiling thinking:

 1. The "Structural Integrity" Questions (The Nulls)
   * The Question: "If VENDORID or TPEP_PICKUP_DATETIME is NULL, does this row even represent a trip?"
   * The Intuition: In a relational database, these are your "Primary" attributes. A trip without a start time is like a ghost.
   * The Decision: If these are NULL, do we try to fix them (impute) or do we drop them because they are fundamentally broken?

  2. The "Physical Reality" Questions (Zeros & Negatives)
   * The Question: "Can a taxi physically move 0.0 miles but charge a passenger $50.00? Or move 10 miles and charge $0.00?"
   * The Intuition: These represent "Edge Cases" or "System Errors" (like a driver accidentally starting the meter or a voided transaction).
   * The Decision: If we keep these "Zero Distance" trips, will they ruin our "Average Speed" or "Average Fare" calculations in the Gold layer?

  3. The "Temporal Logic" Questions (The Dates)
   * The Question: "Why does my max_date say the year 2050 or 50,000?"
   * The Intuition: This is your "Precision Alarm." It’s almost never a real date from the future; it's a signal that your system is misinterpreting the
     "scale" of the data (Microseconds vs. Seconds).
   * The Decision: If the dates are wrong, our join to the Weather Data will fail 100% of the time. How do I scale this number back to the year 2023?

  4. The "Uniqueness" Questions (The Duplicates)
   * The Question: "Is it possible for the same taxi (Vendor) to start a trip at the exact same second in the exact same location twice?"
   * The Intuition: Physical objects cannot be in two places at once. If duplicate_candidate_count is high, we likely have "Re-ingestion" issues (loading
     the same file twice).
   * The Decision: Which row do I keep? The one that was loaded most recently (max(loaded_at))?


Bucket 1: The Structural Fixes (The "Interpreter" Problem)
  The Problem: "Invalid Date" (Microsecond Precision).
   * The Intuition: This isn't "bad data"—it's a "bad translation." The data in the Parquet file is fine, but our Snowflake "eyes" are seeing microseconds
     as seconds.
   * The Thinking: We don't delete these rows. We fix them. If we delete them, we lose 99% of our data.
   * The Plan: In your casting CTE, you need to apply the math we discovered (Divide by 1,000,000) to bring the data back to 2023.

  Bucket 2: The Quality Filters (The "Noise" Problem)
  The Problem: 51k Negative Fares, 86k Zero Distances, 98k Zero Passengers.
   * The Intuition: These are "Ghost Trips." They represent system errors, driver mistakes, or cancelled rides where the meter was accidentally bumped.
   * The Thinking: If we include these in our "Average Fare" or "Average Speed" reports, they will pull the averages down and give a false picture of
     reality.
   * The Plan: In your filtered CTE, you will write WHERE clauses to "prune" this noise out of the pipeline.
*/


SELECT COUNT(*) as total_rows,
    COUNT(*) - COUNT(VENDORID) as null_vendors,
    COUNT(*) - COUNT(TPEP_PICKUP_DATETIME) as null_pickups,
    COUNT(*) - COUNT(PULOCATIONID) as null_pickup_locations,
    SUM(CASE WHEN FARE_AMOUNT <= 0 THEN 1 ELSE 0 END) as zero_or_neg_fare,
    SUM(CASE WHEN TRIP_DISTANCE <= 0 THEN 1 ELSE 0 END) as zero_or_neg_distance,
    SUM(CASE WHEN PASSENGER_COUNT <= 0 THEN 1 ELSE 0 END) as zero_passengers,
    MIN(TPEP_PICKUP_DATETIME) as min_date,
    MAX(TPEP_PICKUP_DATETIME) as max_date,
    COUNT(*) - COUNT(DISTINCT VENDORID || TPEP_PICKUP_DATETIME || PULOCATIONID) as duplicate_candidate_count
FROM URBANFLOW_DB.BRONZE.RAW_TAXI_TRIPS;

SELECT distinct  TPEP_PICKUP_DATETIME FROM BRONZE.RAW_TAXI_TRIPS LIMIT 1000;

/*
  3. The "Future Date" Alarm (The Intuition)
  When you saw "Invalid Date" or a year like 50,000, my "Architect Brain" did this math:

   * Fact A: The year 2023 is roughly 1.6 Billion seconds since 1970 ($1.6 \times 10^9$).
   * Fact B: Your raw number was roughly 1.6 Quadrillion ($1.6 \times 10^{15}$).
   * The Logic: If I take a number that is meant to be microseconds ($10^{15}$) and I tell Snowflake "Hey, these are seconds," Snowflake thinks: "Wow,
     that's a lot of seconds! Let me add 1.6 quadrillion seconds to the year 1970..."
   * The Result: Adding that many seconds lands you in the Year 50,000.

  4. The Fix
  To bring the Year 50,000 back to 2023, I need to shrink the number by the difference between a Second and a Microsecond.
   * 1 Second = 1,000,000 Microseconds.
   * Therefore: Divide by 1,000,000.

  ---

  🎓 The Lesson for You:
  Whenever you see a date that is thousands of years in the future, always check the "zeros."
   * If it's off by 3 zeros (1,000) -> It's Milliseconds.
   * If it's off by 6 zeros (1,000,000) -> It's Microseconds.


   Step 1: EXTRACT(EPOCH_SECONDS FROM ...)
  Even when Snowflake shows "Invalid Date," the raw number is still sitting there in the background. It’s just too big for the UI to show.
   * By using EXTRACT, we tell Snowflake: "Stop trying to show me a calendar. Just give me the raw, massive number of seconds you think have passed since
     1970."
   * Result: 1,672,533,129,971,200 (A massive integer).

  Step 2: / 1000000
  Now that we have a raw number, we can do standard math on it.
   * We divide by a million to shift the decimal point 6 places to the left.
   * Result: 1,672,533,129.9712 (This is the real number of seconds for the year 2023).

  Step 3: TO_TIMESTAMP_NTZ(...)
  Finally, we hand this corrected, smaller number back to Snowflake and say:
   * "Okay, now try again. Turn this number into a calendar date."
   * Result: 2023-01-01 00:32:09 (A perfect, valid date).
*/

SELECT TO_TIMESTAMP_NTZ(EXTRACT(EPOCH_SECONDS FROM TPEP_PICKUP_DATETIME) / 1000000) AS pickup_datetime
from BRONZE.RAW_TAXI_TRIPS LIMIT 100;

SELECT * FROM BRONZE.RAW_TAXI_TRIPS LIMIT 100;

SELECT * FROM SILVER.STG_TAXI_TRIPS;
