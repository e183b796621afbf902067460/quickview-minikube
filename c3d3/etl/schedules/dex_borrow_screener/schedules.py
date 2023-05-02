from dagster import ScheduleDefinition

from etl.jobs.dex_borrow_screener.jobs import dag


every_1th_minute = ScheduleDefinition(
    name='dex_borrow_screener',
    job=dag,
    cron_schedule="*/2 * * * *"
)
