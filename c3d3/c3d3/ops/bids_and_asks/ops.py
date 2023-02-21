from typing import List
from datetime import datetime

from dagster import op, DynamicOut, DynamicOutput
import pandas as pd


@op(
    name='configs',
    required_resource_keys={
        'd3vault',
        'logger'
    },
    tags={
        'fabric': 'bids_and_asks'
    },
    out=DynamicOut(dict)
)
def extract_from_d3vault(context) -> List[dict]:
    query = '''
        SELECT
            h_addresses.h_address,
            h_chains.h_network_name,
            h_chains.h_native_chain_token,
            h_chains.h_network_rpc_node,
            h_chains.h_network_block_limit,
            h_chains.h_network_uri,
            h_chains.h_network_api_key,
            h_protocols.h_protocol_name,
            s_is_reverse.s_is_reverse
        FROM
            l_addresses_chains_protocols_specifications
        LEFT JOIN
            s_is_reverse USING(l_address_chain_protocol_specification_id)
        LEFT JOIN
            l_protocols_specifications USING(l_protocol_specification_id)
        LEFT JOIN
            h_protocols USING(h_protocol_id)
        LEFT JOIN
            h_specifications USING(h_specification_id)
        LEFT JOIN
            l_addresses_chains USING(l_address_chain_id)
        LEFT JOIN
            h_addresses USING(h_address_id)
        LEFT JOIN
            h_chains USING(h_chain_id)
        WHERE
            h_specifications.h_specification_name = 'dex'
        ORDER BY
            h_protocols.h_protocol_name
    '''
    context.resources.logger.info(f"{query}")

    samples = context.resources.d3vault.read(query=query)
    for sample in samples:
        pool_address = sample[0]
        network_name, native_chain_token, network_rpc_node = sample[1], sample[2], sample[3]
        network_block_limit, network_uri, network_api_key = sample[4], sample[5], sample[6]
        protocol_name, is_reverse = sample[7], sample[8]
        yield DynamicOutput(
            {
                'pool_address': pool_address,
                'network_name': network_name,
                'native_chain_token': native_chain_token,
                'network_rpc_node': network_rpc_node,
                'network_block_limit': network_block_limit,
                'network_uri': network_uri,
                'network_api_key': network_api_key,
                'protocol_name': protocol_name,
                'is_reverse': is_reverse
            },
            mapping_key=f'subtask_for_{protocol_name}_{pool_address}_{network_name}'
        )


@op(
    name='load_to_dwh',
    required_resource_keys={
        'dwh',
        'logger',
        'df_serializer'
    },
    tags={
        'fabric': 'bids_and_asks'
    }
)
def load_to_dwh(context, df: List[list]) -> None:
    concat_df = pd.DataFrame()
    for mini_df in df:
        mini_df = context.resources.df_serializer.df_from_list(mini_df)
        concat_df = concat_df.append(mini_df, ignore_index=True)
        context.resources.logger.info(mini_df.head())
    context.resources.dwh.get_client().insert_df(
        table='pit_big_table_bids_and_asks',
        df=concat_df
    )
