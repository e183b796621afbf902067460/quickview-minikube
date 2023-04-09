import random
from dagster import RetryPolicy, Backoff, Jitter


MAX_RETRIES = 12


W3Sleepy = RetryPolicy(
    max_retries=MAX_RETRIES // 6,
    delay=random.uniform(0, .1),
    backoff=Backoff.EXPONENTIAL,
    jitter=Jitter.PLUS_MINUS
)
