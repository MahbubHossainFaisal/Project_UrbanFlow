# 1. Imports and Logging setup
import argparse
import requests
import os
import pandas as pd
import pyarrow.parquet as pq
from datetime import datetime
import snowflake.connector as sf
from snowflake.connector.pandas_tools import write_pandas
from dotenv import load_dotenv
import logging
import sys

# 2. Get API key and dates from ENV/CLI
load_dotenv()

SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE")

# Setup Logging
logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


# 5. Convert API response to Pandas Dataframe
def process_zone_lookup_data(source_url):


    df = pd.read_csv(source_url)
    if df.empty:
        return df

    #Audit columns
    df['SOURCE_URL'] = source_url
    df['LOADED_AT'] = datetime.now()
    #Standardize column names that should be matched to Snowflake table.
    df.rename(columns=str.upper, inplace=True)
    return df

# 4. connect to Snowflake (BRONZE SCHEMA)
def load_to_Snowflake(df):
    if df.empty:
        logger.warning("DataFrame is empty! Skipping Snowflake Load.")
        return

    conn = None
    try:
        logger.info("Connecting to Snowflake...")
        conn = sf.connect(
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PASSWORD,
            account=SNOWFLAKE_ACCOUNT,
            warehouse=SNOWFLAKE_WAREHOUSE,
            database=SNOWFLAKE_DATABASE,
            schema=SNOWFLAKE_SCHEMA,
            role=SNOWFLAKE_ROLE
        )

        logger.info(f"Loading {len(df)} rows into RAW_ZONE_LOOKUP Table...")
        
        success, nchunks, nrows, _ = write_pandas(
            conn,
            df,
            table_name="RAW_TAXI_ZONE_LOOKUP",
            auto_create_table=True,
            overwrite=True
        )
        if success:
            logger.info(f"Successfully loaded {nrows} rows")
    except Exception as e:
        logger.exception(f"Snowflake data load failed")
        raise

    finally:
        if conn:
            conn.close()
            logger.info("Snowflake connection closed")


if __name__ == "__main__":
    
    try:
        # 1. Fetch and Process data
        source_url = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

        zone_lookup_df = process_zone_lookup_data(source_url)

        # 3. Verify locally
        logger.info(f"DataFrame Shape: {zone_lookup_df.shape}")
        logger.info(f"Columns: {zone_lookup_df.columns.tolist()}")

        # 4. Load
        load_to_Snowflake(zone_lookup_df)

    except Exception as e:
        logger.error(f"Ingestion pipeline failed!: {e}")
        sys.exit(1)