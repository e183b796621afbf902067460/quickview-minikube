from dagster import ScheduleDefinition

from etl.jobs._analytics_adj.jobs import dag


every_hour = ScheduleDefinition(
    name='_analytics_adj',
    job=dag,
    cron_schedule="@hourly"
)
