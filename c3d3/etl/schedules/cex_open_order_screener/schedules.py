from dagster import ScheduleDefinition

from etl.jobs.cex_open_order_screener.jobs import dag


every_1th_minute = ScheduleDefinition(
    name='cex_open_order_screener',
    job=dag,
    cron_schedule="*/1 * * * *"
)
