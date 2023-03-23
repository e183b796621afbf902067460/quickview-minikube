from dagster import Definitions, AssetsDefinition

from etl.executors.celery.executor import celery_executor
from etl.assets.bids_and_asks.assets import get_overview
from etl.ops.bids_and_asks.ops import extract_from_d3vault, load_to_dwh
from etl.jobs.bids_and_asks.jobs import dag
from etl.schedules.bids_and_asks.schedules import every_5th_minute
from etl.resources.d3vault.resource import d3vault
from etl.resources.logger.resource import logger
from etl.resources.dwh.resource import dwh
from etl.resources.fernet.resource import fernet
from etl.resources.serializers.resource import df_serializer
from etl.resources.w3sleep.resource import w3sleep


extract_from_d3vault = AssetsDefinition.from_op(extract_from_d3vault)
load_to_dwh = AssetsDefinition.from_op(load_to_dwh)


bids_and_asks = Definitions(
    assets=[extract_from_d3vault, get_overview, load_to_dwh],
    jobs=[dag],
    resources={
        'd3vault': d3vault,
        'dwh': dwh,
        'logger': logger,
        'fernet': fernet,
        'df_serializer': df_serializer,
        'w3sleep': w3sleep
    },
    schedules=[every_5th_minute],
    executor=celery_executor
)
