from dagster import job
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_aws.s3.resources import s3_resource

from etl.executors.celery.executor import celery_executor
from etl.assets.bids_and_asks.assets import get_overview
from etl.ops.bids_and_asks.ops import extract_from_d3vault, load_to_dwh
from etl.resources.d3vault.resource import d3vault
from etl.resources.logger.resource import logger
from etl.resources.dwh.resource import dwh
from etl.resources.fernet.resource import fernet
from etl.resources.serializers.resource import df_serializer
from etl.resources.w3sleep.resource import w3sleep


@job(
    name='bids_and_asks',
    resource_defs={
        'd3vault': d3vault,
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
                    's3_bucket': 'dagster-compute-logs',
                    's3_prefix': 'dagster-compute-logs'
                }
            }
        }
    }
)
def dag():
    configs = extract_from_d3vault()
    overviews = configs.map(get_overview)
    load_to_dwh(overviews.collect())


