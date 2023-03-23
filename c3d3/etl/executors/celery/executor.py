from dagster_celery import celery_executor
import os


CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', None)

if CELERY_BROKER_URL:
    celery_executor.broker = CELERY_BROKER_URL
