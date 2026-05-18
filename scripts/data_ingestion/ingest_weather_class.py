# 1. Imports and Logging setup
import pandas as pd
from datetime import datetime
import logging
from scripts.data_ingestion.core.base_ingestor import BaseIngestor
import requests

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class WeatherIngestor(BaseIngestor):
    """ Ingestor for Hourly Weather data """
    def __init__(self,start_date,end_date):
        super().__init__(table_name="RAW_WEATHER_HOURLY",overwrite=True)
        self.start_date = start_date
        self.end_date = end_date
        self.source_url = "https://archive-api.open-meteo.com/v1/archive"
        self.actual_request_url = self.source_url #By default

    def extract(self) -> pd.DataFrame:
        params = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "hourly": "temperature_2m,precipitation,snowfall,windspeed_10m,weathercode",
            "timezone": "America/New_York"
        }
        logger.info(f"Fetching weather data from {self.start_date} to {self.end_date}")
        try:
            with requests.get(self.source_url,params=params) as response:
                response.raise_for_status()
                logger.info(f"Response status code: {response.status_code}")
                logger.info("Weather data fetched successfully")
                self.actual_request_url = response.url
                json_data = response.json()
                hourly_data = json_data.get('hourly')
                if not hourly_data:
                    logger.error("No 'hourly' data found in the Weather API")
                    return pd.DataFrame()
                return pd.DataFrame(hourly_data)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    def transform(self, df:pd.DataFrame)-> pd.DataFrame:
        logger.info("Transforming Hourly weather data...")
        # Audit columns
        df['SOURCE_URL'] = self.actual_request_url
        df['LOADED_AT'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Standardize column names to uppercase
        df.rename(columns=str.upper, inplace=True)
        return df
    
if __name__ == '__main__':
    weather_ingestor = WeatherIngestor(start_date="2023-01-01",end_date="2023-02-28")
    weather_ingestor.run()