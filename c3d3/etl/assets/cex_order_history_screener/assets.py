from typing import List
import datetime
from dagster import asset, RetryRequested
import requests
import pandas as pd

from c3d3.infrastructure.c3.abstract.factory import C3AbstractFactory
from c3d3.infrastructure.c3.bridge.bridge import C3Bridge
from c3d3.infrastructure.c3.factories.cex_order_history_screener.factory import CexOrderHistoryScreenerFactory
from c3d3.infrastructure.c3.interfaces.cex_order_history_screener.interface import iCexOrderHistoryScreenerHandler

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
                iCexOrderHistoryScreenerHandler._EXCHANGE_COLUMN: 'h_exchange_name',
                iCexOrderHistoryScreenerHandler._LABEL_COLUMN: 'h_label_name',
                iCexOrderHistoryScreenerHandler._TICKER_COLUMN: 'h_ticker_name',
                iCexOrderHistoryScreenerHandler._MARKET_PRICE_COLUMN: 'pit_market_price',
                iCexOrderHistoryScreenerHandler._LIMIT_PRICE_COLUMN: 'pit_limit_price',
                iCexOrderHistoryScreenerHandler._QTY_COLUMN: 'pit_qty',
                iCexOrderHistoryScreenerHandler._ORDER_ID_COLUMN: 'pit_order_id',
                iCexOrderHistoryScreenerHandler._SIDE_COLUMN: 'pit_side',
                iCexOrderHistoryScreenerHandler._STATUS_COLUMN: 'pit_status',
                iCexOrderHistoryScreenerHandler._TYPE_COLUMN: 'pit_type',
                iCexOrderHistoryScreenerHandler._TS_UPDATE_COLUMN: 'pit_update_ts',
                iCexOrderHistoryScreenerHandler._TS_COLUMN: 'pit_ts'
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
                pit_big_table_all_orders
            WHERE 
                h_exchange_name = '{configs['exchange_name']}' AND
                h_ticker_name = '{configs['ticker_name']}' AND
                h_label_name = '{configs['label_name']}'
        ''').result_rows[0][0]
    previous = previous if previous.strftime('%Y') != '1970' or not previous else now - datetime.timedelta(days=7)
    if now - previous > datetime.timedelta(hours=1):
        now = previous + datetime.timedelta(minutes=30)

    context.resources.logger.info(f"Current timestamp: from {previous} to {now}")

    route = C3Bridge(
        abstract_factory=C3AbstractFactory,
        factory_key=CexOrderHistoryScreenerFactory.key,
        object_key=configs['exchange_name']
    ).init_object(
        api=context.resources.fernet.decrypt(configs['label_api_key'].encode()).decode(),
        secret=context.resources.fernet.decrypt(configs['label_secret_key'].encode()).decode(),
        ticker=configs['ticker_name'],
        label=configs['label_name'],
        start_time=previous,
        end_time=now
    )
    try:
        overview = route.do()
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as exc:
        raise RetryRequested(max_retries=MAX_RETRIES, seconds_to_wait=.5) from exc

    df = _formatting(raw=overview)
    return context.resources.df_serializer.df_to_list(df)

