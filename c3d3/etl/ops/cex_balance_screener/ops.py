from typing import List
from datetime import datetime

import pandas as pd
from dagster import op, DynamicOut, DynamicOutput


@op(
    name='configs',
    required_resource_keys={
        'c3vault_exposure',
        'logger'
    },
    out=DynamicOut(dict)
)
def extract_from_c3vault(context) -> List[dict]:
    query = '''
        SELECT
            h_labels.h_label_name,
            h_labels.h_label_api_key,
            h_labels.h_label_secret_key,
            h_symbols.h_symbol_name,
            h_exchanges.h_exchange_name
        FROM
            l_exchanges_symbols_labels
        LEFT JOIN
            h_labels USING(h_label_id)
        LEFT JOIN
            l_exchanges_symbols USING(l_exchange_symbol_id)
        LEFT JOIN
            h_symbols USING(h_symbol_id)
        LEFT JOIN
            h_exchanges USING(h_exchange_id)
        ORDER BY
            h_exchanges.h_exchange_name
    '''
    context.resources.logger.info(f"{query}")

    samples = context.resources.c3vault_exposure.read(query=query)
    for sample in samples:
        label_name, label_api_key, label_secret_key = sample[0], sample[1], sample[2]
        symbol_name, exchange_name = sample[3], sample[4]
        yield DynamicOutput(
            {
                'label_name': label_name,
                'label_api_key': label_api_key,
                'label_secret_key': label_secret_key,
                'symbol_name': symbol_name,
                'exchange_name': exchange_name
            },
            mapping_key=f'subtask_for_{label_name}_{exchange_name}_{symbol_name}'
        )


@op(
    name='load_to_dwh',
    required_resource_keys={
        'dwh',
        'logger',
        'df_serializer'
    }
)
def load_to_dwh(context, df: List[list]) -> None:
    now, concat_df = datetime.utcnow(), pd.DataFrame()
    for mini_df in df:
        mini_df = context.resources.df_serializer.df_from_list(mini_df)
        concat_df = concat_df.append(mini_df, ignore_index=True)
        context.resources.logger.info(mini_df.head())
    concat_df['pit_ts'] = now
    context.resources.dwh.get_client().insert_df(
        table='pit_big_table_account_balances',
        df=concat_df
    )
