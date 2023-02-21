import datetime
from typing import List
from dagster import asset
import pandas as pd

from raffaelo.providers.http.provider import HTTPProvider
from d3tl.abstract.fabric import d3Abstract
from d3tl.bridge.configurator import D3BridgeConfigurator
from trad3r.root.composite.trader import rootTrad3r


@asset(
    name='df',
    required_resource_keys={
        'dwh',
        'logger',
        'fernet',
        'df_serializer',
        'w3sleep'
    },
    description='get_overview() for bids_and_asks'
)
def get_overview(context, configs: dict) -> List[list]:
    def _formatting(samples: List[dict], cfg: dict) -> pd.DataFrame:
        for sample in samples: sample.update(
            {
                'pool_address': cfg['pool_address'],
                'network_name': cfg['network_name'],
                'protocol_name': cfg['protocol_name']
            }
        )
        context.resources.logger.info(f"Current overview: {samples}")
        df = pd.DataFrame(samples)
        df.rename(
            columns={
                'pool_address': 'h_pool_address',
                'network_name': 'h_network_name',
                'native_chain_token': 'h_native_chain_token',
                'protocol_name': 'h_protocol_name',
                'symbol': 'pit_symbol',
                'bid': 'pit_bid',
                'ask': 'pit_ask',
                'price': 'pit_price',
                'sender': 'pit_sender',
                'amount0': 'pit_amount0',
                'amount1': 'pit_amount1',
                'gas_used': 'pit_gas_used',
                'effective_gas_price': 'pit_effective_gas_price',
                'gas_symbol': 'pit_gas_symbol',
                'gas_price': 'pit_gas_price',
                'index_position_in_the_block': 'pit_index_position_in_the_block',
                'tx_hash': 'pit_tx_hash',
                'time': 'pit_ts'
            },
            inplace=True
        )
        return df
    now = datetime.datetime.utcnow()
    previous = context.resources.dwh.get_client().query(
        f'''
        SELECT 
            MAX(pit_ts) 
        FROM 
            pit_big_table_bids_and_asks 
        WHERE 
            h_pool_address = '{configs['pool_address']}' AND
            h_protocol_name = '{configs['protocol_name']}' AND
            h_network_name = '{configs['network_name']}'
    ''').result_rows[0][0]
    previous = previous if previous.strftime('%Y') != '1970' or not previous else now - datetime.timedelta(minutes=5)
    context.resources.logger.info(f"Current previous timestamp: {previous}")
    while True:
        try:
            provider = HTTPProvider(uri=context.resources.fernet.decrypt(configs['network_rpc_node'].encode()).decode())
            class_ = D3BridgeConfigurator(
                abstract=d3Abstract,
                fabric_name='bids_and_asks',
                handler_name=configs['protocol_name']
            ).produce_handler()
            handler = class_(
                address=configs['pool_address'],
                provider=provider,
                uri=configs['network_uri'],
                api_key=context.resources.fernet.decrypt(configs['network_api_key'].encode()).decode(),
                block_limit=configs['network_block_limit'],
                gas_symbol=configs['native_chain_token'],
                trader=rootTrad3r
            )
            overview: List[dict] = handler.get_overview(
                start=previous,
                end=now,
                is_reverse=False
            )
        except ValueError:
            context.resources.w3sleep.sleep()
        else:
            break
    df = _formatting(samples=overview, cfg=configs)
    return context.resources.df_serializer.df_to_list(df)

