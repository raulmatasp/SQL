from dagster import sensor, RunRequest, SkipReason, SensorEvaluationContext
from ..jobs import schema_sync_job
import requests
import os

@sensor(job=schema_sync_job)
def schema_change_sensor(context: SensorEvaluationContext):
    """
    Sensor to detect database schema changes and trigger sync job
    
    This sensor monitors for:
    - Database schema modifications
    - New table additions
    - Column changes
    - Relationship updates
    """
    
    try:
        # Check Laravel API for schema change notifications
        laravel_url = os.getenv("LARAVEL_API_URL", "http://localhost:8000/api")
        api_token = os.getenv("LARAVEL_API_TOKEN", "")
        
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        } if api_token else {}
        
        # Check for schema change notifications endpoint
        response = requests.get(
            f"{laravel_url}/schema/changes/recent",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            changes = response.json()
            
            # Check if there are recent schema changes
            if changes.get("has_changes", False):
                recent_changes = changes.get("changes", [])
                
                context.log.info(f"Schema changes detected: {len(recent_changes)} changes found")
                
                # Create run request with change context
                return RunRequest(
                    run_key=f"schema_change_{changes.get('last_change_id', 'unknown')}",
                    tags={
                        "trigger": "schema_change",
                        "changes_count": str(len(recent_changes)),
                        "last_change_id": str(changes.get("last_change_id", ""))
                    }
                )
            else:
                return SkipReason("No schema changes detected")
        
        elif response.status_code == 404:
            # Endpoint doesn't exist yet - fall back to time-based trigger
            return SkipReason("Schema change monitoring not available - using scheduled sync")
        
        else:
            context.log.warning(f"Schema change check failed with status {response.status_code}")
            return SkipReason(f"Failed to check schema changes: HTTP {response.status_code}")
    
    except requests.RequestException as e:
        context.log.warning(f"Failed to connect to Laravel API for schema changes: {e}")
        return SkipReason("Cannot connect to Laravel API for schema change detection")
    
    except Exception as e:
        context.log.error(f"Schema change sensor error: {e}")
        return SkipReason(f"Sensor error: {str(e)}")