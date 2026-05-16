# 1. Imports and Logging setup
import pandas as pd
from datetime import datetime
import logging
from scripts.data_ingestion.core.base_ingestor import BaseIngestor


# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class ZoneLookupIngestor(BaseIngestor):
    """ Ingestor for Taxi Lookup Data """
    def __init__(self):
        super().__init__(table_name="RAW_TAXI_ZONE_LOOKUP",overwrite=True)
        self.source_url =  "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
    
    def extract(self) -> pd.DataFrame:
        logger.info(f"Extracting CSV from {self.source_url}")
        return pd.read_csv(self.source_url)
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Transforming Zone lookup data...")
        # Audit columns
        df['SOURCE_URL'] = self.source_url
        df['LOADED_AT'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Standardize column names to uppercase
        df.rename(columns=str.upper, inplace=True)
        return df

if __name__ == '__main__':
    ingestor = ZoneLookupIngestor()
    ingestor.run()