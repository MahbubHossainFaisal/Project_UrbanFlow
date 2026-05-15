from .database import SnowflakeClient
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_connection():
    logger.info("Starting Database Engine Test....")
    try:
        with SnowflakeClient() as db:
            cursor = db.conn.cursor()
            cursor.execute("SELECT CURRENT_VERSION(), CURRENT_WAREHOUSE(), CURRENT_DATABASE()")
            version, wh, db_name = cursor.fetchone()
            logger.info(f"Connected! Version: {version} | WH: {wh} | DB: {db_name}")
        logger.info("Test finished! Connection should be closed now.")
    except Exception as e:
        logger.error(f"Test Failed: {e}")


if __name__ == "__main__":
    test_connection()