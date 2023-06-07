from dagster import ScheduleDefinition

from etl.jobs.cex_order_history_screener.jobs import dag


every_30th_minute = ScheduleDefinition(
    name='cex_order_history_screener',
    job=dag,
    cron_schedule="*/30 * * * *"
)
