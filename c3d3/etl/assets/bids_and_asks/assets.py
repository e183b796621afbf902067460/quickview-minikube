import datetime
from typing import List
from dagster import asset
import pandas as pd

from c3d3.domain.d3.adhoc.nodes.http.adhoc import HTTPNode
from c3d3.infrastructure.d3.abstract.factory import D3AbstractFactory
from c3d3.infrastructure.d3.factories.dex_screener.factory import DexScreenerFactory
from c3d3.infrastructure.d3.bridge.bridge import D3Bridge
from c3d3.infrastructure.d3.interfaces.dex_screener.interface import iDexScreenerHandler


@asset(
    name='df',
    required_resource_keys={
        'dwh',
        'logger',
        'fernet',
        'df_serializer',
        'w3sleep'
    },
    description='get_overview() for bids_and_asks',
    op_tags={
        'dagster-celery/queue': 'dagster'
    }
)
def get_overview(context, configs: dict) -> List[list]:
    def _formatting(raw: pd.DataFrame) -> pd.DataFrame:
        raw.rename(
            columns={
                iDexScreenerHandler._POOL_ADDRESS_COLUMN: 'h_pool_address',
                iDexScreenerHandler._CHAIN_NAME_COLUMN: 'h_network_name',
                iDexScreenerHandler._PROTOCOL_NAME_COLUMN: 'h_protocol_name',
                iDexScreenerHandler._POOL_SYMBOL_COLUMN: 'pit_symbol',
                iDexScreenerHandler._TRADE_PRICE_COLUMN: 'pit_price',
                iDexScreenerHandler._SENDER_COLUMN: 'pit_sender',
                iDexScreenerHandler._RECIPIENT_COLUMN: 'pit_recipient',
                iDexScreenerHandler._AMOUNT0_COLUMN: 'pit_amount0',
                iDexScreenerHandler._AMOUNT1_COLUMN: 'pit_amount1',
                iDexScreenerHandler._DECIMALS0_COLUMN: 'pit_decimals0',
                iDexScreenerHandler._DECIMALS1_COLUMN: 'pit_decimals1',
                iDexScreenerHandler._RESERVE0_COLUMN: 'pit_reserve0',
                iDexScreenerHandler._RESERVE1_COLUMN: 'pit_reserve1',
                iDexScreenerHandler._SQRT_P_COLUMN: 'pit_sqrt_p',
                iDexScreenerHandler._LIQUIDITY_COLUMN: 'pit_liquidity',
                iDexScreenerHandler._TRADE_FEE_COLUMN: 'pit_fee',
                iDexScreenerHandler._GAS_USED_COLUMN: 'pit_gas_used',
                iDexScreenerHandler._EFFECTIVE_GAS_PRICE_COLUMN: 'pit_effective_gas_price',
                iDexScreenerHandler._GAS_SYMBOL_COLUMN: 'pit_gas_symbol',
                iDexScreenerHandler._GAS_USD_PRICE_COLUMN: 'pit_gas_usd_price',
                iDexScreenerHandler._INDEX_POSITION_IN_THE_BLOCK_COLUMN: 'pit_index_position_in_the_block',
                iDexScreenerHandler._TX_HASH_COLUMN: 'pit_tx_hash',
                iDexScreenerHandler._TS_COLUMN: 'pit_ts'
            },
            inplace=True
        )
        return raw
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
    if now - previous > datetime.timedelta(hours=1):
        now = previous + datetime.timedelta(minutes=10)
    context.resources.logger.info(f"Current timestamp: from {previous} to {now}")
    while True:
        try:
            node = HTTPNode(uri=context.resources.fernet.decrypt(configs['network_rpc_node'].encode()).decode())
            route = D3Bridge(
                abstract_factory=D3AbstractFactory,
                factory_key=DexScreenerFactory.key,
                object_key=configs['protocol_name']
            ).init_object(
                start_time=previous,
                end_time=now,
                api_key=context.resources.fernet.decrypt(configs['network_api_key'].encode()).decode(),
                chain=configs['network_name'],
                is_reverse=configs['is_reverse'],
                address=configs['pool_address'],
                node=node
            )
            overview = route.do()
        except ValueError:
            context.resources.w3sleep.sleep()
        else:
            break
    df = _formatting(raw=overview)
    return context.resources.df_serializer.df_to_list(df)

