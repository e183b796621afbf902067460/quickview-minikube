from dagster import ScheduleDefinition

from etl.jobs.dex_screener.jobs import dag


every_10th_minute = ScheduleDefinition(
    name='dex_screener',
    job=dag,
    cron_schedule="*/10 * * * *"
)
