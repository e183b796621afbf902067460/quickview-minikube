from dagster import Definitions, AssetsDefinition
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_aws.s3.resources import s3_resource

from etl.executors.celery.executor import celery_executor
from etl.assets.dex_borrow_screener.assets import get_overview
from etl.ops.dex_borrow_screener.ops import extract_from_d3vault, load_to_dwh
from etl.jobs.dex_borrow_screener.jobs import dag
from etl.schedules.dex_borrow_screener.schedules import every_1th_minute
from etl.resources.d3vault_exposure.resource import d3vault_exposure
from etl.resources.logger.resource import logger
from etl.resources.dwh.resource import dwh
from etl.resources.fernet.resource import fernet
from etl.resources.serializers.resource import df_serializer


extract_from_d3vault = AssetsDefinition.from_op(extract_from_d3vault)
load_to_dwh = AssetsDefinition.from_op(load_to_dwh)


dex_borrow_screener = Definitions(
    assets=[extract_from_d3vault, get_overview, load_to_dwh],
    jobs=[dag],
    resources={
        'd3vault_exposure': d3vault_exposure,
        'dwh': dwh,
        'logger': logger,
        'fernet': fernet,
        'df_serializer': df_serializer,
        "io_manager": s3_pickle_io_manager,
        "s3": s3_resource
    },
    schedules=[every_1th_minute],
    executor=celery_executor
)
