from celery import shared_task
from datetime import datetime
import logging
# Get an instance of a logger
logger = logging.getLogger('django')


@shared_task
def auto_save_redis_to_database():
    logger.info("HITTTT")
