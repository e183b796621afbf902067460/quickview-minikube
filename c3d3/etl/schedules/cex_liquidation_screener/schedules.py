from dagster import ScheduleDefinition

from etl.jobs.cex_liquidation_screener.jobs import dag


every_1th_minute = ScheduleDefinition(
    name='cex_liquidation_screener',
    job=dag,
    cron_schedule="*/2 * * * *"
)
