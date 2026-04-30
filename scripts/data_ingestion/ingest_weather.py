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
import time
import sys


# 2. Get API key and dates from ENV/CLI
load_dotenv()

SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")

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


# 4. connect to Snowflake (BRONZE SCHEMA)
# 5. Convert API JSON response to Pandas Dataframe
# 6. Add SOURCE_URL and LOADED_AT audit columns in the dataframe
# 7. Use write_pandas to load data to Snowflake 
# 8. Close the connection to Snowflake
# 9. Exit with success or failure code for Airflow


if __name__ == "__main__":

    test_start = "2023-01-01"
    test_end = "2023-01-02"

    try:
        data = fetch_weather_data(test_start,test_end)
        logger.info("Successfully fetched data!")

        logger.info(f"JSON keys: {data.keys()}")

        if 'hourly' in data:
            sample_times = data['hourly']['time'][:5]
            logger.info(f"Sampel timestamps: {sample_times}")
        else:
            logger.error("The key 'hourly' was not found in the response")

    except Exception as e:
        logger.error(f"Test failed: {e}")