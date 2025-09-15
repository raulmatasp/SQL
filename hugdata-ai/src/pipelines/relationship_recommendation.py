import logging
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel
from src.providers.llm_provider import LLMProvider

logger = logging.getLogger("hugdata-ai")

class RelationType(Enum):
    """Types of database relationships"""
    MANY_TO_ONE = "MANY_TO_ONE"
    ONE_TO_MANY = "ONE_TO_MANY"
    ONE_TO_ONE = "ONE_TO_ONE"

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls._value2member_map_

@dataclass
class ModelRelationship:
    """Represents a relationship between two models"""
    name: str
    from_model: str
    from_column: str
    type: RelationType
    to_model: str
    to_column: str
    reason: str

class RelationshipRecommendationPipeline:
    """Pipeline for recommending relationships between database models"""

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def recommend_relationships(
        self,
        mdl: Dict[str, Any],
        language: str = "English",
        project_id: str = None
    ) -> Dict[str, Any]:
        """
        Analyze models and suggest appropriate relationships

        Args:
            mdl: Model definition language dictionary containing models
            language: Language for relationship names and reasons
            project_id: Project identifier for context

        Returns:
            Dict containing recommended relationships
        """
        try:
            # 1. Clean and prepare models data
            cleaned_models = self._clean_models(mdl)

            # 2. Validate that we have enough models to recommend relationships
            if len(cleaned_models) < 2:
                return {"relationships": []}

            # 3. Build relationship recommendation prompt
            prompt = self._build_recommendation_prompt(cleaned_models, language)

            # 4. Generate relationship recommendations
            response = await self.llm.generate(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.2
            )

            # 5. Parse and normalize the response
            normalized_response = self._normalize_response(response)

            # 6. Validate relationships against the original models
            validated_relationships = self._validate_relationships(
                normalized_response.get("relationships", []),
                mdl
            )

            return {
                "relationships": validated_relationships,
                "total_recommendations": len(validated_relationships),
                "models_analyzed": len(cleaned_models),
                "language": language
            }

        except Exception as e:
            logger.error(f"Relationship recommendation failed: {str(e)}")
            raise Exception(f"Relationship recommendation failed: {str(e)}")

    def _clean_models(self, mdl: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Clean and prepare models for relationship analysis
        Remove display names and filter out relationship columns
        """
        def remove_display_name(d: Dict[str, Any]) -> Dict[str, Any]:
            if "properties" in d and isinstance(d["properties"], dict):
                d["properties"] = d["properties"].copy()
                d["properties"].pop("displayName", None)
            return d

        def filter_columns(columns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            """Filter out columns that are already relationships"""
            filtered_columns = []
            for column in columns:
                if "relationship" not in column:
                    # Create a copy to avoid modifying the original
                    filtered_column = column.copy()
                    filtered_column = remove_display_name(filtered_column)
                    filtered_columns.append(filtered_column)
            return filtered_columns

        models = mdl.get("models", [])
        cleaned = []

        for model in models:
            cleaned_model = remove_display_name(model.copy())
            cleaned_model["columns"] = filter_columns(model.get("columns", []))
            cleaned.append(cleaned_model)

        return cleaned

    def _build_recommendation_prompt(
        self,
        models: List[Dict[str, Any]],
        language: str
    ) -> str:
        """Build the prompt for relationship recommendations"""

        models_json = json.dumps(models, indent=2)

        prompt = f"""
You are an expert in database schema design and relationship recommendation.

Given the following data models, analyze them and suggest appropriate relationships between them, but only if there are clear and beneficial relationships to recommend.

### MODELS ###
{models_json}

### GUIDELINES ###
1. Do not recommend relationships within the same model (fromModel and toModel must be different)
2. Only suggest relationships if there is a clear and beneficial reason to do so
3. If there are no good relationships to recommend, return an empty list
4. Use "MANY_TO_ONE", "ONE_TO_MANY", or "ONE_TO_ONE" relationship types only
5. Prefer "MANY_TO_ONE" and "ONE_TO_MANY" over "MANY_TO_MANY" relationships
6. Look for common patterns like foreign keys (columns ending in _id, id suffixes)
7. Consider columns with similar names that might reference each other
8. Ensure both models and columns exist before recommending

### RELATIONSHIP CRITERIA ###
- Foreign key relationships (e.g., user_id in orders table → id in users table)
- Common naming patterns (e.g., customer_id, product_id)
- Logical business relationships between entities
- Referential integrity opportunities

### RESPONSE FORMAT ###
Provide your response as a JSON object with this exact structure:

{{
    "relationships": [
        {{
            "name": "descriptive_relationship_name",
            "fromModel": "source_model_name",
            "fromColumn": "source_column_name",
            "type": "MANY_TO_ONE|ONE_TO_MANY|ONE_TO_ONE",
            "toModel": "target_model_name",
            "toColumn": "target_column_name",
            "reason": "clear_explanation_in_{language}"
        }}
    ]
}}

If no relationships are recommended, return:
{{
    "relationships": []
}}

### LANGUAGE ###
Use {language} for the relationship name and reason fields.

### INSTRUCTIONS ###
Analyze the models carefully and suggest optimizations for their relationships. Consider best practices in database design, opportunities for normalization, indexing strategies, and relationships that could improve data integrity and enhance query performance.
"""

        return prompt

    def _normalize_response(self, response: str) -> Dict[str, Any]:
        """Normalize and parse the LLM response"""
        try:
            # Clean up the response
            response = response.strip()

            # Remove any markdown code blocks
            response = response.replace("```json", "").replace("```", "")

            # Try to find JSON in the response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # If no JSON found, return empty relationships
                return {"relationships": []}

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return {"relationships": []}
        except Exception as e:
            logger.error(f"Error normalizing response: {e}")
            return {"relationships": []}

    def _validate_relationships(
        self,
        relationships: List[Dict[str, Any]],
        original_mdl: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Validate relationships against the original model definition
        Ensure models and columns exist and relationships are valid
        """
        # Build model-column mapping for validation
        model_columns = {}
        for model in original_mdl.get("models", []):
            model_name = model.get("name")
            if model_name:
                columns = set()
                for column in model.get("columns", []):
                    if isinstance(column, dict) and "name" in column:
                        # Only include non-relationship columns
                        if "relationship" not in column:
                            columns.add(column["name"])
                    elif isinstance(column, str):
                        columns.add(column)
                model_columns[model_name] = columns

        validated_relationships = []

        for relationship in relationships:
            if not isinstance(relationship, dict):
                continue

            # Check required fields
            required_fields = ["name", "fromModel", "fromColumn", "type", "toModel", "toColumn", "reason"]
            if not all(field in relationship for field in required_fields):
                logger.warning(f"Relationship missing required fields: {relationship}")
                continue

            # Validate relationship type
            if not RelationType.is_valid(relationship.get("type")):
                logger.warning(f"Invalid relationship type: {relationship.get('type')}")
                continue

            # Validate models exist
            from_model = relationship.get("fromModel")
            to_model = relationship.get("toModel")

            if from_model not in model_columns:
                logger.warning(f"From model '{from_model}' not found in schema")
                continue

            if to_model not in model_columns:
                logger.warning(f"To model '{to_model}' not found in schema")
                continue

            # Validate columns exist
            from_column = relationship.get("fromColumn")
            to_column = relationship.get("toColumn")

            if from_column not in model_columns[from_model]:
                logger.warning(f"From column '{from_column}' not found in model '{from_model}'")
                continue

            if to_column not in model_columns[to_model]:
                logger.warning(f"To column '{to_column}' not found in model '{to_model}'")
                continue

            # Validate that it's not a self-relationship
            if from_model == to_model:
                logger.warning(f"Self-relationship detected and rejected: {from_model}")
                continue

            # All validations passed
            validated_relationships.append({
                "name": relationship["name"],
                "fromModel": from_model,
                "fromColumn": from_column,
                "type": relationship["type"],
                "toModel": to_model,
                "toColumn": to_column,
                "reason": relationship["reason"]
            })

        logger.info(f"Validated {len(validated_relationships)} out of {len(relationships)} recommended relationships")
        return validated_relationships

    def analyze_model_complexity(self, mdl: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the complexity of the model structure to help with relationship recommendations
        """
        models = mdl.get("models", [])

        analysis = {
            "total_models": len(models),
            "total_columns": 0,
            "potential_foreign_keys": [],
            "naming_patterns": {},
            "model_sizes": {}
        }

        # Analyze each model
        for model in models:
            model_name = model.get("name", "unknown")
            columns = model.get("columns", [])

            model_column_count = len([col for col in columns if "relationship" not in col])
            analysis["total_columns"] += model_column_count
            analysis["model_sizes"][model_name] = model_column_count

            # Look for potential foreign key patterns
            for column in columns:
                if isinstance(column, dict) and "name" in column:
                    col_name = column["name"]

                    # Look for ID patterns
                    if col_name.endswith("_id") or col_name == "id":
                        analysis["potential_foreign_keys"].append({
                            "model": model_name,
                            "column": col_name,
                            "pattern": "id_suffix" if col_name.endswith("_id") else "primary_key"
                        })

                    # Track naming patterns
                    if "_" in col_name:
                        prefix = col_name.split("_")[0]
                        if prefix not in analysis["naming_patterns"]:
                            analysis["naming_patterns"][prefix] = []
                        analysis["naming_patterns"][prefix].append({
                            "model": model_name,
                            "column": col_name
                        })

        return analysis