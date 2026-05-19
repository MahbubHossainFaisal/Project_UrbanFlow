from abc import ABC, abstractmethod
import pandas as pd
from .database import SnowflakeClient
import logging
import time


logger = logging.getLogger(__name__)

class BaseIngestor(ABC):
    """ Define the standard lifecycle of an ingestion job """
    def __init__(self, table_name, overwrite = False):
        self.table_name = table_name
        self.overwrite = overwrite
    
    @abstractmethod
    def extract(self) -> pd.DataFrame:
        """ Abstract method to extract data from source. """
        pass

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """ Abstract method to transform data. """
        pass

    def load(self, df: pd.DataFrame):
        """Standardized loading logic using SnowflakeClient"""
        logger.info(f"Starting load for table: {self.table_name}")
        with SnowflakeClient() as db:
            return db.write_dataframe(df,self.table_name,overwrite=self.overwrite)
        
    def run(self):
        """ Master lifecycle method. """
        start_time = time.time()
        logger.info(f"--- Starting Ingestion Job for {self.table_name} ---")

        try:
            # Extract
            df = self.extract()
            logger.info(f"Extracted {len(df)} rows.")

            # Transform
            df = self.transform(df)
            logger.info("Transformation complete.")

            # Load
            self.load(df)

            duration = round(time.time() - start_time, 2)
            logger.info(f"--- Job Finished Successfully in {duration} seconds ---")
        except Exception as e:
            logger.error(f"--- Job Failed for {self.table_name} ---")
            logger.error(f"Error: {e}")
            raise
