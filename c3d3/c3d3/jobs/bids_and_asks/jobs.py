from dagster import job

from c3d3.assets.bids_and_asks.assets import get_overview
from c3d3.ops.bids_and_asks.ops import extract_from_d3vault, load_to_dwh
from c3d3.resources.d3vault.resource import d3vault
from c3d3.resources.logger.resource import logger
from c3d3.resources.dwh.resource import dwh
from c3d3.resources.fernet.resource import fernet
from c3d3.resources.serializers.resource import df_serializer
from c3d3.resources.w3sleep.resource import w3sleep


@job(
    name='bids_and_asks',
    resource_defs={
        'd3vault': d3vault,
        'dwh': dwh,
        'logger': logger,
        'fernet': fernet,
        'df_serializer': df_serializer,
        'w3sleep': w3sleep
    }
)
def dag():
    configs = extract_from_d3vault()
    overviews = configs.map(get_overview)
    load_to_dwh(overviews.collect())


if __name__ == "__main__":
    result = dag.execute_in_process()
    print(result)

