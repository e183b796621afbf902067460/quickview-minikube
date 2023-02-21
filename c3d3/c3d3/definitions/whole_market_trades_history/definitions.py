from dagster import Definitions, AssetsDefinition

from c3d3.assets.whole_market_trades_history.assets import get_overview
from c3d3.ops.whole_market_trades_history.ops import extract_from_c3vault, load_to_dwh
from c3d3.jobs.whole_market_trades_history.jobs import dag
from c3d3.schedules.whole_market_trades_history.schedules import every_10th_minute
from c3d3.resources.c3vault.resource import c3vault
from c3d3.resources.logger.resource import logger
from c3d3.resources.dwh.resource import dwh
from c3d3.resources.fernet.resource import fernet
from c3d3.resources.serializers.resource import df_serializer
from c3d3.resources.w3sleep.resource import w3sleep


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
    schedules=[every_10th_minute]
)
