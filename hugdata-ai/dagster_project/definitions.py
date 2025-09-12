from dagster import Definitions

from .resources import (
    database_resource,
    vector_store_resource,
    llm_provider_resource
)

from .assets import (
    database_schema,
    schema_vector_index,
    sql_query_asset
)

# Define Dagster project
defs = Definitions(
    assets=[
        database_schema,
        schema_vector_index,
        sql_query_asset
    ],
    resources={
        "database_resource": database_resource,
        "vector_store_resource": vector_store_resource,
        "llm_provider_resource": llm_provider_resource
    }
)