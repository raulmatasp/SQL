import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from .base import BaseService
from src.pipelines.relationship_recommendation import RelationshipRecommendationPipeline

logger = logging.getLogger("hugdata-ai")

class RelationshipRecommendationService(BaseService):
    """Service for handling relationship recommendation requests"""

    def __init__(self, llm_provider, vector_store, embeddings_provider):
        super().__init__(llm_provider, vector_store, embeddings_provider)
        self.pipeline = RelationshipRecommendationPipeline(llm_provider)
        self.recommendations: Dict[str, Dict[str, Any]] = {}

    def initialize_recommendation(self, recommendation_id: str) -> None:
        """Initialize a new recommendation event"""
        self.recommendations[recommendation_id] = {
            "id": recommendation_id,
            "status": "generating",
            "created_at": datetime.utcnow().isoformat(),
            "response": None,
            "error": None,
            "trace_id": None
        }

    async def recommend_relationships(
        self,
        recommendation_id: str,
        mdl: str,
        project_id: Optional[str] = None,
        language: str = "English",
        configurations: Optional[dict] = None
    ) -> None:
        """
        Perform relationship recommendations asynchronously

        Args:
            recommendation_id: Recommendation identifier
            mdl: Model definition language string
            project_id: Project identifier for context
            language: Language for relationship names and descriptions
            configurations: Additional configuration options
        """
        try:
            logger.info(f"Starting relationship recommendation for {recommendation_id}")

            # Update recommendation status
            if recommendation_id in self.recommendations:
                self.recommendations[recommendation_id]["status"] = "generating"

            # Parse MDL
            try:
                mdl_dict = json.loads(mdl)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid MDL JSON: {str(e)}")

            # Perform relationship recommendation
            recommendation_result = await self.pipeline.recommend_relationships(
                mdl=mdl_dict,
                language=language,
                project_id=project_id
            )

            # Update recommendation with successful result
            if recommendation_id in self.recommendations:
                self.recommendations[recommendation_id].update({
                    "status": "finished",
                    "response": {
                        "relationships": recommendation_result["relationships"],
                        "total_recommendations": recommendation_result["total_recommendations"],
                        "models_analyzed": recommendation_result["models_analyzed"],
                        "language": recommendation_result["language"],
                        "project_id": project_id,
                        "configurations": configurations
                    },
                    "completed_at": datetime.utcnow().isoformat()
                })

            logger.info(f"Relationship recommendation completed successfully for {recommendation_id}")

        except Exception as e:
            logger.error(f"Relationship recommendation failed for {recommendation_id}: {str(e)}")

            # Update recommendation with error
            if recommendation_id in self.recommendations:
                self.recommendations[recommendation_id].update({
                    "status": "failed",
                    "error": {
                        "message": str(e),
                        "type": type(e).__name__
                    },
                    "completed_at": datetime.utcnow().isoformat()
                })

    async def analyze_model_complexity(
        self,
        mdl: str,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze model complexity for relationship recommendations

        Args:
            mdl: Model definition language string
            project_id: Project identifier for context

        Returns:
            Model complexity analysis
        """
        try:
            # Parse MDL
            mdl_dict = json.loads(mdl)

            # Perform complexity analysis
            analysis = self.pipeline.analyze_model_complexity(mdl_dict)

            return {
                "complexity_analysis": analysis,
                "project_id": project_id,
                "analyzed_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Model complexity analysis failed: {str(e)}")
            raise

    async def validate_relationships(
        self,
        mdl: str,
        relationships: List[Dict[str, Any]],
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate relationships against the model

        Args:
            mdl: Model definition language string
            relationships: List of relationships to validate
            project_id: Project identifier for context

        Returns:
            Validation results
        """
        try:
            # Parse MDL
            mdl_dict = json.loads(mdl)

            # Validate relationships using the pipeline's validation logic
            validated_relationships = self.pipeline._validate_relationships(
                relationships,
                mdl_dict
            )

            # Calculate validation statistics
            total_proposed = len(relationships)
            total_valid = len(validated_relationships)
            validation_rate = total_valid / total_proposed if total_proposed > 0 else 0

            # Identify invalid relationships
            valid_relationship_names = {rel["name"] for rel in validated_relationships}
            invalid_relationships = [
                rel for rel in relationships
                if rel.get("name") not in valid_relationship_names
            ]

            return {
                "validation_results": {
                    "total_proposed": total_proposed,
                    "total_valid": total_valid,
                    "validation_rate": round(validation_rate, 2),
                    "valid_relationships": validated_relationships,
                    "invalid_relationships": invalid_relationships
                },
                "project_id": project_id,
                "validated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Relationship validation failed: {str(e)}")
            raise

    def get_recommendation_status(self, recommendation_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a recommendation"""
        return self.recommendations.get(recommendation_id)

    def delete_recommendation(self, recommendation_id: str) -> bool:
        """Delete a recommendation"""
        if recommendation_id in self.recommendations:
            del self.recommendations[recommendation_id]
            return True
        return False

    def list_recommendations(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List recommendations with optional filtering

        Args:
            project_id: Filter by project ID
            status: Filter by status
            limit: Maximum number of recommendations to return

        Returns:
            List of recommendations
        """
        recommendations = list(self.recommendations.values())

        # Apply filters
        if status:
            recommendations = [rec for rec in recommendations if rec.get("status") == status]

        if project_id:
            # Filter by project_id in response if available
            filtered_recommendations = []
            for rec in recommendations:
                response = rec.get("response", {})
                if response.get("project_id") == project_id:
                    filtered_recommendations.append(rec)
            recommendations = filtered_recommendations

        # Sort by creation time (newest first)
        recommendations.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # Apply limit
        return recommendations[:limit]

    def get_statistics(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about relationship recommendations

        Args:
            project_id: Optional project ID filter

        Returns:
            Statistics dictionary
        """
        recommendations = list(self.recommendations.values())

        # Filter by project if specified
        if project_id:
            filtered_recommendations = []
            for rec in recommendations:
                response = rec.get("response", {})
                if response.get("project_id") == project_id:
                    filtered_recommendations.append(rec)
            recommendations = filtered_recommendations

        total_recommendations = len(recommendations)
        successful_recommendations = len([r for r in recommendations if r.get("status") == "finished"])
        failed_recommendations = len([r for r in recommendations if r.get("status") == "failed"])
        in_progress_recommendations = len([r for r in recommendations if r.get("status") == "generating"])

        # Calculate success rate
        success_rate = 0.0
        if total_recommendations > 0:
            completed_recommendations = successful_recommendations + failed_recommendations
            if completed_recommendations > 0:
                success_rate = successful_recommendations / completed_recommendations

        # Calculate average relationships per recommendation
        total_relationships = 0
        for rec in recommendations:
            if rec.get("status") == "finished":
                response = rec.get("response", {})
                total_relationships += response.get("total_recommendations", 0)

        avg_relationships = 0.0
        if successful_recommendations > 0:
            avg_relationships = total_relationships / successful_recommendations

        return {
            "total_recommendations": total_recommendations,
            "successful_recommendations": successful_recommendations,
            "failed_recommendations": failed_recommendations,
            "in_progress_recommendations": in_progress_recommendations,
            "success_rate": round(success_rate, 2),
            "total_relationships_generated": total_relationships,
            "average_relationships_per_recommendation": round(avg_relationships, 1),
            "project_id": project_id
        }

    async def cleanup_old_recommendations(self, max_age_hours: int = 24) -> int:
        """
        Clean up old recommendation events

        Args:
            max_age_hours: Maximum age of recommendations to keep

        Returns:
            Number of recommendations cleaned up
        """
        try:
            from datetime import datetime, timedelta

            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            cutoff_iso = cutoff_time.isoformat()

            recommendations_to_remove = []
            for recommendation_id, recommendation_data in self.recommendations.items():
                created_at = recommendation_data.get("created_at", "")
                if created_at < cutoff_iso:
                    recommendations_to_remove.append(recommendation_id)

            # Remove old recommendations
            for recommendation_id in recommendations_to_remove:
                del self.recommendations[recommendation_id]

            logger.info(f"Cleaned up {len(recommendations_to_remove)} old recommendations")
            return len(recommendations_to_remove)

        except Exception as e:
            logger.error(f"Failed to cleanup old recommendations: {str(e)}")
            return 0

    async def export_relationships(
        self,
        recommendation_id: str,
        format: str = "json"
    ) -> Optional[Dict[str, Any]]:
        """
        Export relationships from a recommendation

        Args:
            recommendation_id: Recommendation ID to export
            format: Export format (json, sql, etc.)

        Returns:
            Exported relationships data
        """
        try:
            recommendation = self.recommendations.get(recommendation_id)
            if not recommendation or recommendation.get("status") != "finished":
                return None

            response = recommendation.get("response", {})
            relationships = response.get("relationships", [])

            if format.lower() == "json":
                return {
                    "relationships": relationships,
                    "metadata": {
                        "recommendation_id": recommendation_id,
                        "total_relationships": len(relationships),
                        "language": response.get("language", "English"),
                        "exported_at": datetime.utcnow().isoformat()
                    }
                }

            elif format.lower() == "sql":
                # Generate SQL DDL for creating relationships
                sql_statements = []
                for rel in relationships:
                    sql = f"""
-- Relationship: {rel['name']}
-- Reason: {rel['reason']}
ALTER TABLE {rel['fromModel']}
ADD CONSTRAINT fk_{rel['fromModel']}_{rel['fromColumn']}
FOREIGN KEY ({rel['fromColumn']})
REFERENCES {rel['toModel']}({rel['toColumn']});
"""
                    sql_statements.append(sql.strip())

                return {
                    "sql_statements": sql_statements,
                    "metadata": {
                        "recommendation_id": recommendation_id,
                        "total_statements": len(sql_statements),
                        "exported_at": datetime.utcnow().isoformat()
                    }
                }

            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            logger.error(f"Failed to export relationships: {str(e)}")
            return None