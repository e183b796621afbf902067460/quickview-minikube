from typing import List
from datetime import datetime

from dagster import op, DynamicOut, DynamicOutput
import pandas as pd


@op(
    name='configs',
    required_resource_keys={
        'd3vault_exposure',
        'logger'
    },
    out=DynamicOut(dict)
)
def extract_from_d3vault(context) -> List[dict]:
    query = '''
        SELECT
            h_addresses.h_address,
            h_labels.h_label_name,
            h_chains.h_network_name,
            h_chains.h_network_rpc_node,
            h_chains.h_native_chain_token
        FROM
            l_addresses_chains_labels
        LEFT JOIN
            h_labels USING(h_label_id)
        LEFT JOIN
            l_addresses_chains USING(l_address_chain_id)
        LEFT JOIN
            h_chains USING(h_chain_id)
        LEFT JOIN
            h_addresses USING(h_address_id)
    '''

    context.resources.logger.info(f"{query}")

    samples = context.resources.d3vault_exposure.read(query=query)
    for sample in samples:
        wallet_address, label_name = sample[0], sample[1]
        network_name, network_rpc_node, native_chain_token = sample[2], sample[3], sample[4]
        yield DynamicOutput(
            {
                'wallet_address': wallet_address,
                'label_name': label_name,
                'network_name': network_name,
                'network_rpc_node': network_rpc_node,
                'native_chain_token': native_chain_token,
            },
            mapping_key=f'subtask_for_{wallet_address}_{network_name}'
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
    concat_df.to_sql(name='pit_big_table_wallet_balances_gas', con=context.resources.dwh.get_engine(), if_exists='append', index=False)
