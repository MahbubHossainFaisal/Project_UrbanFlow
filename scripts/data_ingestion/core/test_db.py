from .database import SnowflakeClient
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_connection():
    logger.info("Starting Database Engine Test....")
    try:
        with SnowflakeClient() as db:
            cursor = db.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM RAW_TAXI_TRIPS")
            count = cursor.fetchone()[0]
            logger.info(f"Current Row Count in RAW_TAXI_TRIPS: {count}")
        logger.info("Test finished! Connection should be closed now.")
    except Exception as e:
        logger.error(f"Test Failed: {e}")


if __name__ == "__main__":
    test_connection()