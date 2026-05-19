import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from .config import settings
import logging


logger = logging.getLogger(__name__)

class SnowflakeClient:
    """
    Snowflake client context management.
    Ensures connections are closed and provides high-performance bulk loading
    """
    def __init__(self):
        self.conn = None
    
    def __enter__(self):
        """ Establishes Connection """
        try:
            self.conn = snowflake.connector.connect( 
                user = settings.SNOWFLAKE_USER,
                account = settings.SNOWFLAKE_ACCOUNT,
                password = settings.SNOWFLAKE_PASSWORD,
                warehouse = settings.SNOWFLAKE_WAREHOUSE,
                database = settings.SNOWFLAKE_DATABASE,
                schema = settings.SNOWFLAKE_SCHEMA,
                role = settings.SNOWFLAKE_ROLE
            )
            logger.info("Successfully connected to Snowflake")
            return self
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Ensures connection is closed """
        if self.conn:
            self.conn.close()
            logger.info("Snowflake connection closed.")

    def write_dataframe(self, df, table_name, overwrite=False):
        """ High performance bulk write using write_pandas """
        if self.conn:
            success, nchunks, nrows, _ = write_pandas(
                conn = self.conn,
                df = df,
                table_name = table_name.upper(), # Snowflake convention
                database = settings.SNOWFLAKE_DATABASE,
                schema = settings.SNOWFLAKE_SCHEMA,
                overwrite=overwrite,
                auto_create_table=True
            )

            if success:
                logger.info(f"Successfully loaded {nrows} rows into {table_name}.")
                return nrows
            else:
                logger.error(f"Failed to load data into {table_name}")
                return 0