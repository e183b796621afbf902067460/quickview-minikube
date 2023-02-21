from typing import List
import datetime
import requests
from dagster import asset
import pandas as pd

from c3tl.abstract.fabric import c3Abstract
from c3tl.bridge.configurator import C3BridgeConfigurator
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
    description='get_overview() for whole_market_trades_history'
)
def get_overview(context, configs: dict) -> List[list]:
    def _formatting(samples: List[dict], cfg: dict) -> pd.DataFrame:
        for sample in samples: sample.update(
            {
                'exchange_name': cfg['exchange_name'],
                'ticker_name': cfg['ticker_name'],
            }
        )
        context.resources.logger.info(f"Current overview: {samples}")
        df = pd.DataFrame(samples)
        df.rename(
            columns={
                'exchange_name': 'h_exchange_name',
                'ticker_name': 'h_ticker_name',
                'qty': 'pit_qty',
                'price': 'pit_price',
                'ts': 'pit_ts',
                'side': 'pit_side'
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
                pit_big_table_whole_market_trades_history
            WHERE 
                h_exchange_name = '{configs['exchange_name']}' AND
                h_ticker_name = '{configs['ticker_name']}'
        ''').result_rows[0][0]
    previous = previous if previous.strftime('%Y') != '1970' or not previous else now - datetime.timedelta(minutes=5)
    context.resources.logger.info(f"Current previous timestamp: {previous}")
    while True:
        try:
            class_ = C3BridgeConfigurator(
                abstract=c3Abstract,
                fabric_name='whole_market_trades_history',
                handler_name=configs['exchange_name']
            ).produce_handler()
            handler = class_()
            overview: List[dict] = handler.get_overview(
                start=previous,
                end=now,
                ticker=configs['ticker_name']
            )
        except requests.exceptions.ConnectionError:
            context.resources.w3sleep.sleep()
        else:
            break
    df = _formatting(samples=overview, cfg=configs)
    return context.resources.df_serializer.df_to_list(df)

