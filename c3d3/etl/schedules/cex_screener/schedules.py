from dagster import ScheduleDefinition

from etl.jobs.cex_screener.jobs import dag


every_5th_minute = ScheduleDefinition(
    name='cex_screener',
    job=dag,
    cron_schedule="*/5 * * * *"
)