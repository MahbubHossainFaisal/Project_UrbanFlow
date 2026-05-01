import argparse # built in python library for command line arguments
import requests # for making http requests
import os # for interacting with the operating system
import pandas as pd # for data manipulation and analysis
import pyarrow.parquet as pq # for reading and writing parquet files
from datetime import datetime # for working with dates and times
import snowflake.connector as sf
from snowflake.connector.pandas_tools import write_pandas
from dotenv import load_dotenv
import logging
import time
import sys

# Load credentials from a .env file (standard practice)
load_dotenv()

SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE")
# setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

# Mapping of parquet column names to Snowflake column names
COLUMN_NAME_MAPPING = {
    'VendorID': 'VENDORID',
    'tpep_pickup_datetime': 'TPEP_PICKUP_DATETIME',
    'tpep_dropoff_datetime': 'TPEP_DROPOFF_DATETIME',
    'passenger_count': 'PASSENGER_COUNT',
    'trip_distance': 'TRIP_DISTANCE',
    'RatecodeID': 'RATECODEID',
    'store_and_fwd_flag': 'STORE_AND_FWD_FLAG',
    'PULocationID': 'PULOCATIONID',
    'DOLocationID': 'DOLOCATIONID',
    'payment_type': 'PAYMENT_TYPE',
    'fare_amount': 'FARE_AMOUNT',
    'extra': 'EXTRA',
    'mta_tax': 'MTA_TAX',
    'tip_amount': 'TIP_AMOUNT',
    'tolls_amount': 'TOLLS_AMOUNT',
    'improvement_surcharge': 'IMPROVEMENT_SURCHARGE',
    'total_amount': 'TOTAL_AMOUNT',
    'congestion_surcharge': 'CONGESTION_SURCHARGE',
    'Airport_fee': 'AIRPORT_FEE'
}

def main():
    parser = argparse.ArgumentParser(description="Ingest NYC Taxi Parquet data to Snowflake Bronze layer.")
    parser.add_argument("year", type=str, help="The year of the data (e.g., 2023)")
    parser.add_argument("month", type=str, help="The month of the data (e.g., 01)")
    args = parser.parse_args()


    # Define the URL and File
    filename = f"yellow_tripdata_{args.year}-{args.month}.parquet"
    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{args.year}-{args.month}.parquet"
    

    # define a data directory
    data_dir = "data/raw"
    # create the directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    # define the full path for saving the file
    file_path = os.path.join(data_dir, filename)

    logger.info(f"Starting ingestion for: {filename}")

    #Check for local file
    if os.path.exists(file_path):
        logger.info(f"{filename} already exists. Skipping download.")
    else:
        logger.info(f"Downloading {filename}...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1} out of {max_retries}")
                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    with open(file_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                logger.info("Download complete.")
                break
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    delay= 2 ** attempt
                    logger.warning(f"Failed! Retrying in {delay} seconds... Error: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"Failed to download. Error: {e}")
                    sys.exit(1)
    conn = None
    load_success = False

    try:
        logger.info("Connecting to Snowflake...")
        conn = sf.connect(
            user= SNOWFLAKE_USER,
            password= SNOWFLAKE_PASSWORD,
            account= SNOWFLAKE_ACCOUNT,
            database= SNOWFLAKE_DATABASE,
            schema= SNOWFLAKE_SCHEMA,
            warehouse= SNOWFLAKE_WAREHOUSE,
            role= SNOWFLAKE_ROLE
        )
        logger.info("Snowflake connection established!")
        
        logger.info(f"Setting session context... DB: {SNOWFLAKE_DATABASE}, SCHEMA: {SNOWFLAKE_SCHEMA}")

        # Read parquet file
        logger.info(f"Reading {file_path}...")
        parquet_file = pq.ParquetFile(file_path)

        total_rows = 0
        batch_size = 500000 # Process 500k rows at a time

        for batch in parquet_file.iter_batches(batch_size=batch_size):
            # convert arrow batch to dataframe
            batch_df = batch.to_pandas()
            # Rename columns to match Snowflake table schema
            batch_df = batch_df.rename(columns=COLUMN_NAME_MAPPING)

            # Add audit columns to batch dataframe
            batch_df["SOURCE_FILE"] = filename
            batch_df["LOADED_AT"] = datetime.now()

            # validate batch
            if batch_df.empty:
                logger.warning("Encountered empty batch, skipping...")
                continue 
            
            # Load batch to snowflake
            logger.info(f"Loading batch of {len(batch_df)} rows to Snowflake...")
            success, nchunks, nrow, _ = write_pandas(
                conn,
                batch_df,
                table_name= "RAW_TAXI_TRIPS",
                auto_create_table=False,
                overwrite=False
            )
            total_rows += nrow
            logger.info(f"Batch loaded. {nrow} rows (total:{total_rows})")

        logger.info(f"All batches loaded successfully to {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.RAW_TAXI_TRIPS. Total rows: {total_rows}")
        load_success = True
    except Exception as e:
        logger.exception(f"Snowflake operation failed!")
        load_success=False


    finally:
        if conn:
            conn.close()
            logger.info("Snowflake connection closed.")
        if load_success:
            logger.info(f"Ingestion completed successfully for {filename}.")
        else:
            logger.error(f"Ingestion failed for {filename}.")
            sys.exit(1)
        
    
    

if __name__ == "__main__":
    main()