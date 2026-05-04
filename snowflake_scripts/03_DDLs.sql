 CREATE TABLE IF NOT EXISTS BRONZE.RAW_TAXI_TRIPS (
      -- Original TLC columns (Yellow Taxi schema)
      VendorID INTEGER,
      tpep_pickup_datetime TIMESTAMP_NTZ,
      tpep_dropoff_datetime TIMESTAMP_NTZ,
      passenger_count FLOAT,
      trip_distance FLOAT,
      RatecodeID FLOAT,
      store_and_fwd_flag VARCHAR,
      PULocationID INTEGER,
      DOLocationID INTEGER,
      payment_type INTEGER,
      fare_amount FLOAT,
      extra FLOAT,
      mta_tax FLOAT,
      tip_amount FLOAT,
      tolls_amount FLOAT,
      improvement_surcharge FLOAT,
      total_amount FLOAT,
      congestion_surcharge FLOAT,
      Airport_fee FLOAT,
      -- Audit columns
      SOURCE_FILE VARCHAR,
      LOADED_AT TIMESTAMP_NTZ
  );

  select * from BRONZE.RAW_TAXI_TRIPS;
  --delete from BRONZE.RAW_TAXI_TRIPS;
  select count(*) from BRONZE.RAW_TAXI_TRIPS; -- file 1 has 3066766 data
  
   select * from BRONZE.RAW_WEATHER_HOURLY;
    --delete from BRONZE.RAW_WEATHER_HOURLY;
    -- drop table BRONZE.RAW_WEATHER_HOURLY;

select * from BRONZE.RAW_ZONE_LOOKUP;
-- drop table BRONZE.RAW_ZONE_LOOKUP;