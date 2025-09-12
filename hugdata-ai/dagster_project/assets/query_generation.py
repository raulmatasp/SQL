from dagster import asset, AssetExecutionContext, Config
from typing import Dict, Any
from ..resources.vector_store import VectorStoreResource
from ..resources.llm_provider import LLMProviderResource

class QueryGenerationConfig(Config):
    """Configuration for SQL query generation"""
    user_query: str
    project_id: str = "default"
    max_results: int = 1000

@asset(deps=["schema_vector_index"], group_name="query_processing")
def sql_query_asset(
    context: AssetExecutionContext,
    config: QueryGenerationConfig,
    schema_vector_index: Dict[str, Any],
    vector_store_resource: VectorStoreResource,
    llm_provider_resource: LLMProviderResource
) -> Dict[str, Any]:
    """
    Generate SQL query from natural language using semantic search
    
    This asset combines:
    - Vector search for relevant schema elements
    - LLM-powered SQL generation
    - Query validation and optimization
    """
    context.log.info(f"Generating SQL for query: {config.user_query}")
    
    project_id = config.project_id
    user_query = config.user_query
    
    try:
        # 1. Search for relevant schema elements
        relevant_context = vector_store_resource.similarity_search(
            query=user_query,
            collection=f"schema_{project_id}",
            limit=10
        )
        
        context.log.info(f"Found {len(relevant_context)} relevant schema elements")
        
        # 2. Build prompt for LLM
        prompt = _build_sql_prompt(
            user_query=user_query,
            schema_context=relevant_context,
            project_metadata=schema_vector_index.get("metadata", {})
        )
        
        # 3. Generate SQL using LLM
        llm_response = llm_provider_resource.generate(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.1
        )
        
        # 4. Parse and validate SQL
        parsed_result = _parse_llm_response(llm_response)
        
        # 5. Add safety measures
        safe_sql = _add_safety_measures(parsed_result.get("sql", ""), config.max_results)
        
        result = {
            "sql": safe_sql,
            "explanation": parsed_result.get("explanation", ""),
            "reasoning_steps": parsed_result.get("reasoning_steps", []),
            "confidence": _calculate_confidence(safe_sql, relevant_context),
            "metadata": {
                "project_id": project_id,
                "user_query": user_query,
                "generated_at": context.instance.get_current_timestamp(),
                "context_elements": len(relevant_context)
            }
        }
        
        context.log.info("SQL generation completed successfully")
        return result
        
    except Exception as e:
        context.log.error(f"SQL generation failed: {str(e)}")
        raise e

def _build_sql_prompt(user_query: str, schema_context: list, project_metadata: dict) -> str:
    """Build optimized prompt for SQL generation"""
    
    # Format context information
    context_info = "\n".join([
        f"- Table: {item.get('table_name', 'unknown')}, "
        f"Column: {item.get('column_name', 'N/A')} "
        f"({item.get('column_type', 'unknown')})"
        for item in schema_context[:5]  # Limit to top 5
    ])
    
    prompt = f"""
You are a SQL expert. Generate a safe, efficient SQL query based on this request:

USER REQUEST: "{user_query}"

RELEVANT SCHEMA CONTEXT:
{context_info}

REQUIREMENTS:
- Use only tables and columns from the provided context
- Add appropriate LIMIT clause (max 1000 rows)
- Ensure query is safe (SELECT only, no modifications)
- Follow SQL best practices
- Add comments for complex logic

FORMAT YOUR RESPONSE AS:
SQL: [your complete sql query here]
EXPLANATION: [brief explanation of what the query does]
REASONING: [step by step reasoning]
"""
    
    return prompt.strip()

def _parse_llm_response(response: str) -> Dict[str, Any]:
    """Parse structured response from LLM"""
    import re
    
    result = {
        "sql": "",
        "explanation": "",
        "reasoning_steps": []
    }
    
    # Extract SQL
    sql_match = re.search(r'SQL:\s*(.*?)(?:\n\s*EXPLANATION:|$)', response, re.DOTALL | re.IGNORECASE)
    if sql_match:
        result["sql"] = sql_match.group(1).strip()
    
    # Extract explanation
    exp_match = re.search(r'EXPLANATION:\s*(.*?)(?:\n\s*REASONING:|$)', response, re.DOTALL | re.IGNORECASE)
    if exp_match:
        result["explanation"] = exp_match.group(1).strip()
    
    # Extract reasoning steps
    reasoning_match = re.search(r'REASONING:\s*(.*)', response, re.DOTALL | re.IGNORECASE)
    if reasoning_match:
        reasoning_text = reasoning_match.group(1).strip()
        steps = [step.strip('- ').strip() for step in reasoning_text.split('\n') if step.strip()]
        result["reasoning_steps"] = steps[:5]  # Limit to 5 steps
    
    return result

def _add_safety_measures(sql: str, max_results: int) -> str:
    """Add safety measures to SQL query"""
    if not sql:
        return ""
    
    # Clean SQL
    sql = sql.strip()
    if not sql.endswith(';'):
        sql += ';'
    
    # Remove dangerous keywords
    dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE']
    sql_upper = sql.upper()
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            raise ValueError(f"Dangerous SQL keyword detected: {keyword}")
    
    # Add LIMIT if not present
    if 'LIMIT' not in sql.upper():
        sql = sql.rstrip(';')
        sql += f' LIMIT {max_results};'
    
    return sql

def _calculate_confidence(sql: str, context: list) -> float:
    """Calculate confidence score for generated SQL"""
    confidence = 0.5  # Base confidence
    
    if sql and 'SELECT' in sql.upper():
        confidence += 0.2
    
    if 'FROM' in sql.upper():
        confidence += 0.1
    
    if len(context) > 0:
        confidence += 0.1
    
    if 'LIMIT' in sql.upper():
        confidence += 0.1
    
    return min(confidence, 1.0)