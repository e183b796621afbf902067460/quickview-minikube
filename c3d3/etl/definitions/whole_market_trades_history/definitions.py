from dagster import Definitions, AssetsDefinition

from etl.assets.whole_market_trades_history.assets import get_overview
from etl.ops.whole_market_trades_history.ops import extract_from_c3vault, load_to_dwh
from etl.jobs.whole_market_trades_history.jobs import dag
from etl.schedules.whole_market_trades_history.schedules import every_5th_minute
from etl.resources.c3vault.resource import c3vault
from etl.resources.logger.resource import logger
from etl.resources.dwh.resource import dwh
from etl.resources.fernet.resource import fernet
from etl.resources.serializers.resource import df_serializer
from etl.resources.w3sleep.resource import w3sleep


extract_from_c3vault = AssetsDefinition.from_op(extract_from_c3vault)
load_to_dwh = AssetsDefinition.from_op(load_to_dwh)


whole_market_trades_history = Definitions(
    assets=[extract_from_c3vault, get_overview, load_to_dwh],
    jobs=[dag],
    resources={
        'c3vault': c3vault,
        'dwh': dwh,
        'logger': logger,
        'fernet': fernet,
        'df_serializer': df_serializer,
        'w3sleep': w3sleep
    },
    schedules=[every_5th_minute]
)
