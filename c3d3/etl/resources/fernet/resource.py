import os
from cryptography import fernet as fn
from dagster import resource


@resource
def fernet(init_context) -> fn.Fernet:
    return fn.Fernet(key=os.getenv('JWT_FERNET_KEY', ''))
