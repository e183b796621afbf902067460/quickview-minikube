from dagster import job
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_aws.s3.resources import s3_resource
import os

from etl.executors.celery.executor import celery_executor
from etl.assets.cex_open_order_screener.assets import get_overview
from etl.ops.cex_open_order_screener.ops import extract_from_c3vault, load_to_dwh
from etl.resources.c3vault_exposure.resource import c3vault_exposure
from etl.resources.logger.resource import logger
from etl.resources.dwh.resource import dwh
from etl.resources.fernet.resource import fernet
from etl.resources.serializers.resource import df_serializer


@job(
    name='cex_open_order_screener',
    resource_defs={
        'c3vault_exposure': c3vault_exposure,
        'dwh': dwh,
        'logger': logger,
        'fernet': fernet,
        'df_serializer': df_serializer,
        "io_manager": s3_pickle_io_manager,
        "s3": s3_resource
    },
    executor_def=celery_executor,
    config={
        'resources': {
            'io_manager': {
                'config': {
                    's3_bucket': os.getenv('S3_BUCKET', None)
                }
            },
            's3': {
                'config': {
                    'endpoint_url': os.getenv('S3_BACKEND_URL', None)
                }
            }
        }
    }
)
def dag():
    configs = extract_from_c3vault()
    overviews = configs.map(get_overview)
    load_to_dwh(overviews.collect())