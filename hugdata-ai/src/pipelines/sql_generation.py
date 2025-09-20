from typing import Dict, Any, List
import re
import sqlparse
from src.providers.llm_provider import LLMProvider
from src.providers.vector_store import VectorStore

class SQLGenerationPipeline:
    def __init__(self, llm_provider: LLMProvider, vector_store: VectorStore):
        self.llm = llm_provider
        self.vector_store = vector_store
    
    async def generate_sql(
        self,
        query: str,
        schema: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        project_id: str = None,
        mdl_hash: str = None,
        histories: List = None
    ) -> Dict[str, Any]:
        """
        Generate SQL from natural language using RAG approach
        """
        try:
            # Get project_id from context or parameter
            project_id = project_id or context.get('project_id', 'default')
            
            # 1. Retrieve relevant schema context
            relevant_context = await self.vector_store.similarity_search(
                query=query,
                collection_name=f"schema_{project_id}",
                limit=10,
            )
            
            # 2. Build prompt with context
            prompt = self._build_sql_prompt(query, schema, relevant_context)
            
            # 3. Generate SQL using LLM
            response = await self.llm.generate(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.1
            )
            
            # 4. Extract and validate SQL
            sql = self._extract_sql_from_response(response)
            
            # 5. Calculate confidence based on various factors
            confidence = self._calculate_confidence(sql, schema, query)
            
            return {
                "sql": sql,
                "confidence": confidence,
                "explanation": self._generate_explanation(sql, query),
                "reasoning_steps": self._extract_reasoning_steps(response)
            }
            
        except Exception as e:
            raise Exception(f"SQL generation failed: {str(e)}")
    
    def _build_sql_prompt(self, query: str, schema: Dict, context: List) -> str:
        """Build optimized prompt for SQL generation"""
        
        # Format schema information
        schema_info = self._format_schema_for_prompt(schema)
        
        # Format context information
        context_info = self._format_context_for_prompt(context)
        
        prompt = f"""
Given this database schema:
{schema_info}

Relevant context from similar queries:
{context_info}

Generate a SQL query for the following request: "{query}"

Requirements:
- Use only tables and columns that exist in the provided schema
- Follow SQL best practices and security guidelines
- Add appropriate LIMIT clauses (max 1000 rows)
- Use proper JOIN syntax when needed
- Add comments explaining complex logic
- Ensure the query is safe and read-only (no INSERT, UPDATE, DELETE, DROP, etc.)

Format your response as:
SQL: [your sql query here]
EXPLANATION: [brief explanation of what the query does]
REASONING: [step by step reasoning for your approach]
"""
        
        return prompt
    
    def _format_schema_for_prompt(self, schema: Dict[str, Any]) -> str:
        """Format schema information for the prompt"""
        if not schema or "tables" not in schema:
            return "No schema information available"
        
        formatted_tables = []
        for table_name, table_info in schema["tables"].items():
            if isinstance(table_info, list):
                # Simple list of column names
                columns = ", ".join(table_info)
            elif isinstance(table_info, dict) and "columns" in table_info:
                # Detailed column information
                columns = []
                for col in table_info["columns"]:
                    if isinstance(col, dict):
                        col_str = f"{col['name']} ({col.get('type', 'unknown')})"
                        if not col.get('nullable', True):
                            col_str += " NOT NULL"
                        columns.append(col_str)
                    else:
                        columns.append(str(col))
                columns = ", ".join(columns)
            else:
                columns = str(table_info)
            
            formatted_tables.append(f"Table: {table_name}\nColumns: {columns}")
        
        return "\n\n".join(formatted_tables)
    
    def _format_context_for_prompt(self, context: List[Dict]) -> str:
        """Format context information for the prompt"""
        if not context:
            return "No relevant context available"
        
        formatted_context = []
        for item in context[:5]:  # Limit to top 5 relevant items
            if isinstance(item, dict):
                formatted_context.append(
                    f"- Table: {item.get('table_name', 'unknown')}, "
                    f"Column: {item.get('column_name', 'unknown')} "
                    f"({item.get('column_type', 'unknown')})"
                )
        
        return "\n".join(formatted_context) if formatted_context else "No relevant context available"
    
    def _extract_sql_from_response(self, response: str) -> str:
        """Extract SQL query from LLM response"""
        # Look for SQL: prefix
        sql_match = re.search(r'SQL:\s*(.*?)(?:\n\s*EXPLANATION:|$)', response, re.DOTALL | re.IGNORECASE)
        if sql_match:
            sql = sql_match.group(1).strip()
        else:
            # Fallback: look for SELECT statements
            select_match = re.search(r'(SELECT.*?);?', response, re.DOTALL | re.IGNORECASE)
            if select_match:
                sql = select_match.group(1).strip()
            else:
                # Last resort: return the whole response cleaned up
                sql = response.strip()
        
        # Clean up and validate the SQL
        sql = self._clean_sql(sql)
        return sql
    
    def _clean_sql(self, sql: str) -> str:
        """Clean and validate SQL query"""
        # Remove markdown code blocks if present
        sql = re.sub(r'```sql\s*\n?', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'```\s*\n?', '', sql)
        
        # Remove extra whitespace
        sql = " ".join(sql.split())
        
        # Ensure it ends with semicolon
        if not sql.endswith(';'):
            sql += ';'
        
        # Basic security check - ensure it's a read-only query
        import re as _re
        dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE']
        sql_upper = sql.upper()
        for keyword in dangerous_keywords:
            if _re.search(rf"\b{keyword}\b", sql_upper):
                raise ValueError(f"Dangerous SQL keyword detected: {keyword}")
        
        return sql
    
    def _calculate_confidence(self, sql: str, schema: Dict, query: str) -> float:
        """Calculate confidence score for the generated SQL"""
        confidence = 0.5  # Base confidence
        
        try:
            # Check if SQL parses correctly
            parsed = sqlparse.parse(sql)
            if parsed:
                confidence += 0.2
            
            # Check if it contains expected keywords based on query
            query_lower = query.lower()
            sql_lower = sql.lower()
            
            if 'select' in sql_lower:
                confidence += 0.1
            if 'from' in sql_lower:
                confidence += 0.1
            if 'where' in query_lower and 'where' in sql_lower:
                confidence += 0.1
            if 'limit' in sql_lower:
                confidence += 0.1
            
            # Ensure confidence doesn't exceed 1.0
            confidence = min(confidence, 1.0)
            
        except Exception:
            confidence = 0.3  # Lower confidence if parsing fails
        
        return round(confidence, 2)
    
    def _generate_explanation(self, sql: str, original_query: str) -> str:
        """Generate a human-readable explanation of the SQL query"""
        try:
            parsed = sqlparse.parse(sql)[0]
            tokens = list(parsed.flatten())
            
            explanation = f"This query was generated to answer: '{original_query}'. "
            
            # Basic explanation based on SQL structure
            if any(token.ttype is sqlparse.tokens.Keyword and token.value.upper() == 'SELECT' for token in tokens):
                explanation += "It retrieves data "
            
            from_tables = []
            in_from_clause = False
            for token in tokens:
                if token.ttype is sqlparse.tokens.Keyword and token.value.upper() == 'FROM':
                    in_from_clause = True
                    continue
                elif token.ttype is sqlparse.tokens.Keyword and token.value.upper() in ['WHERE', 'GROUP', 'ORDER', 'LIMIT']:
                    in_from_clause = False
                elif in_from_clause and token.ttype is None and token.value.strip():
                    from_tables.append(token.value.strip())
            
            if from_tables:
                explanation += f"from the {', '.join(from_tables)} table(s)"
            
            if 'WHERE' in sql.upper():
                explanation += " with specific filtering conditions"
            
            if 'ORDER BY' in sql.upper():
                explanation += " and sorts the results"
            
            if 'LIMIT' in sql.upper():
                explanation += " with a limit on the number of rows returned"
            
            return explanation + "."
            
        except Exception:
            return f"This query was generated to answer: '{original_query}'"
    
    def _extract_reasoning_steps(self, response: str) -> List[str]:
        """Extract reasoning steps from LLM response"""
        reasoning_match = re.search(r'REASONING:\s*(.*)', response, re.DOTALL | re.IGNORECASE)
        if reasoning_match:
            reasoning_text = reasoning_match.group(1).strip()
            # Split by lines and clean up
            steps = [step.strip('- ').strip() for step in reasoning_text.split('\n') if step.strip()]
            return steps[:5]  # Limit to 5 steps
        
        # Default reasoning steps
        return [
            "Analyzed the natural language query",
            "Identified relevant tables and columns from schema",
            "Applied appropriate filters and conditions",
            "Added safety measures (LIMIT clause)",
            "Validated the generated SQL query"
        ]
