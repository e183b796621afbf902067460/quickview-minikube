from typing import List
from dagster import asset, RetryRequested
import pandas as pd

from c3d3.domain.d3.adhoc.nodes.http.adhoc import HTTPNode
from c3d3.infrastructure.d3.abstract.factory import D3AbstractFactory
from c3d3.infrastructure.d3.bridge.bridge import D3Bridge
from c3d3.infrastructure.d3.factories.dex_borrow_screener.factory import DexBorrowScreenerFactory
from c3d3.infrastructure.d3.interfaces.dex_borrow_screener.interface import iDexBorrowScreenerHandler

from etl.resources.w3sleepy.resource import W3Sleepy, MAX_RETRIES


@asset(
    name='df',
    required_resource_keys={
        'logger',
        'fernet',
        'df_serializer'
    }
)
def get_overview(context, configs: dict) -> List[list]:
    def _formatting(raw: pd.DataFrame) -> pd.DataFrame:
        raw.rename(
            columns={
                iDexBorrowScreenerHandler._WALLET_ADDRESS_COLUMN: 'h_wallet_address',
                iDexBorrowScreenerHandler._LABEL_COLUMN: 'h_label_name',
                iDexBorrowScreenerHandler._PROTOCOL_NAME_COLUMN: 'h_protocol_name',
                iDexBorrowScreenerHandler._TOKEN_ADDRESS_COLUMN: 'h_token_address',
                iDexBorrowScreenerHandler._CHAIN_NAME_COLUMN: 'h_network_name',
                iDexBorrowScreenerHandler._SYMBOL_COLUMN: 'pit_symbol',
                iDexBorrowScreenerHandler._CURRENT_PRICE_COLUMN: 'pit_price',
                iDexBorrowScreenerHandler._QTY_COLUMN: 'pit_qty',
                iDexBorrowScreenerHandler._HEALTH_FACTOR_COLUMN: 'pit_health_factor',
                iDexBorrowScreenerHandler._TS_COLUMN: 'pit_ts'
            },
            inplace=True
        )
        return df

    node = HTTPNode(uri=context.resources.fernet.decrypt(configs['network_rpc_node'].encode()).decode())
    handler = D3Bridge(
        abstract_factory=D3AbstractFactory,
        factory_key=DexBorrowScreenerFactory.key,
        object_key=configs['protocol_name']
    ).init_object(
        address=configs['token_address'],
        wallet_address=configs['wallet_address'],
        node=node,
        label=configs['label_name'],
        chain=configs['network_name']
    )
    try:
        overview = handler.do()
    except ValueError as exc:
        raise RetryRequested(max_retries=MAX_RETRIES, seconds_to_wait=.5) from exc

    df = _formatting(raw=overview)
    return context.resources.df_serializer.df_to_list(df)
