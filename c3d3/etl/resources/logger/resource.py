import logging
from dagster import resource, get_dagster_logger


@resource
def logger(init_context) -> logging.Logger:
    return get_dagster_logger()
