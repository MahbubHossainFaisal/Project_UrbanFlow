import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class Settings:
    def __init__(self):
        load_dotenv()

        # Required Snowflake credentials
        self.SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
        self.SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
        self.SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
        self.SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
        self.SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
        self.SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")
        self.SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE")

        # Trigger Validation
        self._validate_config()

    def _validate_config(self):
        # This validate function checks if any env variables are missing
        required_vars = [
        "SNOWFLAKE_USER",
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_PASSWORD",
        "SNOWFLAKE_WAREHOUSE",
        "SNOWFLAKE_DATABASE",
        "SNOWFLAKE_SCHEMA",
        "SNOWFLAKE_ROLE"]

        missing = [var for var in required_vars if not getattr(self,var)]
        """
        if not getattr(self, var)
        This checks if the value is:
        None or empty string or "" or False
        Because all are considered falsy in Python.
        """
        if missing:
            error_msg = f"Oops! Configuration Error: Missing environment variables: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.info("Great! Configuration validated successfully.")

# Singleton instance for easy import accross the framework
settings = Settings()