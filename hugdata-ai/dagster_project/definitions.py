from dagster import Definitions, ScheduleDefinition

from .resources import (
    database_resource,
    vector_store_resource,
    llm_provider_resource
)

from .assets import (
    database_schema,
    schema_vector_index,
    sql_query_asset,
    semantic_model,
    query_performance_analytics,
    business_intelligence_metrics,
    usage_pattern_analytics,
    optimized_query,
    query_execution_plan
)

from .jobs import (
    schema_sync_job,
    analytics_refresh_job
)

from .sensors import (
    schema_change_sensor
)

# Define schedules for regular job execution
schema_sync_schedule = ScheduleDefinition(
    job=schema_sync_job,
    cron_schedule="0 2 * * *",  # Daily at 2 AM
    name="daily_schema_sync"
)

analytics_refresh_schedule = ScheduleDefinition(
    job=analytics_refresh_job,
    cron_schedule="0 6 * * *",  # Daily at 6 AM
    name="daily_analytics_refresh"
)

# Define Dagster project with complete workflow orchestration
defs = Definitions(
    assets=[
        # Core pipeline assets
        database_schema,
        schema_vector_index,
        sql_query_asset,
        semantic_model,
        
        # Analytics assets
        query_performance_analytics,
        business_intelligence_metrics,
        usage_pattern_analytics,
        
        # Optimization assets
        optimized_query,
        query_execution_plan
    ],
    jobs=[
        schema_sync_job,
        analytics_refresh_job
    ],
    schedules=[
        schema_sync_schedule,
        analytics_refresh_schedule
    ],
    sensors=[
        schema_change_sensor
    ],
    resources={
        "database_resource": database_resource,
        "vector_store_resource": vector_store_resource,
        "llm_provider_resource": llm_provider_resource
    }
)