import os
import argparse
import requests
import pandas as pd
import pyarrow.parquet as pq
from datetime import datetime
import logging
import time
from scripts.data_ingestion.core.base_ingestor import BaseIngestor
from scripts.data_ingestion.core.config import settings
from scripts.data_ingestion.core.database import SnowflakeClient
import sys



logging.basicConfig(
      level=logging.INFO,format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
          )
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Ingest NYC TLC yellow taxi parquet data.")
    parser.add_argument(
        "--year",
        default="2023",
        help="Four-digit taxi source year, for example 2023.",
    )
    parser.add_argument(
        "--month",
        default="02",
        help="One- or two-digit taxi source month, for example 2 or 02.",
    )
    return parser.parse_args()


def normalize_year_month(year, month):
    year = str(year)
    month = str(month).zfill(2)

    if not year.isdigit() or len(year) != 4:
        raise ValueError(f"Invalid taxi year: {year}")

    if not month.isdigit() or not 1 <= int(month) <= 12:
        raise ValueError(f"Invalid taxi month: {month}")

    return year, month

class TaxiIngestor(BaseIngestor):

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
    'airport_fee': 'AIRPORT_FEE'
    }

    def __init__(self, year, month):
        super().__init__(table_name="RAW_TAXI_TRIPS", overwrite=False)
        year, month = normalize_year_month(year, month)
        self.year = year
        self.month = month
        self.file_name = f"yellow_tripdata_{year}-{month}.parquet"
        self.source_url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month}.parquet"

        self.data_dir = os.path.join("data","raw")
        os.makedirs(self.data_dir, exist_ok=True)
        self.local_path = os.path.join(self.data_dir, self.file_name)
    
    def extract(self) -> str:
        """ Download the files and returns the local path """
        logger.info(f"Starting ingestion for {self.local_path}")
        #Check for local file
        if os.path.exists(self.local_path):
            logger.info(f"{self.file_name} already exists. Skipping download.")
        else:
            logger.info(f"Downloading {self.file_name}...")
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempt {attempt + 1} out of {max_retries}")
                    with requests.get(self.source_url, stream=True) as r:
                        r.raise_for_status()
                        with open(self.local_path, 'wb') as f:
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

        return self.local_path
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """ This is required by BaseIngestor parent class, but we use transform_batch here instead"""
        return df
    
    def transform_batch(self, batch_df: pd.DataFrame) -> pd.DataFrame:
        """ Transforms a single batch of data """
        batch_df = batch_df.rename(columns=self.COLUMN_NAME_MAPPING)
        
        # Defensive: force all columns to uppercase
        batch_df.columns = [c.upper() for c in batch_df.columns]

        # ELITE: Use ISO strings for maximum compatibility with Snowflake's TIMESTAMP_NTZ
        # This prevents internal serialization from converting dates back to Epoch numbers.
        batch_df['TPEP_PICKUP_DATETIME'] = batch_df['TPEP_PICKUP_DATETIME'].dt.strftime("%Y-%m-%d %H:%M:%S")
        batch_df['TPEP_DROPOFF_DATETIME'] = batch_df['TPEP_DROPOFF_DATETIME'].dt.strftime("%Y-%m-%d %H:%M:%S")

        batch_df["SOURCE_FILE"] = self.file_name
        batch_df["LOADED_AT"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return batch_df

    def get_existing_source_file_rows(self) -> int:
        """Return existing raw rows for this source file to avoid duplicate appends."""
        with SnowflakeClient() as db:
            return db.count_rows_by_value(
                table_name=self.table_name,
                column_name="SOURCE_FILE",
                value=self.file_name,
            )

    def should_load_source_file(self, expected_rows: int) -> bool:
        """Return False for fully loaded files and fail on partial loads."""
        existing_rows = self.get_existing_source_file_rows()

        if existing_rows == 0:
            logger.info(f"No existing rows found for {self.file_name}. Continuing ingestion.")
            return True

        if existing_rows == expected_rows:
            logger.info(
                f"{self.file_name} is already loaded with {existing_rows} rows. "
                "Skipping taxi ingestion to prevent duplicate raw data."
            )
            return False

        raise RuntimeError(
            f"Found {existing_rows} existing rows for {self.file_name}, "
            f"but the source file contains {expected_rows} rows. "
            "Refusing to append because the raw table may contain a partial load."
        )

    
    def run(self):
        """ Overwrite run to handle batch processing """
        try:
            path = self.extract()
            logger.info(f"Reading {path}...")
            parquet_file = pq.ParquetFile(path)
            expected_rows = parquet_file.metadata.num_rows

            if not self.should_load_source_file(expected_rows):
                return

            total_rows = 0
            batch_size = 500000 # Process 500k rows at a time
            for batch in parquet_file.iter_batches(batch_size=batch_size):
                # convert arrow batch to dataframe
                batch_df = batch.to_pandas()
                batch_df = self.transform_batch(batch_df)

                # validate batch
                if batch_df.empty:
                    logger.warning("Encountered empty batch, skipping...")
                    continue 

                # Load batch to snowflake
                logger.info(f"Loading batch of {len(batch_df)} rows to Snowflake...")
                rows_loaded = self.load(batch_df)
                total_rows += rows_loaded 
                logger.info(f"Batch loaded. {rows_loaded} rows (total:{total_rows})")
            logger.info(f"All batches loaded successfully to {settings.SNOWFLAKE_DATABASE}.{settings.SNOWFLAKE_SCHEMA}.RAW_TAXI_TRIPS. Total rows: {total_rows}")
        except Exception as e:
            logger.exception(f"Snowflake operation failed!")
            raise
        

if __name__ == '__main__':
    args = parse_args()
    ingestor = TaxiIngestor(year=args.year, month=args.month)
    ingestor.run()
