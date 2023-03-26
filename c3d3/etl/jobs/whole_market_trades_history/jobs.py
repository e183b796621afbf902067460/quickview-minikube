from dagster import job
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_aws.s3.resources import s3_resource
import os

from etl.executors.celery.executor import celery_executor
from etl.assets.whole_market_trades_history.assets import get_overview
from etl.ops.whole_market_trades_history.ops import extract_from_c3vault, load_to_dwh
from etl.resources.c3vault.resource import c3vault
from etl.resources.logger.resource import logger
from etl.resources.dwh.resource import dwh
from etl.resources.fernet.resource import fernet
from etl.resources.serializers.resource import df_serializer
from etl.resources.w3sleep.resource import w3sleep


@job(
    name='whole_market_trades_history',
    resource_defs={
        'c3vault': c3vault,
        'dwh': dwh,
        'logger': logger,
        'fernet': fernet,
        'df_serializer': df_serializer,
        'w3sleep': w3sleep,
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
