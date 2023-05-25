from dagster import ScheduleDefinition

from etl.jobs._analytics_adj.jobs import dag


every_15th_minute = ScheduleDefinition(
    name='_analytics_adj',
    job=dag,
    cron_schedule="*/15 * * * *"
)
