from dagster import ScheduleDefinition

from c3d3.jobs.whole_market_trades_history.jobs import dag


every_5th_minute = ScheduleDefinition(
    name='whole_market_trades_history',
    job=dag,
    cron_schedule="*/5 * * * *"
)
