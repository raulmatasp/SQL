import logging
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from src.providers.llm_provider import LLMProvider
from src.providers.vector_store import VectorStore

logger = logging.getLogger("hugdata-ai")

@dataclass
class SQLError:
    """Represents an SQL error with correction context"""
    sql: str
    error: str
    error_type: str = "syntax_error"
    line_number: Optional[int] = None

class SQLCorrectionPipeline:
    """Pipeline for correcting syntactically incorrect SQL queries"""

    def __init__(self, llm_provider: LLMProvider, vector_store: VectorStore):
        self.llm = llm_provider
        self.vector_store = vector_store

        # SQL correction rules and patterns
        self.sql_rules = """
1. Use proper ANSI SQL syntax
2. Ensure all table and column names are properly quoted if needed
3. Use correct JOIN syntax (JOIN ... ON ...)
4. Ensure parentheses are balanced
5. Use proper data type casting
6. Ensure all referenced tables and columns exist in the schema
7. Use proper GROUP BY clause when using aggregate functions
8. Ensure HAVING clause is used correctly with GROUP BY
9. Use proper ORDER BY syntax
10. Add LIMIT clauses for data safety (max 1000 rows)
"""

    async def correct_sql(
        self,
        sql_error: SQLError,
        schema: Dict[str, Any] = None,
        project_id: str = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Correct a syntactically incorrect SQL query

        Args:
            sql_error: SQLError object containing the SQL and error information
            schema: Database schema information
            project_id: Project identifier for context retrieval
            context: Additional context information

        Returns:
            Dict containing the corrected SQL and metadata
        """
        try:
            # 1. Analyze the error to understand the root cause
            error_analysis = self._analyze_error(sql_error)

            # 2. Retrieve relevant schema context if available
            relevant_context = []
            if project_id and self.vector_store:
                relevant_context = await self.vector_store.similarity_search(
                    query=f"SQL error: {sql_error.error} {sql_error.sql}",
                    collection=f"schema_{project_id}",
                    limit=5
                )

            # 3. Build correction prompt
            prompt = self._build_correction_prompt(
                sql_error,
                schema,
                relevant_context,
                error_analysis
            )

            # 4. Generate corrected SQL
            response = await self.llm.generate(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.1
            )

            # 5. Extract and validate corrected SQL
            corrected_sql = self._extract_corrected_sql(response)

            # 6. Validate the correction
            validation_result = self._validate_correction(
                original_sql=sql_error.sql,
                corrected_sql=corrected_sql,
                schema=schema
            )

            return {
                "corrected_sql": corrected_sql,
                "original_sql": sql_error.sql,
                "original_error": sql_error.error,
                "correction_explanation": self._extract_explanation(response),
                "confidence": validation_result["confidence"],
                "validation_passed": validation_result["passed"],
                "corrections_applied": validation_result["corrections"]
            }

        except Exception as e:
            logger.error(f"SQL correction failed: {str(e)}")
            raise Exception(f"SQL correction failed: {str(e)}")

    def _analyze_error(self, sql_error: SQLError) -> Dict[str, Any]:
        """Analyze the SQL error to understand the root cause"""
        error_lower = sql_error.error.lower()
        sql_lower = sql_error.sql.lower()

        error_patterns = {
            "syntax_error": ["syntax error", "unexpected token", "invalid syntax"],
            "column_not_found": ["column", "doesn't exist", "unknown column"],
            "table_not_found": ["table", "doesn't exist", "unknown table", "relation does not exist"],
            "missing_group_by": ["group by", "not in group by", "aggregate"],
            "unbalanced_parentheses": ["parenthes", "bracket", "missing"],
            "join_error": ["join", "on clause", "ambiguous"],
            "data_type_error": ["type", "conversion", "cast", "invalid type"],
            "missing_from": ["from", "missing from clause"]
        }

        detected_errors = []
        for error_type, patterns in error_patterns.items():
            if any(pattern in error_lower for pattern in patterns):
                detected_errors.append(error_type)

        # Analyze SQL structure
        has_select = "select" in sql_lower
        has_from = "from" in sql_lower
        has_where = "where" in sql_lower
        has_group_by = "group by" in sql_lower
        has_order_by = "order by" in sql_lower

        return {
            "detected_error_types": detected_errors,
            "primary_error_type": detected_errors[0] if detected_errors else "unknown",
            "sql_structure": {
                "has_select": has_select,
                "has_from": has_from,
                "has_where": has_where,
                "has_group_by": has_group_by,
                "has_order_by": has_order_by
            },
            "complexity": self._assess_query_complexity(sql_error.sql)
        }

    def _assess_query_complexity(self, sql: str) -> str:
        """Assess the complexity of the SQL query"""
        sql_lower = sql.lower()
        complexity_indicators = {
            "joins": len(re.findall(r'\bjoin\b', sql_lower)),
            "subqueries": len(re.findall(r'\(.*select.*\)', sql_lower)),
            "aggregates": len(re.findall(r'\b(count|sum|avg|max|min|group_concat)\b', sql_lower)),
            "unions": len(re.findall(r'\bunion\b', sql_lower)),
            "window_functions": len(re.findall(r'\bover\s*\(', sql_lower))
        }

        total_complexity = sum(complexity_indicators.values())

        if total_complexity == 0:
            return "simple"
        elif total_complexity <= 3:
            return "moderate"
        else:
            return "complex"

    def _build_correction_prompt(
        self,
        sql_error: SQLError,
        schema: Dict[str, Any],
        context: List[Dict],
        error_analysis: Dict[str, Any]
    ) -> str:
        """Build the prompt for SQL correction"""

        schema_info = self._format_schema_for_prompt(schema) if schema else "No schema information available"
        context_info = self._format_context_for_prompt(context)

        prompt = f"""
You are an expert SQL debugger. Your task is to fix the syntactically incorrect SQL query below.

### ERROR ANALYSIS ###
Error Type: {error_analysis.get('primary_error_type', 'unknown')}
Detected Issues: {', '.join(error_analysis.get('detected_error_types', []))}
Query Complexity: {error_analysis.get('complexity', 'unknown')}

### ORIGINAL SQL ###
{sql_error.sql}

### ERROR MESSAGE ###
{sql_error.error}

### DATABASE SCHEMA ###
{schema_info}

### RELEVANT CONTEXT ###
{context_info}

### SQL CORRECTION RULES ###
{self.sql_rules}

### CORRECTION INSTRUCTIONS ###
1. Analyze the error message carefully to understand the root cause
2. Use the database schema to ensure all referenced tables and columns exist
3. Apply the SQL rules strictly to generate syntactically correct SQL
4. Preserve the original intent and logic of the query as much as possible
5. Add appropriate safety measures (LIMIT clauses if missing)
6. Ensure the query is read-only (no INSERT, UPDATE, DELETE, DROP, etc.)

### RESPONSE FORMAT ###
Please provide your response in the following format:

CORRECTED_SQL:
[Your corrected SQL query here]

EXPLANATION:
[Brief explanation of what was wrong and how you fixed it]

CHANGES_MADE:
[List of specific changes made to fix the query]
"""

        return prompt

    def _format_schema_for_prompt(self, schema: Dict[str, Any]) -> str:
        """Format schema information for the correction prompt"""
        if not schema or "tables" not in schema:
            return "No schema information available"

        formatted_tables = []
        for table_name, table_info in schema["tables"].items():
            if isinstance(table_info, list):
                columns = ", ".join(table_info)
            elif isinstance(table_info, dict) and "columns" in table_info:
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
        """Format context information for the correction prompt"""
        if not context:
            return "No relevant context available"

        formatted_context = []
        for item in context[:3]:  # Limit to top 3 relevant items
            if isinstance(item, dict):
                formatted_context.append(
                    f"- Related: {item.get('content', str(item))}"
                )

        return "\n".join(formatted_context) if formatted_context else "No relevant context available"

    def _extract_corrected_sql(self, response: str) -> str:
        """Extract the corrected SQL from the LLM response"""
        # Look for CORRECTED_SQL: section
        sql_match = re.search(r'CORRECTED_SQL:\s*(.*?)(?:\n\s*EXPLANATION:|$)', response, re.DOTALL | re.IGNORECASE)
        if sql_match:
            sql = sql_match.group(1).strip()
        else:
            # Fallback: look for SQL blocks
            sql_block_match = re.search(r'```sql\s*(.*?)```', response, re.DOTALL | re.IGNORECASE)
            if sql_block_match:
                sql = sql_block_match.group(1).strip()
            else:
                # Last resort: look for SELECT statements
                select_match = re.search(r'(SELECT.*?);?', response, re.DOTALL | re.IGNORECASE)
                if select_match:
                    sql = select_match.group(1).strip()
                else:
                    raise ValueError("Could not extract corrected SQL from response")

        # Clean up the SQL
        sql = self._clean_sql(sql)
        return sql

    def _clean_sql(self, sql: str) -> str:
        """Clean and validate the corrected SQL"""
        # Remove markdown code blocks if present
        sql = re.sub(r'```sql\s*\n?', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'```\s*\n?', '', sql)

        # Remove extra whitespace
        sql = " ".join(sql.split())

        # Ensure it ends with semicolon
        if not sql.endswith(';'):
            sql += ';'

        # Basic security check
        dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE']
        sql_upper = sql.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                raise ValueError(f"Dangerous SQL keyword detected in correction: {keyword}")

        return sql

    def _extract_explanation(self, response: str) -> str:
        """Extract the explanation from the LLM response"""
        explanation_match = re.search(r'EXPLANATION:\s*(.*?)(?:\n\s*CHANGES_MADE:|$)', response, re.DOTALL | re.IGNORECASE)
        if explanation_match:
            return explanation_match.group(1).strip()

        return "SQL was corrected to fix syntax errors and ensure proper structure."

    def _validate_correction(
        self,
        original_sql: str,
        corrected_sql: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate the corrected SQL"""
        validation_result = {
            "passed": True,
            "confidence": 0.5,
            "corrections": [],
            "issues": []
        }

        try:
            # Check if the corrected SQL is different from original
            if original_sql.strip().lower() == corrected_sql.strip().lower():
                validation_result["issues"].append("No changes were made to the original SQL")
                validation_result["confidence"] = 0.2
            else:
                validation_result["corrections"].append("SQL syntax was modified")
                validation_result["confidence"] += 0.2

            # Check for basic SQL structure
            sql_lower = corrected_sql.lower()
            if 'select' in sql_lower:
                validation_result["confidence"] += 0.1
            if 'from' in sql_lower:
                validation_result["confidence"] += 0.1

            # Check for safety measures
            if 'limit' in sql_lower:
                validation_result["corrections"].append("Added LIMIT clause for safety")
                validation_result["confidence"] += 0.1

            # Check for dangerous operations
            dangerous_keywords = ['insert', 'update', 'delete', 'drop', 'create', 'alter', 'truncate']
            for keyword in dangerous_keywords:
                if keyword in sql_lower:
                    validation_result["passed"] = False
                    validation_result["issues"].append(f"Contains dangerous keyword: {keyword}")
                    validation_result["confidence"] = 0.0

            # Ensure confidence doesn't exceed 1.0
            validation_result["confidence"] = min(validation_result["confidence"], 1.0)

        except Exception as e:
            validation_result["passed"] = False
            validation_result["issues"].append(f"Validation error: {str(e)}")
            validation_result["confidence"] = 0.1

        return validation_result