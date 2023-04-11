from dagster import ScheduleDefinition

from etl.jobs.dex_gwei_screener.jobs import dag


every_1th_minute = ScheduleDefinition(
    name='dex_gwei_screener',
    job=dag,
    cron_schedule="*/1 * * * *"
)
