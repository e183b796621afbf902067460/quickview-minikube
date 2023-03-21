from dagster import job
from dagster_celery import celery_executor

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
        'w3sleep': w3sleep
    },
    config={
        "execution": {
            "config": {
                "multiprocess": {
                    "max_concurrent": 4,
                },
            }
        }
    },
    executor_def=celery_executor
)
def dag():
    configs = extract_from_d3vault()
    overviews = configs.map(get_overview)
    load_to_dwh(overviews.collect())


