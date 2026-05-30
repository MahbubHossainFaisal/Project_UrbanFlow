import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from .config import settings
import logging
import re


logger = logging.getLogger(__name__)
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

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

    @staticmethod
    def _validate_identifier(identifier):
        if not IDENTIFIER_PATTERN.match(identifier):
            raise ValueError(f"Invalid Snowflake identifier: {identifier}")
        return identifier.upper()

    def _qualified_table_name(self, table_name):
        database = self._validate_identifier(settings.SNOWFLAKE_DATABASE)
        schema = self._validate_identifier(settings.SNOWFLAKE_SCHEMA)
        table = self._validate_identifier(table_name)
        return f"{database}.{schema}.{table}"

    def table_exists(self, table_name):
        """Return True when a table exists in the configured Snowflake schema."""
        table = self._validate_identifier(table_name)
        query = """
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_CATALOG = %s
              AND TABLE_SCHEMA = %s
              AND TABLE_NAME = %s
        """
        with self.conn.cursor() as cursor:
            cursor.execute(
                query,
                (
                    settings.SNOWFLAKE_DATABASE.upper(),
                    settings.SNOWFLAKE_SCHEMA.upper(),
                    table,
                ),
            )
            return cursor.fetchone()[0] > 0

    def count_rows_by_value(self, table_name, column_name, value):
        """Count rows in a table where a column matches a specific value."""
        if not self.table_exists(table_name):
            return 0

        qualified_table = self._qualified_table_name(table_name)
        column = self._validate_identifier(column_name)
        query = f"SELECT COUNT(*) FROM {qualified_table} WHERE {column} = %s"

        with self.conn.cursor() as cursor:
            cursor.execute(query, (value,))
            return int(cursor.fetchone()[0])

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
