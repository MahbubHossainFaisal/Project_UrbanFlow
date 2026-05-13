import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
print("1. About to import...")
from core.config import settings
print("2. Import successful!")
print(f"3. Data DB is: {settings.SNOWFLAKE_DATABASE}")