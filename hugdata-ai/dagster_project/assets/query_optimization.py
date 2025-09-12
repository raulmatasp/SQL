from dagster import asset, AssetExecutionContext
from typing import Dict, Any, List
import re

@asset(deps=["sql_query_asset", "semantic_model"], group_name="optimization")
def optimized_query(
    context: AssetExecutionContext,
    sql_query_asset: Dict[str, Any],
    semantic_model: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Optimize SQL queries using semantic understanding and performance heuristics
    
    This asset:
    - Analyzes generated SQL for optimization opportunities
    - Applies semantic model knowledge for better optimization
    - Suggests index recommendations
    - Implements query rewriting rules
    """
    context.log.info("Starting query optimization")
    
    try:
        original_sql = sql_query_asset.get("sql", "")
        confidence = sql_query_asset.get("confidence", 0.0)
        project_id = sql_query_asset.get("metadata", {}).get("project_id")
        
        # Get semantic context
        entities = semantic_model.get("entities", [])
        relationships = semantic_model.get("semantic_relationships", [])
        
        context.log.info(f"Optimizing SQL query with {len(entities)} entities context")
        
        # Perform optimization analysis
        optimization_analysis = _analyze_optimization_opportunities(original_sql, entities, relationships)
        
        # Apply optimization rules
        optimized_sql = _apply_optimization_rules(original_sql, optimization_analysis)
        
        # Generate index recommendations
        index_recommendations = _generate_index_recommendations(optimization_analysis, entities)
        
        # Calculate optimization impact
        impact_assessment = _assess_optimization_impact(original_sql, optimized_sql, optimization_analysis)
        
        result = {
            "original_sql": original_sql,
            "optimized_sql": optimized_sql,
            "optimization_applied": len(optimization_analysis["optimizations"]) > 0,
            "optimization_rules": optimization_analysis["optimizations"],
            "index_recommendations": index_recommendations,
            "impact_assessment": impact_assessment,
            "metadata": {
                "project_id": project_id,
                "optimized_at": context.instance.get_current_timestamp(),
                "original_confidence": confidence,
                "optimization_confidence": min(confidence * 1.1, 1.0)  # Slight boost for optimization
            }
        }
        
        context.log.info(f"Query optimization completed with {len(optimization_analysis['optimizations'])} rules applied")
        return result
        
    except Exception as e:
        context.log.error(f"Query optimization failed: {str(e)}")
        raise e

@asset(deps=["optimized_query"], group_name="optimization")
def query_execution_plan(
    context: AssetExecutionContext,
    optimized_query: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate execution plan analysis and cost estimation
    
    This asset provides:
    - Estimated query execution plan
    - Cost analysis and resource requirements
    - Performance predictions
    - Bottleneck identification
    """
    context.log.info("Generating query execution plan analysis")
    
    try:
        optimized_sql = optimized_query.get("optimized_sql", "")
        optimization_rules = optimized_query.get("optimization_rules", [])
        
        # Analyze execution plan
        execution_plan = _analyze_execution_plan(optimized_sql)
        
        # Estimate costs
        cost_estimation = _estimate_query_costs(execution_plan, optimization_rules)
        
        # Identify bottlenecks
        bottlenecks = _identify_bottlenecks(execution_plan, cost_estimation)
        
        # Generate performance predictions
        performance_predictions = _predict_performance(execution_plan, cost_estimation)
        
        result = {
            "execution_plan": execution_plan,
            "cost_estimation": cost_estimation,
            "bottlenecks": bottlenecks,
            "performance_predictions": performance_predictions,
            "recommendations": _generate_execution_recommendations(bottlenecks),
            "metadata": {
                "analyzed_at": context.instance.get_current_timestamp(),
                "plan_complexity": execution_plan.get("complexity", "unknown")
            }
        }
        
        context.log.info("Query execution plan analysis completed")
        return result
        
    except Exception as e:
        context.log.error(f"Query execution plan analysis failed: {str(e)}")
        raise e

def _analyze_optimization_opportunities(sql: str, entities: List[Dict], relationships: List[Dict]) -> Dict[str, Any]:
    """Analyze SQL query for optimization opportunities"""
    
    if not sql:
        return {"optimizations": [], "analysis": {}}
    
    sql_upper = sql.upper()
    analysis = {
        "query_type": "SELECT",
        "tables_involved": [],
        "joins_detected": [],
        "where_conditions": [],
        "has_subqueries": False,
        "has_aggregation": False,
        "has_ordering": False
    }
    
    optimizations = []
    
    # Parse basic query structure
    analysis["has_subqueries"] = "(" in sql and "SELECT" in sql[sql.find("("):]
    analysis["has_aggregation"] = any(agg in sql_upper for agg in ["GROUP BY", "SUM(", "COUNT(", "AVG(", "MAX(", "MIN("])
    analysis["has_ordering"] = "ORDER BY" in sql_upper
    
    # Extract table names (simplified)
    from_match = re.search(r'FROM\s+(\w+)', sql_upper)
    if from_match:
        analysis["tables_involved"].append(from_match.group(1).lower())
    
    # Detect joins
    join_types = ["JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "OUTER JOIN"]
    for join_type in join_types:
        if join_type in sql_upper:
            analysis["joins_detected"].append(join_type.lower())
    
    # Optimization rules based on analysis
    
    # Rule 1: Add LIMIT if missing on simple queries
    if "LIMIT" not in sql_upper and not analysis["has_aggregation"]:
        optimizations.append({
            "rule": "add_limit",
            "description": "Add LIMIT clause to prevent large result sets",
            "priority": "high",
            "applicable": True
        })
    
    # Rule 2: Optimize WHERE clause ordering
    where_match = re.search(r'WHERE\s+(.+?)(?:\s+GROUP|ORDER|LIMIT|$)', sql, re.IGNORECASE | re.DOTALL)
    if where_match:
        where_clause = where_match.group(1)
        if " AND " in where_clause:
            optimizations.append({
                "rule": "optimize_where_order",
                "description": "Reorder WHERE conditions for better selectivity",
                "priority": "medium",
                "applicable": True
            })
    
    # Rule 3: Index recommendations for JOINs
    if analysis["joins_detected"]:
        optimizations.append({
            "rule": "join_optimization",
            "description": "Optimize JOIN operations with proper indexing",
            "priority": "high",
            "applicable": True
        })
    
    # Rule 4: Subquery optimization
    if analysis["has_subqueries"]:
        optimizations.append({
            "rule": "subquery_optimization", 
            "description": "Consider converting subqueries to JOINs",
            "priority": "medium",
            "applicable": True
        })
    
    # Rule 5: SELECT * avoidance
    if "SELECT *" in sql_upper:
        optimizations.append({
            "rule": "select_specific_columns",
            "description": "Replace SELECT * with specific column names",
            "priority": "medium",
            "applicable": True
        })
    
    return {
        "analysis": analysis,
        "optimizations": optimizations,
        "semantic_context": {
            "entities_available": len(entities),
            "relationships_available": len(relationships)
        }
    }

def _apply_optimization_rules(original_sql: str, optimization_analysis: Dict[str, Any]) -> str:
    """Apply optimization rules to the SQL query"""
    
    optimized_sql = original_sql
    optimizations = optimization_analysis.get("optimizations", [])
    
    for optimization in optimizations:
        rule = optimization.get("rule")
        
        if rule == "add_limit" and optimization.get("applicable"):
            # Add LIMIT if not present
            if "LIMIT" not in optimized_sql.upper():
                optimized_sql = optimized_sql.rstrip(";") + " LIMIT 1000;"
        
        elif rule == "select_specific_columns" and optimization.get("applicable"):
            # Replace SELECT * with common columns (simplified)
            if "SELECT *" in optimized_sql.upper():
                optimized_sql = re.sub(
                    r'SELECT \*',
                    'SELECT id, name, created_at',
                    optimized_sql,
                    flags=re.IGNORECASE
                )
        
        elif rule == "optimize_where_order" and optimization.get("applicable"):
            # This would require more complex parsing in practice
            # For now, just add a comment
            optimized_sql = "-- Optimized WHERE clause ordering\n" + optimized_sql
    
    return optimized_sql

def _generate_index_recommendations(optimization_analysis: Dict[str, Any], entities: List[Dict]) -> List[Dict]:
    """Generate index recommendations based on optimization analysis"""
    
    recommendations = []
    analysis = optimization_analysis.get("analysis", {})
    tables_involved = analysis.get("tables_involved", [])
    
    # Recommendations for tables involved in query
    for table in tables_involved:
        # Find entity info
        entity = next((e for e in entities if e["name"].lower() == table), None)
        if entity:
            # Primary key index (usually exists)
            pk_field = entity.get("primary_key", "id")
            recommendations.append({
                "table": table,
                "columns": [pk_field],
                "index_type": "primary",
                "priority": "high",
                "rationale": "Primary key index for efficient lookups"
            })
            
            # Foreign key indexes
            for attr in entity.get("attributes", []):
                if attr.get("name", "").endswith("_id") and attr["name"] != pk_field:
                    recommendations.append({
                        "table": table,
                        "columns": [attr["name"]],
                        "index_type": "foreign_key",
                        "priority": "high",
                        "rationale": f"Foreign key index for JOIN operations on {attr['name']}"
                    })
    
    # JOIN-specific recommendations
    if analysis.get("joins_detected"):
        recommendations.append({
            "table": "multiple",
            "columns": ["join_columns"],
            "index_type": "composite",
            "priority": "high",
            "rationale": "Composite indexes for JOIN operations"
        })
    
    # WHERE clause recommendations
    if analysis.get("where_conditions"):
        recommendations.append({
            "table": tables_involved[0] if tables_involved else "unknown",
            "columns": ["where_columns"],
            "index_type": "filtered",
            "priority": "medium",
            "rationale": "Indexes for WHERE clause filtering"
        })
    
    return recommendations

def _assess_optimization_impact(original_sql: str, optimized_sql: str, optimization_analysis: Dict) -> Dict[str, Any]:
    """Assess the impact of applied optimizations"""
    
    optimizations_applied = len(optimization_analysis.get("optimizations", []))
    
    # Mock impact assessment (would be more sophisticated in practice)
    if optimizations_applied == 0:
        impact_level = "none"
        estimated_improvement = 0
    elif optimizations_applied <= 2:
        impact_level = "low"
        estimated_improvement = 15
    elif optimizations_applied <= 4:
        impact_level = "medium" 
        estimated_improvement = 35
    else:
        impact_level = "high"
        estimated_improvement = 55
    
    return {
        "impact_level": impact_level,
        "estimated_performance_improvement_percent": estimated_improvement,
        "optimizations_applied": optimizations_applied,
        "query_changed": original_sql != optimized_sql,
        "benefits": _calculate_optimization_benefits(optimization_analysis),
        "trade_offs": _identify_optimization_tradeoffs(optimization_analysis)
    }

def _calculate_optimization_benefits(optimization_analysis: Dict) -> List[str]:
    """Calculate benefits of optimization"""
    
    benefits = []
    optimizations = optimization_analysis.get("optimizations", [])
    
    for opt in optimizations:
        rule = opt.get("rule")
        if rule == "add_limit":
            benefits.append("Reduced memory usage and faster response times")
        elif rule == "join_optimization":
            benefits.append("Improved JOIN performance with proper indexing")
        elif rule == "select_specific_columns":
            benefits.append("Reduced network transfer and memory usage")
        elif rule == "subquery_optimization":
            benefits.append("Better query execution plan and performance")
    
    return list(set(benefits))  # Remove duplicates

def _identify_optimization_tradeoffs(optimization_analysis: Dict) -> List[str]:
    """Identify potential trade-offs of optimization"""
    
    tradeoffs = []
    optimizations = optimization_analysis.get("optimizations", [])
    
    for opt in optimizations:
        rule = opt.get("rule")
        if rule == "add_limit":
            tradeoffs.append("May not return all relevant results")
        elif rule == "join_optimization":
            tradeoffs.append("Additional index maintenance overhead")
        elif rule == "select_specific_columns":
            tradeoffs.append("May need to modify if additional columns required")
    
    return tradeoffs

def _analyze_execution_plan(sql: str) -> Dict[str, Any]:
    """Analyze query execution plan (mock implementation)"""
    
    # Mock execution plan analysis
    operations = []
    complexity = "simple"
    
    sql_upper = sql.upper()
    
    # Basic operation detection
    if "SELECT" in sql_upper:
        operations.append("table_scan")
    if "JOIN" in sql_upper:
        operations.append("hash_join")
        complexity = "medium"
    if "GROUP BY" in sql_upper:
        operations.append("aggregation")
        complexity = "medium"
    if "ORDER BY" in sql_upper:
        operations.append("sort")
    if "LIMIT" in sql_upper:
        operations.append("limit")
    
    # Subqueries increase complexity
    if "(" in sql and "SELECT" in sql[sql.find("("):]:
        complexity = "high"
        operations.append("subquery")
    
    return {
        "operations": operations,
        "complexity": complexity,
        "estimated_steps": len(operations),
        "parallel_operations": max(1, len(operations) // 2)
    }

def _estimate_query_costs(execution_plan: Dict, optimization_rules: List[Dict]) -> Dict[str, Any]:
    """Estimate query execution costs"""
    
    base_cost = 10  # Base cost units
    operations = execution_plan.get("operations", [])
    complexity = execution_plan.get("complexity", "simple")
    
    # Cost calculation based on operations
    operation_costs = {
        "table_scan": 5,
        "index_scan": 2,
        "hash_join": 15,
        "nested_loop": 25,
        "aggregation": 10,
        "sort": 8,
        "limit": 1,
        "subquery": 20
    }
    
    total_cost = base_cost + sum(operation_costs.get(op, 5) for op in operations)
    
    # Complexity multiplier
    complexity_multipliers = {
        "simple": 1.0,
        "medium": 1.5,
        "high": 2.5
    }
    
    total_cost *= complexity_multipliers.get(complexity, 1.0)
    
    # Optimization impact
    optimization_discount = len(optimization_rules) * 0.1
    total_cost *= (1.0 - min(optimization_discount, 0.5))
    
    return {
        "total_cost_units": round(total_cost, 2),
        "cpu_cost": round(total_cost * 0.6, 2),
        "io_cost": round(total_cost * 0.3, 2),
        "memory_cost": round(total_cost * 0.1, 2),
        "cost_level": "low" if total_cost < 20 else "medium" if total_cost < 50 else "high"
    }

def _identify_bottlenecks(execution_plan: Dict, cost_estimation: Dict) -> List[Dict]:
    """Identify potential performance bottlenecks"""
    
    bottlenecks = []
    operations = execution_plan.get("operations", [])
    total_cost = cost_estimation.get("total_cost_units", 0)
    
    # High-cost operations
    expensive_ops = ["hash_join", "nested_loop", "subquery", "aggregation"]
    for op in operations:
        if op in expensive_ops:
            bottlenecks.append({
                "type": "operation",
                "operation": op,
                "severity": "high" if total_cost > 50 else "medium",
                "description": f"{op.replace('_', ' ').title()} operation may be expensive"
            })
    
    # Missing indexes (heuristic)
    if "table_scan" in operations and "index_scan" not in operations:
        bottlenecks.append({
            "type": "indexing",
            "operation": "table_scan",
            "severity": "high",
            "description": "Full table scan detected - consider adding indexes"
        })
    
    # High complexity
    if execution_plan.get("complexity") == "high":
        bottlenecks.append({
            "type": "complexity",
            "operation": "query_structure",
            "severity": "medium",
            "description": "High query complexity may impact performance"
        })
    
    return bottlenecks

def _predict_performance(execution_plan: Dict, cost_estimation: Dict) -> Dict[str, Any]:
    """Predict query performance characteristics"""
    
    total_cost = cost_estimation.get("total_cost_units", 0)
    complexity = execution_plan.get("complexity", "simple")
    
    # Performance predictions based on cost and complexity
    if total_cost < 20:
        response_time = "< 100ms"
        throughput = "high"
        resource_usage = "low"
    elif total_cost < 50:
        response_time = "100ms - 1s"
        throughput = "medium"
        resource_usage = "medium"
    else:
        response_time = "> 1s"
        throughput = "low"
        resource_usage = "high"
    
    return {
        "estimated_response_time": response_time,
        "throughput_rating": throughput,
        "resource_usage": resource_usage,
        "scalability": "good" if complexity == "simple" else "fair" if complexity == "medium" else "poor",
        "recommendations": [
            "Monitor execution time in production",
            "Consider query result caching for frequently accessed data"
        ]
    }

def _generate_execution_recommendations(bottlenecks: List[Dict]) -> List[Dict]:
    """Generate recommendations based on identified bottlenecks"""
    
    recommendations = []
    
    for bottleneck in bottlenecks:
        bottleneck_type = bottleneck.get("type")
        severity = bottleneck.get("severity", "medium")
        
        if bottleneck_type == "operation":
            recommendations.append({
                "area": "query_optimization",
                "recommendation": f"Optimize {bottleneck['operation']} operation",
                "priority": severity,
                "action": "Consider query rewriting or additional indexes"
            })
        elif bottleneck_type == "indexing":
            recommendations.append({
                "area": "database_tuning",
                "recommendation": "Add appropriate indexes",
                "priority": severity,
                "action": "Create indexes on frequently queried columns"
            })
        elif bottleneck_type == "complexity":
            recommendations.append({
                "area": "architecture",
                "recommendation": "Simplify query structure",
                "priority": severity,
                "action": "Break complex query into simpler parts or use materialized views"
            })
    
    # General recommendations
    if not recommendations:
        recommendations.append({
            "area": "monitoring",
            "recommendation": "Continue monitoring performance",
            "priority": "low",
            "action": "Set up query performance monitoring and alerting"
        })
    
    return recommendations