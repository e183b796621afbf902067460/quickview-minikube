from dagster import _check as check
from dagster_celery import celery_executor
from dagster_celery.config import dict_wrapper, DEFAULT_CONFIG
import os


CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', None)
CELERYD_CONCURRENCY = os.getenv('CELERYD_CONCURRENCY', None)

if CELERY_BROKER_URL:
    celery_executor.broker = CELERY_BROKER_URL
if CELERYD_CONCURRENCY:
    DEFAULT_CONFIG.update(
        {
            'worker_concurrency': CELERYD_CONCURRENCY
        }
    )
    celery_executor.config_source = DEFAULT_CONFIG

