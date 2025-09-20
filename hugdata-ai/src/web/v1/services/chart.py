import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import json

logger = logging.getLogger("hugdata-ai")


class ChartRequest(BaseModel):
    data: List[Dict[str, Any]]
    columns: List[str]
    query: str
    chart_type: Optional[str] = None


class ChartResponse(BaseModel):
    chart_schema: Dict[str, Any]
    chart_type: str
    confidence: float


class ChartService:
    def __init__(self, llm_provider):
        self.llm_provider = llm_provider

    async def suggest_chart(self, chart_request: ChartRequest) -> ChartResponse:
        """Generate chart suggestions based on data and query context"""

        # Analyze data structure
        data_analysis = self._analyze_data_structure(chart_request.data, chart_request.columns)

        # Generate chart suggestion using LLM
        chart_suggestion = await self._generate_chart_suggestion(
            chart_request.query,
            data_analysis,
            chart_request.chart_type
        )

        # Generate Vega-Lite schema
        vega_schema = await self._generate_vega_lite_schema(
            chart_suggestion["chart_type"],
            data_analysis,
            chart_request.data[:100]  # Sample data for schema generation
        )

        return ChartResponse(
            chart_schema=vega_schema,
            chart_type=chart_suggestion["chart_type"],
            confidence=chart_suggestion["confidence"]
        )

    def _analyze_data_structure(self, data: List[Dict], columns: List[str]) -> Dict[str, Any]:
        """Analyze the structure and types of the data"""
        if not data or not columns:
            return {"error": "No data provided"}

        analysis = {
            "row_count": len(data),
            "column_count": len(columns),
            "columns": {},
            "patterns": {}
        }

        # Analyze each column
        for col in columns:
            values = [row.get(col) for row in data[:100] if row.get(col) is not None]

            if not values:
                continue

            col_analysis = {
                "type": self._infer_column_type(values),
                "unique_count": len(set(str(v) for v in values)),
                "null_count": sum(1 for row in data[:100] if row.get(col) is None),
                "sample_values": values[:5]
            }

            analysis["columns"][col] = col_analysis

        # Identify patterns
        analysis["patterns"] = self._identify_patterns(analysis["columns"])

        return analysis

    def _infer_column_type(self, values: List) -> str:
        """Infer the type of a column based on its values"""
        if not values:
            return "unknown"

        # Check for numeric types
        numeric_count = 0
        date_count = 0

        for value in values:
            str_value = str(value).strip()

            # Check if numeric
            try:
                float(str_value)
                numeric_count += 1
                continue
            except (ValueError, TypeError):
                pass

            # Check if date-like
            if any(char in str_value for char in ['-', '/', ':']):
                date_count += 1

        total = len(values)

        if numeric_count / total > 0.8:
            return "quantitative"
        elif date_count / total > 0.5:
            return "temporal"
        else:
            return "nominal"

    def _identify_patterns(self, columns: Dict[str, Any]) -> Dict[str, Any]:
        """Identify common data patterns for chart recommendations"""
        patterns = {}

        quantitative_cols = [col for col, info in columns.items() if info.get("type") == "quantitative"]
        nominal_cols = [col for col, info in columns.items() if info.get("type") == "nominal"]
        temporal_cols = [col for col, info in columns.items() if info.get("type") == "temporal"]

        patterns["has_time_series"] = len(temporal_cols) > 0
        patterns["quantitative_count"] = len(quantitative_cols)
        patterns["categorical_count"] = len(nominal_cols)
        patterns["suitable_for_scatter"] = len(quantitative_cols) >= 2
        patterns["suitable_for_bar"] = len(quantitative_cols) >= 1 and len(nominal_cols) >= 1
        patterns["suitable_for_line"] = len(temporal_cols) >= 1 and len(quantitative_cols) >= 1

        return patterns

    async def _generate_chart_suggestion(
        self,
        query: str,
        data_analysis: Dict[str, Any],
        preferred_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Use LLM to suggest appropriate chart type"""

        patterns = data_analysis.get("patterns", {})
        columns_info = data_analysis.get("columns", {})

        # Build context for LLM
        context = f"""
        Data Analysis:
        - Row count: {data_analysis.get("row_count", 0)}
        - Columns: {list(columns_info.keys())}
        - Column types: {[(col, info.get("type")) for col, info in columns_info.items()]}
        - Time series data: {patterns.get("has_time_series", False)}
        - Quantitative columns: {patterns.get("quantitative_count", 0)}
        - Categorical columns: {patterns.get("categorical_count", 0)}

        Original query: "{query}"
        """

        if preferred_type:
            context += f"\nPreferred chart type: {preferred_type}"

        prompt = f"""
        Based on the following data analysis and user query, suggest the most appropriate chart type:

        {context}

        Available chart types:
        - bar: For comparing categories
        - line: For showing trends over time
        - scatter: For showing relationships between two quantitative variables
        - pie: For showing parts of a whole
        - histogram: For showing distribution of a single quantitative variable
        - area: For showing trends with emphasis on magnitude

        Respond with JSON format:
        {{
            "chart_type": "suggested_type",
            "reasoning": "explanation of why this chart type is appropriate",
            "confidence": 0.85
        }}
        """

        try:
            # Use the standard LLM provider interface
            response_text = await self.llm_provider.generate(
                prompt=prompt,
                max_tokens=300,
                temperature=0.1
            )

            # Parse JSON response (provider returns a string)
            result = json.loads(response_text)
            return {
                "chart_type": result.get("chart_type", "bar"),
                "reasoning": result.get("reasoning", "Default suggestion"),
                "confidence": float(result.get("confidence", 0.7))
            }

        except Exception as e:
            logger.warning(f"Chart suggestion failed: {e}")
            # Fallback logic
            if patterns.get("has_time_series") and patterns.get("quantitative_count", 0) > 0:
                return {"chart_type": "line", "reasoning": "Time series data detected", "confidence": 0.6}
            elif patterns.get("suitable_for_bar"):
                return {"chart_type": "bar", "reasoning": "Categorical and quantitative data", "confidence": 0.6}
            else:
                return {"chart_type": "bar", "reasoning": "Default fallback", "confidence": 0.4}

    async def _generate_vega_lite_schema(
        self,
        chart_type: str,
        data_analysis: Dict[str, Any],
        sample_data: List[Dict]
    ) -> Dict[str, Any]:
        """Generate Vega-Lite schema for the suggested chart type"""

        columns = data_analysis.get("columns", {})

        # Find appropriate columns for each encoding
        x_field = None
        y_field = None

        # Simple heuristics for field selection
        quantitative_fields = [col for col, info in columns.items() if info.get("type") == "quantitative"]
        nominal_fields = [col for col, info in columns.items() if info.get("type") == "nominal"]
        temporal_fields = [col for col, info in columns.items() if info.get("type") == "temporal"]

        if chart_type == "bar":
            x_field = nominal_fields[0] if nominal_fields else list(columns.keys())[0]
            y_field = quantitative_fields[0] if quantitative_fields else list(columns.keys())[-1]
        elif chart_type == "line":
            x_field = temporal_fields[0] if temporal_fields else nominal_fields[0] if nominal_fields else list(columns.keys())[0]
            y_field = quantitative_fields[0] if quantitative_fields else list(columns.keys())[-1]
        elif chart_type == "scatter":
            x_field = quantitative_fields[0] if len(quantitative_fields) > 0 else list(columns.keys())[0]
            y_field = quantitative_fields[1] if len(quantitative_fields) > 1 else list(columns.keys())[-1]
        else:
            # Default
            x_field = list(columns.keys())[0] if columns else "x"
            y_field = list(columns.keys())[-1] if len(columns) > 1 else "y"

        # Generate basic Vega-Lite schema
        schema = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "description": f"Generated {chart_type} chart",
            "data": {"values": sample_data},
            "mark": {"type": chart_type},
            "encoding": {}
        }

        # Add encodings based on chart type
        if x_field and x_field in columns:
            schema["encoding"]["x"] = {
                "field": x_field,
                "type": columns[x_field].get("type", "nominal")
            }

        if y_field and y_field in columns:
            schema["encoding"]["y"] = {
                "field": y_field,
                "type": columns[y_field].get("type", "quantitative")
            }

        # Chart-specific adjustments
        if chart_type == "pie":
            schema["mark"] = {"type": "arc"}
            schema["encoding"] = {
                "theta": {"field": y_field, "type": "quantitative"},
                "color": {"field": x_field, "type": "nominal"}
            }

        return schema