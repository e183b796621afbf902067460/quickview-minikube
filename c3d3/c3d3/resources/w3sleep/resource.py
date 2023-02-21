import time
import random
from dagster import resource


MAX_BACKOFF = 64
MAX_RETRIES = 8


class W3Sleep:
    instance, n = None, 0

    def __new__(cls):
        if not cls.instance:
            cls.instance = super(W3Sleep, cls).__new__(cls)
        return cls.instance

    @classmethod
    def sleep(cls):
        if cls.n < MAX_RETRIES:
            time.sleep(min(2 ** cls.n + random.uniform(0, .1), MAX_BACKOFF))
        else:
            raise TimeoutError(f'W3Sleep too much retries: {cls.n}')
        cls.n += 1


@resource
def w3sleep(init_context) -> None:
    return W3Sleep()
