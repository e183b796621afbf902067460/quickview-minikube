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
            h_addresses0.h_address as wallet_address,
            h_addresses1.h_address as token_address,
            h_chains.h_network_name,
            h_chains.h_network_rpc_node,
            h_labels.h_label_name
        FROM
            l_tokens_on_wallets
        LEFT JOIN
            l_addresses_chains_labels USING(l_address_chain_label_id)
        LEFT JOIN
            h_labels USING(h_label_id)
        LEFT JOIN
            l_addresses_chains AS l_addresses_chains0 ON l_addresses_chains_labels.l_address_chain_id = l_addresses_chains0.l_address_chain_id
        LEFT JOIN
            h_addresses as h_addresses0 ON l_addresses_chains0.h_address_id = h_addresses0.h_address_id
        LEFT JOIN
            l_addresses_chains AS l_addresses_chains1 ON l_tokens_on_wallets.l_address_chain_id = l_addresses_chains1.l_address_chain_id
        LEFT JOIN
            h_addresses as h_addresses1 ON l_addresses_chains1.h_address_id = h_addresses1.h_address_id
        LEFT JOIN
            h_chains ON l_addresses_chains0.h_chain_id = h_chains.h_chain_id
    '''

    context.resources.logger.info(f"{query}")

    samples = context.resources.d3vault_exposure.read(query=query)
    for sample in samples:
        wallet_address, token_address, label_name = sample[0], sample[1], sample[4]
        network_name, network_rpc_node = sample[2], sample[3]
        yield DynamicOutput(
            {
                'wallet_address': wallet_address,
                'token_address': token_address,
                'network_name': network_name,
                'network_rpc_node': network_rpc_node,
                'label_name': label_name
            },
            mapping_key=f'subtask_for_{wallet_address}_{token_address}_{network_name}'
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
    concat_df.to_sql(name='pit_big_table_wallet_balances_erc_20', con=context.resources.dwh.get_engine(), if_exists='append', index=False)
