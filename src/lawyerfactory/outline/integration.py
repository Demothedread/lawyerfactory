"""
# Script Name: integration.py
# Description: Maestro Skeletal Outline Bot - Phase 4 Integration Integrates skeletal outline generation into the Maestro orchestration workflow. This bot operates during the OUTLINE phase of the 7-phase workflow.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
Maestro Skeletal Outline Bot - Phase 4 Integration
Integrates skeletal outline generation into the Maestro orchestration workflow.
This bot operates during the OUTLINE phase of the 7-phase workflow.
"""

import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional

from lawyerfactory.claims.matrix import ComprehensiveClaimsMatrixIntegration
from lawyerfactory.kg.enhanced_graph import EnhancedKnowledgeGraph
from lawyerfactory.outline.integration_legacy import SkeletalOutlineIntegration
from lawyerfactory.phases.phaseA01_intake.evidence_routes import EvidenceAPI

logger = logging.getLogger(__name__)


@dataclass
class OutlineTask:
    """Task definition for skeletal outline generation"""

    task_id: str
    case_id: str
    session_id: str
    document_type: str = "complaint"
    jurisdiction: str = "California"
    priority: int = 1
    estimated_duration: int = 300  # 5 minutes
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = ["statement_of_facts", "claims_matrix"]


@dataclass
class OutlineResult:
    """Result from skeletal outline generation"""

    task_id: str
    workflow_id: str
    success: bool
    outline_id: Optional[str] = None
    sections_generated: int = 0
    word_count: int = 0
    estimated_pages: int = 0
    rule_12b6_compliance_score: float = 0.0
    generation_time_seconds: float = 0.0
    final_document_path: Optional[str] = None
    error_message: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class MaestroSkeletalOutlineBot:
    """Skeletal outline generation bot for Maestro orchestration"""

    def __init__(
        self,
        enhanced_kg: EnhancedKnowledgeGraph,
        claims_matrix: ComprehensiveClaimsMatrixIntegration,
        evidence_api: EvidenceAPI,
        llm_service=None,
    ):

        self.kg = enhanced_kg
        self.claims_matrix = claims_matrix
        self.evidence_api = evidence_api
        self.llm_service = llm_service

        # Initialize skeletal outline system
        self.outline_integration = SkeletalOutlineIntegration(
            enhanced_kg, claims_matrix, evidence_api, llm_service
        )

        # Bot metadata
        self.bot_name = "SkeletalOutlineBot"
        self.bot_version = "1.0.0"
        self.supported_document_types = ["complaint", "motion", "brief"]

        logger.info(f"Maestro Skeletal Outline Bot v{self.bot_version} initialized")

    async def execute_task(self, task: OutlineTask, context: Dict[str, Any]) -> OutlineResult:
        """Execute skeletal outline generation task"""
        try:
            logger.info(f"Executing outline task {task.task_id} for case {task.case_id}")

            # Validate prerequisites
            validation_result = await self._validate_prerequisites(task, context)
            if not validation_result["valid"]:
                return OutlineResult(
                    task_id=task.task_id,
                    workflow_id="",
                    success=False,
                    error_message=validation_result["error"],
                    warnings=validation_result.get("warnings", []),
                )

            # Start skeletal outline workflow
            workflow_id = await self.outline_integration.start_skeletal_outline_workflow(
                task.case_id, task.session_id, task.document_type
            )

            # Wait for completion (with timeout)
            result = await self._wait_for_completion(workflow_id, timeout_seconds=600)

            # Package results for Maestro
            outline_result = self._package_results(task.task_id, workflow_id, result)

            logger.info(f"Outline task {task.task_id} completed: {outline_result.success}")
            return outline_result

        except Exception as e:
            logger.exception(f"Outline task {task.task_id} failed: {e}")
            return OutlineResult(
                task_id=task.task_id,
                workflow_id="",
                success=False,
                error_message=str(e),
            )

    async def _validate_prerequisites(
        self, task: OutlineTask, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that prerequisites are met for outline generation"""
        validation = {"valid": True, "error": None, "warnings": []}

        try:
            # Check if claims matrix session exists
            if task.session_id not in self.claims_matrix.active_sessions:
                validation["valid"] = False
                validation["error"] = f"Claims matrix session {task.session_id} not found"
                return validation

            # Check if evidence table has data
            evidence_stats = self.evidence_api.evidence_table.get_stats()
            if evidence_stats.get("total_evidence_entries", 0) == 0:
                validation["warnings"].append(
                    "No evidence entries found - document may lack supporting evidence"
                )

            if evidence_stats.get("total_fact_assertions", 0) == 0:
                validation["warnings"].append(
                    "No fact assertions found - document may lack factual foundation"
                )

            # Check claims matrix analysis
            session = self.claims_matrix.active_sessions[task.session_id]
            if not session.current_element:
                validation["warnings"].append(
                    "Claims matrix analysis incomplete - may affect element coverage"
                )

            # Validate document type
            if task.document_type not in self.supported_document_types:
                validation["warnings"].append(
                    f"Document type '{task.document_type}' not fully supported"
                )

            # Check jurisdiction support
            supported_jurisdictions = ["California", "Federal", "New York"]
            if task.jurisdiction not in supported_jurisdictions:
                validation["warnings"].append(
                    f"Limited support for jurisdiction '{task.jurisdiction}'"
                )

        except Exception as e:
            logger.error(f"Prerequisites validation failed: {e}")
            validation["valid"] = False
            validation["error"] = f"Validation error: {str(e)}"

        return validation

    async def _wait_for_completion(
        self, workflow_id: str, timeout_seconds: int = 600
    ) -> Dict[str, Any]:
        """Wait for workflow completion with timeout"""
        start_time = datetime.now()
        check_interval = 5  # seconds

        while (datetime.now() - start_time).total_seconds() < timeout_seconds:
            status = self.outline_integration.get_workflow_status(workflow_id)

            if not status:
                return {"success": False, "error": "Workflow not found"}

            if status["status"] == "completed":
                return {"success": True, "status": status}
            elif status["status"] == "failed":
                return {
                    "success": False,
                    "error": status.get("error_message", "Unknown error"),
                }

            # Still generating - wait and check again
            await asyncio.sleep(check_interval)

        # Timeout reached
        return {
            "success": False,
            "error": f"Workflow timeout after {timeout_seconds} seconds",
        }

    def _package_results(
        self, task_id: str, workflow_id: str, result: Dict[str, Any]
    ) -> OutlineResult:
        """Package workflow results for Maestro consumption"""
        if not result["success"]:
            return OutlineResult(
                task_id=task_id,
                workflow_id=workflow_id,
                success=False,
                error_message=result.get("error", "Unknown error"),
            )

        status = result["status"]
        generation_results = status.get("generation_results", {})
        outline_summary = status.get("outline_summary", {})

        # Determine document path
        document_path = None
        if generation_results.get("success"):
            document_path = f"skeletal_outlines/{workflow_id}_complaint.txt"

        return OutlineResult(
            task_id=task_id,
            workflow_id=workflow_id,
            success=generation_results.get("success", False),
            outline_id=outline_summary.get("outline_id"),
            sections_generated=generation_results.get("sections_generated", 0),
            word_count=generation_results.get("word_count", 0),
            estimated_pages=generation_results.get("estimated_pages", 0),
            rule_12b6_compliance_score=generation_results.get("rule_12b6_compliance_score", 0.0),
            generation_time_seconds=generation_results.get("generation_time_seconds", 0.0),
            final_document_path=document_path,
            warnings=generation_results.get("warnings", []),
        )

    def get_task_capabilities(self) -> Dict[str, Any]:
        """Return bot capabilities for Maestro task assignment"""
        return {
            "bot_name": self.bot_name,
            "bot_version": self.bot_version,
            "supported_phases": ["OUTLINE"],
            "supported_document_types": self.supported_document_types,
            "task_types": ["skeletal_outline_generation"],
            "dependencies": ["claims_matrix", "evidence_table"],
            "estimated_duration_minutes": 5,
            "concurrent_tasks_supported": 3,
            "resource_requirements": {
                "memory_mb": 512,
                "cpu_cores": 1,
                "disk_space_mb": 100,
            },
        }

    async def get_progress_update(self, workflow_id: str) -> Dict[str, Any]:
        """Get progress update for active workflow"""
        try:
            status = self.outline_integration.get_workflow_status(workflow_id)
            if not status:
                return {"error": "Workflow not found"}

            progress_data = {
                "workflow_id": workflow_id,
                "status": status["status"],
                "progress_percentage": self._calculate_progress_percentage(status),
                "current_step": self._get_current_step(status),
                "estimated_completion": self._estimate_completion_time(status),
                "sections_completed": 0,
                "total_sections": 0,
            }

            # Add section progress if available
            outline_summary = status.get("outline_summary", {})
            if outline_summary:
                progress_data["total_sections"] = outline_summary.get("section_count", 0)

            generation_results = status.get("generation_results", {})
            if generation_results:
                progress_data["sections_completed"] = generation_results.get(
                    "sections_generated", 0
                )

            return progress_data

        except Exception as e:
            logger.error(f"Failed to get progress update: {e}")
            return {"error": str(e)}

    def _calculate_progress_percentage(self, status: Dict[str, Any]) -> float:
        """Calculate progress percentage based on status"""
        if status["status"] == "completed":
            return 100.0
        elif status["status"] == "failed":
            return 0.0
        elif status["status"] == "generating":
            # Estimate based on time elapsed (rough approximation)
            if status.get("created_at"):
                try:
                    created = datetime.fromisoformat(status["created_at"].replace("Z", "+00:00"))
                    elapsed = (datetime.now() - created.replace(tzinfo=None)).total_seconds()
                    # Assume 5 minute average generation time
                    return min(90.0, (elapsed / 300) * 90)  # Cap at 90% until confirmed complete
                except:
                    pass
            return 10.0  # Default progress for generating state
        else:
            return 0.0

    def _get_current_step(self, status: Dict[str, Any]) -> str:
        """Determine current step based on status"""
        if status["status"] == "generating":
            return "Generating skeletal outline and prompts"
        elif status["status"] == "completed":
            return "Skeletal outline generation complete"
        elif status["status"] == "failed":
            return "Generation failed"
        else:
            return "Initializing"

    def _estimate_completion_time(self, status: Dict[str, Any]) -> Optional[str]:
        """Estimate completion time"""
        if status["status"] in ["completed", "failed"]:
            return None

        if status.get("created_at"):
            try:
                created = datetime.fromisoformat(status["created_at"].replace("Z", "+00:00"))
                elapsed = (datetime.now() - created.replace(tzinfo=None)).total_seconds()
                # Estimate 5 minutes total, subtract elapsed time
                remaining = max(0, 300 - elapsed)
                completion = datetime.now().timestamp() + remaining
                return datetime.fromtimestamp(completion).isoformat()
            except:
                pass

        # Default to 5 minutes from now
        completion = datetime.now().timestamp() + 300
        return datetime.fromtimestamp(completion).isoformat()

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel active workflow (if supported)"""
        try:
            # For now, just remove from active workflows
            # In production, would need to actually stop async processing
            if workflow_id in self.outline_integration.active_workflows:
                workflow = self.outline_integration.active_workflows[workflow_id]
                workflow.status = "cancelled"
                workflow.completed_at = datetime.now()
                workflow.error_message = "Cancelled by user request"
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to cancel workflow {workflow_id}: {e}")
            return False

    def get_bot_health(self) -> Dict[str, Any]:
        """Get bot health status for monitoring"""
        try:
            active_workflows = len(self.outline_integration.active_workflows)
            completed_workflows = len(
                [
                    wf
                    for wf in self.outline_integration.active_workflows.values()
                    if wf.status == "completed"
                ]
            )
            failed_workflows = len(
                [
                    wf
                    for wf in self.outline_integration.active_workflows.values()
                    if wf.status == "failed"
                ]
            )

            return {
                "bot_name": self.bot_name,
                "status": "healthy",
                "active_workflows": active_workflows,
                "completed_workflows": completed_workflows,
                "failed_workflows": failed_workflows,
                "success_rate": completed_workflows / max(1, active_workflows) * 100,
                "last_health_check": datetime.now().isoformat(),
                "memory_usage_mb": 0,  # Would implement actual memory monitoring
                "cpu_usage_percent": 0,  # Would implement actual CPU monitoring
            }

        except Exception as e:
            return {
                "bot_name": self.bot_name,
                "status": "unhealthy",
                "error": str(e),
                "last_health_check": datetime.now().isoformat(),
            }


async def test_maestro_skeletal_outline_bot():
    """Test the Maestro skeletal outline bot"""
    try:
        from lawyerfactory.claims.matrix import ComprehensiveClaimsMatrixIntegration
        from lawyerfactory.kg.enhanced_graph import EnhancedKnowledgeGraph
        from lawyerfactory.phases.phaseA01_intake.evidence_routes import EvidenceAPI

        # Initialize components
        kg = EnhancedKnowledgeGraph()
        claims_matrix = ComprehensiveClaimsMatrixIntegration(kg)
        evidence_api = EvidenceAPI()

        # Create bot
        bot = MaestroSkeletalOutlineBot(kg, claims_matrix, evidence_api)

        # Test capabilities
        capabilities = bot.get_task_capabilities()
        print(f"Bot capabilities: {json.dumps(capabilities, indent=2)}")

        # Test health check
        health = bot.get_bot_health()
        print(f"Bot health: {json.dumps(health, indent=2)}")

        # Create test task
        task = OutlineTask(
            task_id="test_outline_task_001",
            case_id="test_case_001",
            session_id="test_session_001",
        )

        # Test task execution (this will fail without proper setup, but tests the flow)
        print("Testing task execution...")
        result = await bot.execute_task(task, {})
        print(f"Task result: {json.dumps(asdict(result), indent=2)}")

        return bot

    except Exception as e:
        print(f"Test failed: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(test_maestro_skeletal_outline_bot())
