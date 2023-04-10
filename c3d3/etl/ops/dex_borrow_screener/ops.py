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
            h_addresses0.h_address as token_address,
            h_addresses1.h_address as wallet_address,
            h_labels.h_label_name,
            h_protocols.h_protocol_name,
            h_chains.h_network_name,
            h_chains.h_network_rpc_node
        FROM
            l_addresses_chains_protocols_specifications_labels
        LEFT JOIN
            l_addresses_chains_protocols_specifications USING(l_address_chain_protocol_specification_id)
        LEFT JOIN
            l_protocols_specifications USING(l_protocol_specification_id)
        LEFT JOIN
            h_protocols USING(h_protocol_id)
        LEFT JOIN
            h_specifications USING(h_specification_id)
        LEFT JOIN
            l_addresses_chains AS l_addresses_chains0 ON l_addresses_chains_protocols_specifications.l_address_chain_id = l_addresses_chains0.l_address_chain_id
        LEFT JOIN
            h_addresses AS h_addresses0 ON l_addresses_chains0.h_address_id = h_addresses0.h_address_id
        LEFT JOIN
            l_addresses_chains_labels USING(l_address_chain_label_id)
        LEFT JOIN
            h_labels USING(h_label_id)
        LEFT JOIN
            l_addresses_chains AS l_addresses_chains1 ON l_addresses_chains_labels.l_address_chain_id = l_addresses_chains1.l_address_chain_id
        LEFT JOIN
            h_addresses AS h_addresses1 ON l_addresses_chains1.h_address_id = h_addresses1.h_address_id
        LEFT JOIN
            h_chains ON l_addresses_chains0.h_chain_id = h_chains.h_chain_id
        WHERE
            h_specifications.h_specification_name = 'lending'
        ORDER BY
            h_protocols.h_protocol_name
    '''
    context.resources.logger.info(f"{query}")

    samples = context.resources.d3vault_exposure.read(query=query)
    for sample in samples:
        token_address = sample[0]
        wallet_address, label_name = sample[1], sample[2]
        protocol_name = sample[3]
        network_name, network_rpc_node = sample[4], sample[5]
        yield DynamicOutput(
            {
                'token_address': token_address,
                'wallet_address': wallet_address,
                'label_name': label_name,
                'protocol_name': protocol_name,
                'network_name': network_name,
                'network_rpc_node': network_rpc_node
            },
            mapping_key=f'subtask_for_{label_name}_{protocol_name}_{token_address}_{network_name}'
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
        table='pit_big_table_hedge_to_borrows',
        df=concat_df
    )
