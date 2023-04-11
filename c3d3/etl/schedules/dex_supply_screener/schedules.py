from dagster import ScheduleDefinition

from etl.jobs.dex_supply_screener.jobs import dag


every_1th_minute = ScheduleDefinition(
    name='dex_supply_screener',
    job=dag,
    cron_schedule="*/1 * * * *"
)
