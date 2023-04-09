from typing import List
import datetime
from dagster import asset, RetryRequested
import requests
import pandas as pd

from c3d3.infrastructure.c3.abstract.factory import C3AbstractFactory
from c3d3.infrastructure.c3.bridge.bridge import C3Bridge
from c3d3.infrastructure.c3.factories.cex_screener.factory import CexScreenerFactory
from c3d3.infrastructure.c3.interfaces.cex_screener.interface import iCexScreenerHandler

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
                iCexScreenerHandler._EXCHANGE_COLUMN: 'h_exchange_name',
                iCexScreenerHandler._TICKER_COLUMN: 'h_ticker_name',
                iCexScreenerHandler._QTY_COLUMN: 'pit_qty',
                iCexScreenerHandler._PRICE_COLUMN: 'pit_price',
                iCexScreenerHandler._TS_COLUMN: 'pit_ts',
                iCexScreenerHandler._SIDE_COLUMN: 'pit_side',
                iCexScreenerHandler._TRADE_FEE_COLUMN: 'pit_fee'
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
                pit_big_table_whole_market_trades_history
            WHERE 
                h_exchange_name = '{configs['exchange_name']}' AND
                h_ticker_name = '{configs['ticker_name']}'
        ''').result_rows[0][0]
    previous = previous if previous.strftime('%Y') != '1970' or not previous else now - datetime.timedelta(minutes=5)
    if now - previous > datetime.timedelta(hours=1):
        now = previous + datetime.timedelta(minutes=10)

    context.resources.logger.info(f"Current timestamp: from {previous} to {now}")

    route = C3Bridge(
        abstract_factory=C3AbstractFactory,
        factory_key=CexScreenerFactory.key,
        object_key=configs['exchange_name']
    ).init_object(
        ticker=configs['ticker_name'],
        start_time=previous,
        end_time=now
    )
    try:
        overview = route.do()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as exc:
        raise RetryRequested(max_retries=MAX_RETRIES, seconds_to_wait=.5) from exc
    df = _formatting(raw=overview)
    return context.resources.df_serializer.df_to_list(df)

