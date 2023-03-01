from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
import clickhouse_connect
from sqlalchemy.orm import Session
import pandahouse as ph
import pandas as pd
from dagster import resource

import os
from urllib.parse import quote_plus


class DataWarehouse:
    DB_ADDRESS = os.getenv('DWH_HOST', '')
    DB_PORT = os.getenv('DWH_PORT', '')
    DB_USER = os.getenv('DWH_USER', '')
    DB_PASSWORD = quote_plus(os.getenv('DWH_PASSWORD', ''))
    DB_NAME = os.getenv('DWH_DB', '')

    DB_URL = f'clickhouse://{DB_USER}:{DB_PASSWORD}@{DB_ADDRESS}/{DB_NAME}'

    @classmethod
    def get_client(cls):
        return clickhouse_connect.get_client(
            host=cls.DB_ADDRESS,
            port=cls.DB_PORT,
            username=cls.DB_USER,
            password=cls.DB_PASSWORD,
            database=cls.DB_NAME
        )

    @classmethod
    def get_connection(cls):
        return dict(
            database=cls.DB_NAME,
            host=f'http://{cls.DB_ADDRESS}:{cls.DB_PORT}',
            user=cls.DB_USER,
            password=cls.DB_PASSWORD
        )

    @classmethod
    def get_session(cls) -> Session:
        s = Session(cls.get_engine())
        try:
            yield s
        finally:
            s.close()

    @classmethod
    def get_engine(cls) -> Engine:
        return create_engine(cls.get_uri())

    @classmethod
    def get_uri(cls) -> str:
        return cls.DB_URL

    def read(self, query, *args, **kwargs):
        return self.get_engine().execute(query).fetchall()

    @classmethod
    def load(cls, df: pd.DataFrame, table: str) -> None:
        ph.to_clickhouse(df=df, table=table, index=False, connection=cls.get_connection(), chunksize=1000000)


@resource
def dwh(init_context) -> DataWarehouse:
    return DataWarehouse()
