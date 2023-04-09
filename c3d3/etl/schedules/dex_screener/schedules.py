from dagster import ScheduleDefinition

from etl.jobs.dex_screener.jobs import dag


every_5th_minute = ScheduleDefinition(
    name='dex_screener',
    job=dag,
    cron_schedule="*/5 * * * *"
)
