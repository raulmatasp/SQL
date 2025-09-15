import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from .base import BaseService
from src.pipelines.sql_correction import SQLCorrectionPipeline, SQLError

logger = logging.getLogger("hugdata-ai")

class SqlCorrectionService(BaseService):
    """Service for handling SQL correction requests"""

    def __init__(self, llm_provider, vector_store, embeddings_provider):
        super().__init__(llm_provider, vector_store, embeddings_provider)
        self.pipeline = SQLCorrectionPipeline(llm_provider, vector_store)
        self.events: Dict[str, Dict[str, Any]] = {}

    def initialize_event(self, event_id: str) -> None:
        """Initialize a new correction event"""
        self.events[event_id] = {
            "event_id": event_id,
            "status": "correcting",
            "created_at": datetime.utcnow().isoformat(),
            "response": None,
            "error": None,
            "trace_id": None,
            "invalid_sql": None
        }

    async def correct_sql(
        self,
        event_id: str,
        sql: str,
        error: str,
        project_id: Optional[str] = None,
        retrieved_tables: Optional[List[str]] = None,
        use_dry_plan: bool = False,
        allow_dry_plan_fallback: bool = True
    ) -> None:
        """
        Perform SQL correction asynchronously

        Args:
            event_id: Event identifier
            sql: Original SQL query with errors
            error: Error message from SQL execution
            project_id: Project identifier for context
            retrieved_tables: List of tables to consider
            use_dry_plan: Whether to use dry plan validation
            allow_dry_plan_fallback: Whether to allow fallback to dry plan
        """
        try:
            logger.info(f"Starting SQL correction for event {event_id}")

            # Update event status
            if event_id in self.events:
                self.events[event_id]["status"] = "correcting"
                self.events[event_id]["invalid_sql"] = sql

            # Create SQL error object
            sql_error = SQLError(
                sql=sql,
                error=error,
                error_type=self._determine_error_type(error)
            )

            # Get schema context if project_id is provided
            schema = None
            if project_id:
                schema = await self._get_project_schema(project_id)

            # Prepare context
            context = {
                "project_id": project_id,
                "retrieved_tables": retrieved_tables,
                "use_dry_plan": use_dry_plan,
                "allow_dry_plan_fallback": allow_dry_plan_fallback
            }

            # Perform correction
            correction_result = await self.pipeline.correct_sql(
                sql_error=sql_error,
                schema=schema,
                project_id=project_id,
                context=context
            )

            # Update event with successful result
            if event_id in self.events:
                self.events[event_id].update({
                    "status": "finished",
                    "response": {
                        "corrected_sql": correction_result["corrected_sql"],
                        "original_sql": correction_result["original_sql"],
                        "original_error": correction_result["original_error"],
                        "correction_explanation": correction_result["correction_explanation"],
                        "confidence": correction_result["confidence"],
                        "validation_passed": correction_result["validation_passed"],
                        "corrections_applied": correction_result["corrections_applied"]
                    },
                    "completed_at": datetime.utcnow().isoformat()
                })

            logger.info(f"SQL correction completed successfully for event {event_id}")

        except Exception as e:
            logger.error(f"SQL correction failed for event {event_id}: {str(e)}")

            # Update event with error
            if event_id in self.events:
                self.events[event_id].update({
                    "status": "failed",
                    "error": {
                        "message": str(e),
                        "type": type(e).__name__
                    },
                    "completed_at": datetime.utcnow().isoformat()
                })

    def _determine_error_type(self, error: str) -> str:
        """Determine the type of SQL error"""
        error_lower = error.lower()

        if any(phrase in error_lower for phrase in ["syntax error", "unexpected token"]):
            return "syntax_error"
        elif any(phrase in error_lower for phrase in ["column", "doesn't exist", "unknown column"]):
            return "column_not_found"
        elif any(phrase in error_lower for phrase in ["table", "doesn't exist", "unknown table"]):
            return "table_not_found"
        elif "group by" in error_lower:
            return "missing_group_by"
        elif any(phrase in error_lower for phrase in ["join", "on clause"]):
            return "join_error"
        else:
            return "unknown"

    async def _get_project_schema(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get schema information for a project"""
        try:
            # Search for schema information in vector store
            results = await self.vector_store.similarity_search(
                query="database schema table structure",
                collection=f"schema_{project_id}",
                limit=10
            )

            if results:
                # Build schema from search results
                schema = {"tables": {}}
                for result in results:
                    metadata = result.get("metadata", {})
                    table_name = metadata.get("table_name")
                    if table_name:
                        if table_name not in schema["tables"]:
                            schema["tables"][table_name] = []

                        column_name = metadata.get("column_name")
                        if column_name and column_name not in schema["tables"][table_name]:
                            schema["tables"][table_name].append(column_name)

                return schema

        except Exception as e:
            logger.warning(f"Failed to get schema for project {project_id}: {str(e)}")

        return None

    def get_event_status(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a correction event"""
        return self.events.get(event_id)

    def delete_event(self, event_id: str) -> bool:
        """Delete a correction event"""
        if event_id in self.events:
            del self.events[event_id]
            return True
        return False

    def list_events(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List correction events with optional filtering

        Args:
            project_id: Filter by project ID
            status: Filter by status
            limit: Maximum number of events to return

        Returns:
            List of correction events
        """
        events = list(self.events.values())

        # Apply filters
        if status:
            events = [event for event in events if event.get("status") == status]

        # Sort by creation time (newest first)
        events.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # Apply limit
        return events[:limit]

    def get_statistics(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about SQL corrections

        Args:
            project_id: Optional project ID filter

        Returns:
            Statistics dictionary
        """
        events = list(self.events.values())

        total_corrections = len(events)
        successful_corrections = len([e for e in events if e.get("status") == "finished"])
        failed_corrections = len([e for e in events if e.get("status") == "failed"])
        in_progress_corrections = len([e for e in events if e.get("status") == "correcting"])

        # Calculate success rate
        success_rate = 0.0
        if total_corrections > 0:
            completed_corrections = successful_corrections + failed_corrections
            if completed_corrections > 0:
                success_rate = successful_corrections / completed_corrections

        return {
            "total_corrections": total_corrections,
            "successful_corrections": successful_corrections,
            "failed_corrections": failed_corrections,
            "in_progress_corrections": in_progress_corrections,
            "success_rate": round(success_rate, 2),
            "project_id": project_id
        }

    async def cleanup_old_events(self, max_age_hours: int = 24) -> int:
        """
        Clean up old correction events

        Args:
            max_age_hours: Maximum age of events to keep

        Returns:
            Number of events cleaned up
        """
        try:
            from datetime import datetime, timedelta

            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            cutoff_iso = cutoff_time.isoformat()

            events_to_remove = []
            for event_id, event_data in self.events.items():
                created_at = event_data.get("created_at", "")
                if created_at < cutoff_iso:
                    events_to_remove.append(event_id)

            # Remove old events
            for event_id in events_to_remove:
                del self.events[event_id]

            logger.info(f"Cleaned up {len(events_to_remove)} old correction events")
            return len(events_to_remove)

        except Exception as e:
            logger.error(f"Failed to cleanup old events: {str(e)}")
            return 0