from dagster import job
from dagster_celery import celery_executor

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
        'w3sleep': w3sleep
    },
    executor_def=celery_executor
)
def dag():
    configs = extract_from_c3vault()
    overviews = configs.map(get_overview)
    load_to_dwh(overviews.collect())
