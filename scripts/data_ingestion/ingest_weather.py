# 1. Imports and Logging setup
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

# 3. Request data from open-meteo api with retries

def fetch_weather_data(start_date, end_date):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,precipitation,snowfall,windspeed_10m,weathercode",
        "timezone": "America/New_York"
    }

    with requests.get(url,params=params) as response:
        response.raise_for_status()
        return response.json()
    
# 5. Convert API JSON response to Pandas Dataframe
def process_weather_data(json_data,source_url):
    hourly_data = json_data.get('hourly')
    if not hourly_data:
        logger.error("No 'hourly' data found in the API")
        return pd.DataFrame()


    df = pd.DataFrame(hourly_data)

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

        logger.info(f"Loading {len(df)} rows into RAW_WEATHER_HOURLY Table...")
        
        success, nchunks, nrows, _ = write_pandas(
            conn,
            df,
            table_name="RAW_WEATHER_HOURLY",
            auto_create_table=True,
            overwrite=False
        )
        if success:
            logger.info(f"Successfully loaded {nrows} rows")
    except Exception as e:
        logger.error(f"Snowflake data load failed: {e}")
        raise

    finally:
        if conn:
            conn.close()
            logger.info("Snowflake connection closed")



if __name__ == "__main__":

    test_start = "2023-01-01"
    test_end = "2023-02-28"

    try:
        # 1. Fetch data
        raw_json = fetch_weather_data(test_start,test_end)
        source_url = "https://archive-api.open-meteo.com/v1/archive"
        logger.info("Successfully fetched data!")

        # 2. Process data

        weather_df = process_weather_data(raw_json,source_url)

        # 3. Verify locally
        logger.info(f"DataFrame Shape: {weather_df.shape}")
        logger.info(f"Columns: {weather_df.columns.tolist()}")

        # 4. Load
        load_to_Snowflake(weather_df)

    except Exception as e:
        logger.error(f"Ingestion pipeline failed!: {e}")
        sys.exit(1)