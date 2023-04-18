from typing import List
import datetime
from dagster import asset, RetryRequested
import requests
import pandas as pd

from c3d3.infrastructure.c3.abstract.factory import C3AbstractFactory
from c3d3.infrastructure.c3.bridge.bridge import C3Bridge
from c3d3.infrastructure.c3.factories.cex_balance_screener.factory import CexBalanceScreenerFactory
from c3d3.infrastructure.c3.interfaces.cex_balance_screener.interface import iCexBalanceScreenerHandler

from etl.resources.w3sleepy.resource import W3Sleepy, MAX_RETRIES


@asset(
    name='df',
    required_resource_keys={
        'dwh',
        'logger',
        'fernet',
        'df_serializer'
    },
    retry_policy=W3Sleepy
)
def get_overview(context, configs: dict) -> List[list]:
    def _formatting(raw: pd.DataFrame) -> pd.DataFrame:
        raw.rename(
            columns={
                iCexBalanceScreenerHandler._EXCHANGE_COLUMN: 'h_exchange_name',
                iCexBalanceScreenerHandler._TICKER_COLUMN: 'h_ticker_name',
                iCexBalanceScreenerHandler._LABEL_COLUMN: 'h_label_name',
                iCexBalanceScreenerHandler._QTY_COLUMN: 'pit_qty',
                iCexBalanceScreenerHandler._CURRENT_PRICE_COLUMN: 'pit_price',
                iCexBalanceScreenerHandler._TS_COLUMN: 'pit_ts'
            },
            inplace=True
        )
        return raw

    route = C3Bridge(
        abstract_factory=C3AbstractFactory,
        factory_key=CexBalanceScreenerFactory.key,
        object_key=configs['exchange_name']
    ).init_object(
        api=context.resources.fernet.decrypt(configs['label_api_key'].encode()).decode(),
        secret=context.resources.fernet.decrypt(configs['label_secret_key'].encode()).decode(),
        ticker=configs['symbol_name'],
        label=configs['label_name']
    )
    try:
        overview = route.do()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as exc:
        raise RetryRequested(max_retries=MAX_RETRIES, seconds_to_wait=.5) from exc
    df = _formatting(raw=overview)
    return context.resources.df_serializer.df_to_list(df)

