from dagster import job
from ..assets import semantic_model, business_intelligence_metrics, usage_pattern_analytics

@job
def analytics_refresh_job():
    """
    Scheduled job to refresh analytics and business intelligence metrics
    
    This job runs periodically to:
    - Update business intelligence dashboards
    - Refresh usage pattern analytics
    - Generate new insights and recommendations
    """
    # Analytics dependencies
    semantic_data = semantic_model()
    business_intelligence_metrics(semantic_data)
    usage_pattern_analytics()
    
    return business_intelligence_metrics