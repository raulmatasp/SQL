from dagster import job, SkipReason
from ..assets import database_schema, schema_vector_index, semantic_model

@job
def schema_sync_job():
    """
    Scheduled job to sync database schema and update semantic models
    
    This job runs daily to:
    - Refresh database schema from Laravel API
    - Update vector indexes with latest schema information
    - Regenerate semantic models with new business logic
    """
    # Define asset dependencies for schema sync
    schema = database_schema()
    vector_index = schema_vector_index(schema)
    semantic_model(schema)
    
    return vector_index