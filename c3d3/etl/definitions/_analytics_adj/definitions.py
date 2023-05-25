from dagster import Definitions, AssetsDefinition
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_aws.s3.resources import s3_resource

from etl.executors.celery.executor import celery_executor
from etl.ops._analytics_adj.ops import _etl, _get_c3d3
from etl.jobs._analytics_adj.jobs import dag
from etl.schedules._analytics_adj.schedules import every_15th_minute
from etl.resources.logger.resource import logger
from etl.resources.dwh.resource import dwh
from etl.resources.serializers.resource import df_serializer


_etl = AssetsDefinition.from_op(_etl)
_get_c3d3 = AssetsDefinition.from_op(_get_c3d3)


_analytics_adj = Definitions(
    assets=[_etl, _get_c3d3],
    jobs=[dag],
    resources={
        'dwh': dwh,
        'logger': logger,
        'df_serializer': df_serializer,
        "io_manager": s3_pickle_io_manager,
        "s3": s3_resource
    },
    schedules=[every_15th_minute],
    executor=celery_executor
)
