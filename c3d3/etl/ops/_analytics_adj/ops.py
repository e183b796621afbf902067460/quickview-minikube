from typing import List
import datetime

from dagster import op, DynamicOut, DynamicOutput
import pandas as pd

from c3d3.domain.d3.adhoc.chains.polygon.chain import Polygon

from c3d3.infrastructure.c3.handlers.cex_screener.binance.usdtm.handler import BinanceUsdtmCexScreenerHandler
from c3d3.infrastructure.c3.handlers.cex_screener.binance.spot.handler import BinanceSpotCexScreenerHandler
from c3d3.infrastructure.d3.handlers.dex_screener.quickswap.v3.handler import QuickSwapV3DexScreenerHandler
from c3d3.infrastructure.d3.handlers.dex_screener.uniswap.v3.handler import UniSwapV3DexScreenerHandler


_CEX, _DEX, _SIZE = 'cex', 'dex', 'size'
_IS_ADJUST, _IS_REVERSE = 'is_adjust', 'is_reverse'
_H_EXCHANGE_NAME, _H_TICKER_NAME = 'h_exchange_name', 'h_ticker_name'
_H_POOL_ADDRESS, _H_PROTOCOL_NAME, _H_NETWORK_NAME = 'h_pool_address', 'h_protocol_name', 'h_network_name'

CFGS = {
    # Polygon WETH/USDC QuickV3 & ETHUSDT Binance USDT-M
    1: {
        _DEX: {
            _H_POOL_ADDRESS: '0x55CAaBB0d2b704FD0eF8192A7E35D8837e678207',
            _H_PROTOCOL_NAME: QuickSwapV3DexScreenerHandler.key,
            _H_NETWORK_NAME: Polygon.name
        },
        _CEX: {
            _H_EXCHANGE_NAME: BinanceUsdtmCexScreenerHandler.key,
            _H_TICKER_NAME: 'ETHUSDT'
        },
        _SIZE: 2,
        _IS_ADJUST: True,
        _IS_REVERSE: True
    },
    # Polygon WMATIC/USDC QuickV3 & MATICUSDT Binance USDT-M
    2: {
        _DEX: {
            _H_POOL_ADDRESS: '0xAE81FAc689A1b4b1e06e7ef4a2ab4CD8aC0A087D',
            _H_PROTOCOL_NAME: QuickSwapV3DexScreenerHandler.key,
            _H_NETWORK_NAME: Polygon.name
        },
        _CEX: {
            _H_EXCHANGE_NAME: BinanceUsdtmCexScreenerHandler.key,
            _H_TICKER_NAME: 'MATICUSDT'
        },
        _SIZE: 5000,
        _IS_ADJUST: True,
        _IS_REVERSE: False
    },
    # Polygon WETH/USDC UniV3 & ETHUSDT Binance USDT-M
    3: {
        _DEX: {
            _H_POOL_ADDRESS: '0x45dDa9cb7c25131DF268515131f647d726f50608',
            _H_PROTOCOL_NAME: UniSwapV3DexScreenerHandler.key,
            _H_NETWORK_NAME: Polygon.name
        },
        _CEX: {
            _H_EXCHANGE_NAME: BinanceUsdtmCexScreenerHandler.key,
            _H_TICKER_NAME: 'ETHUSDT'
        },
        _SIZE: 2,
        _IS_ADJUST: True,
        _IS_REVERSE: True
    },
    # Polygon WMATIC/USDC UniV3 & MATICUSDT Binance USDT-M
    4: {
        _DEX: {
            _H_POOL_ADDRESS: '0xA374094527e1673A86dE625aa59517c5dE346d32',
            _H_PROTOCOL_NAME: UniSwapV3DexScreenerHandler.key,
            _H_NETWORK_NAME: Polygon.name
        },
        _CEX: {
            _H_EXCHANGE_NAME: BinanceUsdtmCexScreenerHandler.key,
            _H_TICKER_NAME: 'MATICUSDT'
        },
        _SIZE: 5000,
        _IS_ADJUST: True,
        _IS_REVERSE: False
    }
}


def _calc_win(row: pd.Series, df: pd.DataFrame) -> pd.DataFrame:
    return df[(df['pit_ts'] <= row['pit_ts'] - datetime.timedelta(seconds=3)) & (df['pit_ts'] >= row['pit_ts'] - datetime.timedelta(seconds=6))]


@op(
    name='configs',
    out=DynamicOut(dict)
)
def _get_c3d3(context) -> List[dict]:

    for k, v in CFGS.items():

        pool_address, protocol_name, network_name = v[_DEX][_H_POOL_ADDRESS], v[_DEX][_H_PROTOCOL_NAME], v[_DEX][_H_NETWORK_NAME]
        exchange_name, ticker_name = v[_CEX][_H_EXCHANGE_NAME], v[_CEX][_H_TICKER_NAME]
        size = v[_SIZE]
        is_adjust, is_reverse = v[_IS_ADJUST], v[_IS_REVERSE]

        yield DynamicOutput(
            {
                _H_POOL_ADDRESS: pool_address,
                _H_PROTOCOL_NAME: protocol_name,
                _H_NETWORK_NAME: network_name,
                _H_EXCHANGE_NAME: exchange_name,
                _H_TICKER_NAME: ticker_name,
                _SIZE: size,
                _IS_ADJUST: is_adjust,
                _IS_REVERSE: is_reverse
            },
            mapping_key=f'subtask_for_{network_name}_{protocol_name}_{pool_address}_{exchange_name}_{ticker_name}'
        )


@op(
    name='df',
    required_resource_keys={
        'dwh',
        'logger',
        'df_serializer'
    }
)
def _etl(context, configs: dict) -> None:
    now_dt = datetime.datetime.utcnow()
    delta_dt = now_dt - datetime.timedelta(days=7)
    delta_ts = delta_dt.timestamp()

    dwh_engine, dwh_client, log = context.resources.dwh.get_engine(), context.resources.dwh.get_client(), context.resources.logger

    ts_q = f'''
        SELECT 
            MAX(pit_ts) 
        FROM 
            pit_big_table_analytics_adj 
        WHERE 
            h_pool_address = '{configs[_H_POOL_ADDRESS]}' AND
            h_protocol_name = '{configs[_H_PROTOCOL_NAME]}' AND
            h_network_name = '{configs[_H_NETWORK_NAME]}' AND
            h_exchange_name = '{configs[_H_EXCHANGE_NAME]}' AND
            h_ticker_name = '{configs[_H_TICKER_NAME]}'
    '''
    ts_down_border_dt = dwh_client.query(ts_q).result_rows[0][0]
    ts_down_border_ts = ts_down_border_dt.timestamp() if ts_down_border_dt.strftime('%Y') != '1970' or not ts_down_border_dt else delta_ts

    ts_down_border_dt = datetime.datetime.fromtimestamp(ts_down_border_ts)

    if now_dt - ts_down_border_dt > datetime.timedelta(days=1):
        now_dt = ts_down_border_dt + datetime.timedelta(days=1)

    now_ts = now_dt.timestamp()

    log.info(f"Current borders for query: from {ts_down_border_dt} to {now_dt}")

    d3_q = f'''
        WITH dropped_duplicates_view AS (
            SELECT
                pit_symbol,
                AVG(pit_amount0) AS pit_amount0,
                AVG(pit_amount1) AS pit_amount1,
                AVG(pit_decimals0) AS pit_decimals0,
                AVG(pit_decimals1) AS pit_decimals1,
                AVG(pit_fee) AS pit_fee,
                AVG(pit_sqrt_p) AS pit_sqrt_p,
                AVG(pit_liquidity) AS pit_liquidity,
                AVG(pit_index_position_in_the_block) AS pit_index_position_in_the_block,
                AVG(pit_gas_used) AS pit_gas_used,
                AVG(pit_effective_gas_price) AS pit_effective_gas_price,
                AVG(pit_gas_usd_price) AS pit_gas_usd_price,
                AVG(pit_price) AS pit_price,
                pit_recipient,
                pit_tx_hash,
                pit_ts
            FROM 
                pit_big_table_bids_and_asks
            WHERE
                h_pool_address = '{configs[_H_POOL_ADDRESS]}' AND
                h_network_name = '{configs[_H_NETWORK_NAME]}' AND
                h_protocol_name = '{configs[_H_PROTOCOL_NAME]}' AND
                pit_ts > {ts_down_border_ts} AND
                pit_ts < {now_ts}
            GROUP BY
                pit_symbol,
                pit_tx_hash,
                pit_recipient,
                pit_ts
        )
        SELECT
            pit_symbol,
            pit_recipient AS pit_sender,
            pit_price AS pit_dex_price,
            pit_amount0 / POW(10, pit_decimals0) AS pit_amount0,
            pit_amount1 / POW(10, pit_decimals1) AS pit_amount1,
            ABS(pit_amount1) AS pit_usd_size,
            if(
                {configs[_IS_REVERSE]}, 
                1 / ABS({configs[_SIZE]} / ((POW(2, 96) / pit_sqrt_p - 1 / (pit_sqrt_p / POW(2, 96) - {configs[_SIZE]} * POW(10, pit_decimals0) * (1 - pit_fee) / pit_liquidity)) * pit_liquidity / POW(10, pit_decimals1))), 
                ABS(((pit_liquidity * ((1 / (({configs[_SIZE]} * POW(10, pit_decimals0) * (1 - pit_fee) / pit_liquidity) + 1 / (pit_sqrt_p / POW(2, 96)))) - pit_sqrt_p / POW(2, 96))) / POW(10, pit_decimals1)) / {configs[_SIZE]})
            ) AS pit_bid,
            if(
                {configs[_IS_REVERSE]},
                1 / ABS(((pit_liquidity * ((1 / (({configs[_SIZE]} * pit_bid * POW(10, pit_decimals1) * (1 - pit_fee) / pit_liquidity) + 1 / (pit_sqrt_p / POW(2, 96)))) - pit_sqrt_p / POW(2, 96))) / POW(10, pit_decimals0)) / ({configs[_SIZE]} * pit_bid)),
                ABS({configs[_SIZE]} * pit_bid / ((POW(2, 96) / pit_sqrt_p - 1 / (pit_sqrt_p / POW(2, 96) - {configs[_SIZE]} * pit_bid * POW(10, pit_decimals1) * (1 - pit_fee) / pit_liquidity)) * pit_liquidity / POW(10, pit_decimals0)))
            ) AS pit_ask,
            pit_index_position_in_the_block,
            pit_effective_gas_price * pit_gas_used / POW(10, 18) AS pit_gwei,
            pit_effective_gas_price / POW(10, 9) AS pit_gas_price,
            pit_gas_usd_price,
            pit_fee AS pit_dex_fee,
            pit_tx_hash,
            pit_ts
        FROM 
            dropped_duplicates_view
    '''
    c3_q = f'''
        SELECT
            pit_price,
            pit_ts
        FROM
            pit_big_table_whole_market_trades_history
        WHERE
            h_exchange_name = '{configs[_H_EXCHANGE_NAME]}' AND
            h_ticker_name = '{configs[_H_TICKER_NAME]}' AND
            pit_ts > {ts_down_border_ts} AND
            pit_ts < {now_ts}
    '''
    d3_df = pd.read_sql(sql=d3_q, con=dwh_engine)
    c3_df = pd.read_sql(sql=c3_q, con=dwh_engine)

    if d3_df.empty or c3_df.empty:
        return

    d3_max_ts = d3_df.pit_ts.max().value
    c3_max_ts = c3_df.pit_ts.max().value

    ts_up_border = d3_max_ts if d3_max_ts < c3_max_ts else c3_max_ts
    ts_up_border = datetime.datetime.fromtimestamp(ts_up_border / 10 ** 9)

    d3_df = d3_df[d3_df['pit_ts'] <= ts_up_border]
    c3_df = c3_df[c3_df['pit_ts'] <= ts_up_border]

    if d3_df.empty or c3_df.empty:
        return

    log.info(f"Current borders for df: from {ts_down_border_dt} to {ts_up_border}")

    c3_df['pit_ts'] = pd.to_datetime(c3_df['pit_ts'])

    c3_ohlc_df = c3_df.set_index('pit_ts').pit_price.resample('S').ohlc().reset_index().ffill().bfill()
    c3_ohlc_df.rename(
        columns={
            'open': 'pit_c3_open',
            'close': 'pit_c3_close',
            'high': 'pit_c3_high',
            'low': 'pit_c3_low'
        },
        inplace=True
    )

    if configs[_IS_ADJUST]:
        adj_q = f'''
            SELECT
                pit_price,
                pit_ts
            FROM
                pit_big_table_whole_market_trades_history
            WHERE
                h_exchange_name = '{BinanceSpotCexScreenerHandler.key}' AND
                h_ticker_name = 'USDCUSDT' AND
                pit_ts BETWEEN {ts_down_border_ts} AND {ts_up_border.timestamp()}
        '''
        adj_df = pd.read_sql(sql=adj_q, con=dwh_engine)
        adj_ohlc_df = adj_df.set_index('pit_ts').pit_price.resample('S').ohlc().reset_index().ffill().bfill()
        adj_ohlc_df.rename(
            columns={
                'open': 'pit_adj_open',
                'close': 'pit_adj_close',
                'high': 'pit_adj_high',
                'low': 'pit_adj_low'
            },
            inplace=True
        )
        c3_ohlc_df = pd.merge(c3_ohlc_df, adj_ohlc_df, how='outer', on=['pit_ts']).ffill().bfill()

        c3_ohlc_df['pit_c3_open'] = c3_ohlc_df['pit_c3_open'] / c3_ohlc_df['pit_adj_open']
        c3_ohlc_df['pit_c3_close'] = c3_ohlc_df['pit_c3_close'] / c3_ohlc_df['pit_adj_close']
        c3_ohlc_df['pit_c3_high'] = c3_ohlc_df['pit_c3_high'] / c3_ohlc_df['pit_adj_high']
        c3_ohlc_df['pit_c3_low'] = c3_ohlc_df['pit_c3_low'] / c3_ohlc_df['pit_adj_low']

        c3_ohlc_df = c3_ohlc_df[['pit_ts', 'pit_c3_open', 'pit_c3_close', 'pit_c3_high', 'pit_c3_low']]

    df = pd.merge(c3_ohlc_df, d3_df, how='outer', on=['pit_ts']).sort_values('pit_ts').ffill().bfill()

    df['pit_down_th'] = df['pit_bid'] / df['pit_c3_low'] - 1
    df['pit_up_th'] = df['pit_c3_high'] / df['pit_ask'] - 1
    df['pit_side'] = df.apply(lambda x: 'BUY' if x.pit_amount1 < 0 else 'SELL', axis=1)

    df = df.assign(_pit_tx_hash_lag=lambda x: x.pit_tx_hash.shift(1)).bfill()
    df['pit_is_new_tx'] = df.apply(lambda x: 0 if x.pit_tx_hash == x._pit_tx_hash_lag else 1, axis=1)

    df['_pit_lag_bid'] = df.apply(lambda row: _calc_win(row, df)['pit_bid'].mean(), axis=1).bfill()
    df['_pit_lag_ask'] = df.apply(lambda row: _calc_win(row, df)['pit_ask'].mean(), axis=1).bfill()
    df['_pit_lag_low_min'] = df.apply(lambda row: _calc_win(row, df)['pit_c3_low'].min(), axis=1).bfill()
    df['_pit_lag_high_max'] = df.apply(lambda row: _calc_win(row, df)['pit_c3_high'].max(), axis=1).bfill()

    df['pit_buy_tt'], df['pit_sell_tt'] = df['_pit_lag_bid'] / df['_pit_lag_low_min'] - 1, df['_pit_lag_high_max'] / df['_pit_lag_ask'] - 1
    df['pit_lag_buy_price'], df['pit_lag_sell_price'] = df['_pit_lag_low_min'], df['_pit_lag_high_max']

    df['pit_gross'] = df.apply(lambda x: ((x.pit_lag_sell_price - (x.pit_lag_sell_price * 0.0002)) - x.pit_dex_price) * abs(x.pit_amount0) if x.pit_side == 'BUY' else (x.pit_dex_price - (x.pit_lag_buy_price - (x.pit_lag_buy_price * 0.0002))) * abs(x.pit_amount0), axis=1)
    df['pit_net'] = df.apply(lambda x: (((x.pit_lag_sell_price - (x.pit_lag_sell_price * 0.0002)) - x.pit_dex_price) * abs(x.pit_amount0 - (x.pit_amount0 * x.pit_dex_fee))) - (x.pit_gwei * x.pit_gas_usd_price) if x.pit_side == 'BUY' else ((x.pit_dex_price - (x.pit_lag_buy_price - (x.pit_lag_buy_price * 0.0002))) * abs(x.pit_amount0 - (x.pit_amount0 * x.pit_dex_fee)) - (x.pit_gwei * x.pit_gas_usd_price)), axis=1)

    df['h_network_name'] = configs[_H_NETWORK_NAME]
    df['h_protocol_name'] = configs[_H_PROTOCOL_NAME]
    df['h_pool_address'] = configs[_H_POOL_ADDRESS]
    df['h_exchange_name'] = configs[_H_EXCHANGE_NAME]
    df['h_ticker_name'] = configs[_H_TICKER_NAME]

    df = df[
        [
            'pit_ts', 'pit_symbol', 'h_network_name', 'h_protocol_name', 'h_pool_address', 'h_exchange_name', 'h_ticker_name',
            'pit_c3_open', 'pit_c3_high', 'pit_c3_low', 'pit_c3_close', 'pit_dex_price',
            'pit_amount0', 'pit_amount1', 'pit_usd_size', 'pit_bid', 'pit_ask', 'pit_sender',
            'pit_down_th', 'pit_up_th', 'pit_buy_tt', 'pit_sell_tt',
            'pit_lag_buy_price', 'pit_lag_sell_price',
            'pit_side', 'pit_index_position_in_the_block', 'pit_gwei', 'pit_gas_price',
            'pit_tx_hash', 'pit_is_new_tx',
            'pit_gross', 'pit_net'
        ]
    ]

    df.to_sql(name='pit_big_table_analytics_adj', con=dwh_engine, if_exists='append', index=False)
