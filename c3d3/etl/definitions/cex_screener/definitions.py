from dagster import Definitions, AssetsDefinition
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_aws.s3.resources import s3_resource

from etl.executors.celery.executor import celery_executor
from etl.assets.cex_screener.assets import get_overview
from etl.ops.cex_screener.ops import extract_from_c3vault, load_to_dwh
from etl.jobs.cex_screener.jobs import dag
from etl.schedules.cex_screener.schedules import every_5th_minute
from etl.resources.c3vault.resource import c3vault
from etl.resources.logger.resource import logger
from etl.resources.dwh.resource import dwh
from etl.resources.fernet.resource import fernet
from etl.resources.serializers.resource import df_serializer


extract_from_c3vault = AssetsDefinition.from_op(extract_from_c3vault)
load_to_dwh = AssetsDefinition.from_op(load_to_dwh)


cex_screener = Definitions(
    assets=[extract_from_c3vault, get_overview, load_to_dwh],
    jobs=[dag],
    resources={
        'c3vault': c3vault,
        'dwh': dwh,
        'logger': logger,
        'fernet': fernet,
        'df_serializer': df_serializer,
        "io_manager": s3_pickle_io_manager,
        "s3": s3_resource
    },
    schedules=[every_5th_minute],
    executor=celery_executor
)
