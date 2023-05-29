from dagster import job, MAX_RUNTIME_SECONDS_TAG
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_aws.s3.resources import s3_resource
import os

from etl.executors.celery.executor import celery_executor
from etl.ops._analytics_adj.ops import _get_c3d3, _etl
from etl.resources.logger.resource import logger
from etl.resources.dwh.resource import dwh
from etl.resources.serializers.resource import df_serializer


@job(
    name='_analytics_adj',
    resource_defs={
        'dwh': dwh,
        'logger': logger,
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
    },
    tags={
        MAX_RUNTIME_SECONDS_TAG: 60 * 60
    }
)
def dag():
    configs = _get_c3d3()
    configs.map(_etl)
