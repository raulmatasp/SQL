from dagster import asset, AssetExecutionContext
from typing import Dict, Any, List
from datetime import datetime, timedelta

@asset(deps=["sql_query_asset"], group_name="analytics")
def query_performance_analytics(
    context: AssetExecutionContext,
    sql_query_asset: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze query performance and usage patterns
    
    This asset tracks:
    - Query execution times and patterns
    - Most common query types
    - Error rates and failure analysis
    - Performance optimization suggestions
    """
    context.log.info("Starting query performance analytics")
    
    try:
        # Extract query metadata
        query_metadata = sql_query_asset.get("metadata", {})
        sql = sql_query_asset.get("sql", "")
        confidence = sql_query_asset.get("confidence", 0.0)
        
        # Analyze query characteristics
        query_analysis = _analyze_query_characteristics(sql)
        
        # Generate performance metrics
        performance_metrics = _calculate_performance_metrics(query_analysis, confidence)
        
        # Create optimization suggestions
        optimizations = _generate_optimization_suggestions(query_analysis)
        
        analytics_result = {
            "query_id": query_metadata.get("project_id", "unknown"),
            "analysis": query_analysis,
            "performance_metrics": performance_metrics,
            "optimization_suggestions": optimizations,
            "metadata": {
                "analyzed_at": context.instance.get_current_timestamp(),
                "confidence_score": confidence,
                "complexity_score": query_analysis.get("complexity_score", 0)
            }
        }
        
        context.log.info("Query performance analytics completed")
        return analytics_result
        
    except Exception as e:
        context.log.error(f"Query performance analytics failed: {str(e)}")
        raise e

@asset(deps=["semantic_model"], group_name="analytics") 
def business_intelligence_metrics(
    context: AssetExecutionContext,
    semantic_model: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate business intelligence metrics and insights
    
    This asset creates:
    - KPI dashboards and trend analysis
    - Business entity health scores
    - Data quality metrics
    - Usage pattern insights
    """
    context.log.info("Starting business intelligence metrics generation")
    
    try:
        entities = semantic_model.get("entities", [])
        business_metrics = semantic_model.get("business_metrics", [])
        
        # Calculate entity health scores
        entity_health = _calculate_entity_health_scores(entities)
        
        # Generate KPI trends (mock data for now)
        kpi_trends = _generate_kpi_trends(business_metrics)
        
        # Analyze data quality
        data_quality = _analyze_data_quality(entities)
        
        # Generate business insights
        business_insights = _generate_business_insights(entities, business_metrics)
        
        bi_metrics = {
            "project_id": semantic_model.get("project_id"),
            "entity_health_scores": entity_health,
            "kpi_trends": kpi_trends,
            "data_quality_metrics": data_quality,
            "business_insights": business_insights,
            "metadata": {
                "generated_at": context.instance.get_current_timestamp(),
                "entities_analyzed": len(entities),
                "kpis_tracked": len(business_metrics)
            }
        }
        
        context.log.info("Business intelligence metrics generated successfully")
        return bi_metrics
        
    except Exception as e:
        context.log.error(f"Business intelligence metrics failed: {str(e)}")
        raise e

@asset(deps=["schema_vector_index"], group_name="analytics")
def usage_pattern_analytics(
    context: AssetExecutionContext,
    schema_vector_index: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze usage patterns and schema utilization
    
    This asset tracks:
    - Most queried tables and columns
    - Schema coverage and utilization
    - User query patterns and preferences  
    - Data access frequency
    """
    context.log.info("Starting usage pattern analytics")
    
    try:
        project_id = schema_vector_index.get("metadata", {}).get("project_id")
        documents = schema_vector_index.get("documents", [])
        
        # Analyze table usage patterns
        table_usage = _analyze_table_usage_patterns(documents)
        
        # Calculate schema coverage
        schema_coverage = _calculate_schema_coverage(documents)
        
        # Generate usage recommendations
        recommendations = _generate_usage_recommendations(table_usage, schema_coverage)
        
        usage_analytics = {
            "project_id": project_id,
            "table_usage_patterns": table_usage,
            "schema_coverage_metrics": schema_coverage,
            "usage_recommendations": recommendations,
            "metadata": {
                "analyzed_at": context.instance.get_current_timestamp(),
                "documents_analyzed": len(documents)
            }
        }
        
        context.log.info("Usage pattern analytics completed")
        return usage_analytics
        
    except Exception as e:
        context.log.error(f"Usage pattern analytics failed: {str(e)}")
        raise e

def _analyze_query_characteristics(sql: str) -> Dict[str, Any]:
    """Analyze SQL query characteristics for performance insights"""
    
    if not sql:
        return {"complexity_score": 0, "query_type": "empty", "features": []}
    
    sql_upper = sql.upper()
    analysis = {
        "query_type": "SELECT",  # Assume SELECT for now
        "features": [],
        "tables_involved": [],
        "complexity_score": 0
    }
    
    # Detect query features
    features = []
    complexity = 0
    
    if "JOIN" in sql_upper:
        features.append("joins")
        complexity += 2
    if "SUBQUERY" in sql_upper or "(" in sql:
        features.append("subqueries") 
        complexity += 3
    if "GROUP BY" in sql_upper:
        features.append("aggregation")
        complexity += 1
    if "ORDER BY" in sql_upper:
        features.append("sorting")
        complexity += 1
    if "HAVING" in sql_upper:
        features.append("having_clause")
        complexity += 2
    if "UNION" in sql_upper:
        features.append("union")
        complexity += 2
    
    # Extract table names (basic regex would be better)
    words = sql_upper.split()
    from_index = -1
    for i, word in enumerate(words):
        if word == "FROM":
            from_index = i
            break
    
    if from_index > -1 and from_index + 1 < len(words):
        table = words[from_index + 1].strip(",;")
        analysis["tables_involved"].append(table.lower())
    
    analysis["features"] = features
    analysis["complexity_score"] = min(complexity, 10)  # Cap at 10
    
    return analysis

def _calculate_performance_metrics(query_analysis: Dict, confidence: float) -> Dict[str, Any]:
    """Calculate performance metrics based on query analysis"""
    
    complexity = query_analysis.get("complexity_score", 0)
    features = query_analysis.get("features", [])
    
    # Estimated execution time (mock calculation)
    base_time = 100  # milliseconds
    complexity_multiplier = 1 + (complexity * 0.2)
    estimated_time = base_time * complexity_multiplier
    
    # Performance rating
    if complexity <= 2:
        performance_rating = "excellent"
    elif complexity <= 5:
        performance_rating = "good"
    elif complexity <= 8:
        performance_rating = "fair" 
    else:
        performance_rating = "poor"
    
    return {
        "estimated_execution_time_ms": round(estimated_time),
        "performance_rating": performance_rating,
        "complexity_level": "low" if complexity <= 3 else "medium" if complexity <= 6 else "high",
        "confidence_impact": "high" if confidence > 0.8 else "medium" if confidence > 0.5 else "low",
        "optimization_potential": "high" if complexity > 6 else "medium" if complexity > 3 else "low"
    }

def _generate_optimization_suggestions(query_analysis: Dict) -> List[Dict[str, str]]:
    """Generate query optimization suggestions"""
    
    suggestions = []
    features = query_analysis.get("features", [])
    complexity = query_analysis.get("complexity_score", 0)
    
    if complexity > 6:
        suggestions.append({
            "type": "complexity",
            "suggestion": "Consider breaking complex query into simpler parts",
            "priority": "high"
        })
    
    if "joins" in features:
        suggestions.append({
            "type": "indexing",
            "suggestion": "Ensure proper indexes exist on join columns",
            "priority": "medium"
        })
    
    if "subqueries" in features:
        suggestions.append({
            "type": "rewrite",
            "suggestion": "Consider rewriting subqueries as JOINs for better performance",
            "priority": "medium"
        })
    
    if not any(feature in features for feature in ["joins", "aggregation"]):
        suggestions.append({
            "type": "caching",
            "suggestion": "Simple queries can benefit from result caching",
            "priority": "low"
        })
    
    return suggestions

def _calculate_entity_health_scores(entities: List[Dict]) -> List[Dict]:
    """Calculate health scores for business entities"""
    
    health_scores = []
    
    for entity in entities:
        # Mock health score calculation
        attributes = entity.get("attributes", [])
        
        # Factors for health score
        completeness = len([attr for attr in attributes if not attr.get("nullable", True)]) / max(len(attributes), 1)
        diversity = len(set(attr.get("business_type") for attr in attributes)) / max(len(attributes), 1)
        
        health_score = (completeness * 0.6 + diversity * 0.4) * 100
        
        health_scores.append({
            "entity": entity["name"],
            "health_score": round(health_score, 1),
            "factors": {
                "completeness": round(completeness * 100, 1),
                "diversity": round(diversity * 100, 1)
            },
            "status": "healthy" if health_score > 70 else "warning" if health_score > 40 else "critical"
        })
    
    return health_scores

def _generate_kpi_trends(business_metrics: List[Dict]) -> List[Dict]:
    """Generate mock KPI trend data"""
    
    trends = []
    
    for metric in business_metrics[:5]:  # Limit to 5 metrics
        # Generate mock trend data for last 30 days
        trend_data = []
        base_value = 1000
        
        for i in range(30):
            date = datetime.now() - timedelta(days=29-i)
            # Mock trending data with some variation
            variation = 0.8 + (i * 0.01)  # Slight upward trend
            value = base_value * variation
            
            trend_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": round(value, 2)
            })
        
        trends.append({
            "metric": metric["name"],
            "display_name": metric["display_name"],
            "trend_data": trend_data,
            "growth_rate": "+2.3%",  # Mock growth rate
            "status": "increasing"
        })
    
    return trends

def _analyze_data_quality(entities: List[Dict]) -> Dict[str, Any]:
    """Analyze data quality metrics"""
    
    total_attributes = sum(len(entity.get("attributes", [])) for entity in entities)
    nullable_attributes = sum(
        len([attr for attr in entity.get("attributes", []) if attr.get("nullable", True)])
        for entity in entities
    )
    
    # Calculate quality metrics
    completeness_score = ((total_attributes - nullable_attributes) / max(total_attributes, 1)) * 100
    consistency_score = 85  # Mock consistency score
    accuracy_score = 92    # Mock accuracy score
    
    overall_score = (completeness_score + consistency_score + accuracy_score) / 3
    
    return {
        "overall_score": round(overall_score, 1),
        "completeness": round(completeness_score, 1),
        "consistency": round(consistency_score, 1),
        "accuracy": round(accuracy_score, 1),
        "status": "good" if overall_score > 80 else "warning" if overall_score > 60 else "critical",
        "issues_found": []  # Would contain actual data quality issues
    }

def _generate_business_insights(entities: List[Dict], metrics: List[Dict]) -> List[Dict]:
    """Generate business insights from analysis"""
    
    insights = []
    
    # Entity-based insights
    customer_entities = [e for e in entities if e["entity_type"] == "customer"]
    if customer_entities:
        insights.append({
            "type": "entity_analysis",
            "insight": f"Found {len(customer_entities)} customer-related entities with rich attribute sets",
            "recommendation": "Focus on customer analytics and segmentation opportunities",
            "priority": "medium"
        })
    
    # Metrics-based insights
    financial_metrics = [m for m in metrics if m.get("category") == "financial"]
    if financial_metrics:
        insights.append({
            "type": "metrics_analysis", 
            "insight": f"Tracking {len(financial_metrics)} financial metrics for revenue optimization",
            "recommendation": "Consider adding customer lifetime value and churn prediction metrics",
            "priority": "high"
        })
    
    # General insights
    insights.append({
        "type": "data_maturity",
        "insight": f"Schema contains {len(entities)} business entities with {sum(len(e.get('attributes', [])) for e in entities)} total attributes",
        "recommendation": "Data model shows good complexity for advanced analytics implementations",
        "priority": "low"
    })
    
    return insights

def _analyze_table_usage_patterns(documents: List[Dict]) -> List[Dict]:
    """Analyze table usage patterns from schema documents"""
    
    usage_patterns = []
    
    # Group documents by table
    tables = {}
    for doc in documents:
        if doc.get("type") == "table":
            table_name = doc.get("table_name")
            if table_name:
                tables[table_name] = tables.get(table_name, 0) + 1
    
    # Create usage pattern analysis
    for table_name, frequency in tables.items():
        usage_patterns.append({
            "table": table_name,
            "access_frequency": "high" if frequency > 5 else "medium" if frequency > 2 else "low",
            "usage_score": frequency,
            "recommendation": "Consider optimization" if frequency > 5 else "Monitor usage"
        })
    
    return sorted(usage_patterns, key=lambda x: x["usage_score"], reverse=True)

def _calculate_schema_coverage(documents: List[Dict]) -> Dict[str, Any]:
    """Calculate schema coverage metrics"""
    
    total_documents = len(documents)
    table_docs = len([d for d in documents if d.get("type") == "table"])
    column_docs = len([d for d in documents if d.get("type") == "column"])
    relation_docs = len([d for d in documents if d.get("type") == "relationship"])
    
    return {
        "total_elements": total_documents,
        "tables_indexed": table_docs,
        "columns_indexed": column_docs,
        "relationships_indexed": relation_docs,
        "coverage_percentage": 100 if total_documents > 0 else 0,  # Mock full coverage
        "indexing_health": "excellent"
    }

def _generate_usage_recommendations(table_usage: List[Dict], coverage: Dict) -> List[Dict]:
    """Generate recommendations based on usage patterns"""
    
    recommendations = []
    
    # High usage tables
    high_usage_tables = [t for t in table_usage if t["access_frequency"] == "high"]
    if high_usage_tables:
        recommendations.append({
            "type": "performance",
            "recommendation": f"Optimize indexing for {len(high_usage_tables)} high-usage tables",
            "priority": "high",
            "affected_tables": [t["table"] for t in high_usage_tables]
        })
    
    # Low usage tables
    low_usage_tables = [t for t in table_usage if t["access_frequency"] == "low"]
    if len(low_usage_tables) > 3:
        recommendations.append({
            "type": "cleanup",
            "recommendation": f"Review {len(low_usage_tables)} low-usage tables for potential archival",
            "priority": "low",
            "affected_tables": [t["table"] for t in low_usage_tables]
        })
    
    # Coverage recommendations
    if coverage["coverage_percentage"] < 90:
        recommendations.append({
            "type": "indexing",
            "recommendation": "Improve schema indexing coverage for better search performance",
            "priority": "medium"
        })
    
    return recommendations