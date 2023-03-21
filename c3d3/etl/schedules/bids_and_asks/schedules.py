from dagster import ScheduleDefinition

from etl.jobs.bids_and_asks.jobs import dag


every_5th_minute = ScheduleDefinition(
    name='bids_and_asks',
    job=dag,
    cron_schedule="*/5 * * * *"
)
