from typing import List
from dagster import resource
import pandas as pd


class DataFrameToDagsterMapReduceSerializer:

    @staticmethod
    def df_to_list(df: pd.DataFrame) -> List[list]:
        return [df.columns.values.tolist()] + df.values.tolist()

    @staticmethod
    def df_from_list(lst: List[list]) -> pd.DataFrame:
        return pd.DataFrame(lst[1:], columns=lst[0])


@resource
def df_serializer(init_context) -> DataFrameToDagsterMapReduceSerializer:
    return DataFrameToDagsterMapReduceSerializer()

