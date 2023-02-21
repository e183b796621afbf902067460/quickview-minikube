from typing import List
from datetime import datetime

from dagster import op, DynamicOut, DynamicOutput
import pandas as pd


@op(
    name='configs',
    required_resource_keys={
        'c3vault',
        'logger'
    },
    tags={
        'fabric': 'whole_market_trades_history'
    },
    out=DynamicOut(dict)
)
def extract_from_c3vault(context) -> List[dict]:
    query = '''
        SELECT
            h_tickers.h_ticker_name,
            h_exchanges.h_exchange_name
        FROM
            l_exchanges_tickers
        LEFT JOIN
            h_tickers USING(h_ticker_id)
        LEFT JOIN
            h_exchanges USING(h_exchange_id)
        ORDER BY
            h_exchanges.h_exchange_name
    '''
    context.resources.logger.info(f"{query}")

    samples = context.resources.c3vault.read(query=query)
    for sample in samples:
        ticker_name, exchange_name = sample[0], sample[1]
        yield DynamicOutput(
            {
                'ticker_name': ticker_name,
                'exchange_name': exchange_name
            },
            mapping_key=f'subtask_for_{ticker_name}_{exchange_name}'
        )


@op(
    name='load_to_dwh',
    required_resource_keys={
        'dwh',
        'logger',
        'df_serializer'
    },
    tags={
        'fabric': 'whole_market_trades_history'
    }
)
def load_to_dwh(context, df: List[list]) -> None:
    concat_df = pd.DataFrame()
    for mini_df in df:
        mini_df = context.resources.df_serializer.df_from_list(mini_df)
        concat_df = concat_df.append(mini_df, ignore_index=True)
        context.resources.logger.info(mini_df.head())
    context.resources.dwh.get_client().insert_df(
        table='pit_big_table_whole_market_trades_history',
        df=concat_df
    )
