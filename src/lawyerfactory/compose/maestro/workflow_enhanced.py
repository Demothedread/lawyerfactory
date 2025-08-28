"""
# Script Name: workflow_enhanced.py
# Description: Enhanced workflow management for LawyerFactory. Integrates with the new maestro orchestration system while maintaining compatibility.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: orchestration
Enhanced workflow management for LawyerFactory.
Integrates with the new maestro orchestration system while maintaining compatibility.
"""

import asyncio
from itertools import islice
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional
import uuid  # <-- added import

# Ensure src root is on sys.path so imports from src.* resolve when this module is executed from different CWDs.
project_root = Path(__file__).resolve().parents[2]
src_root = project_root
# Ensure src root is first on sys.path so imports like `from knowledge_graph import ...` resolve
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from maestro.enhanced_maestro import EnhancedMaestro
from maestro.workflow_models import PhaseStatus, WorkflowPhase

from knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class EnhancedWorkflowManager:
    """Enhanced workflow manager that coordinates with the maestro orchestration"""

    def __init__(
        self,
        knowledge_graph_path: str = "knowledge_graph.db",
        storage_path: str = "workflow_storage",
    ):
        """Initialize the enhanced workflow manager"""
        self.knowledge_graph = KnowledgeGraph(knowledge_graph_path)
        self.maestro = EnhancedMaestro(
            knowledge_graph=self.knowledge_graph, storage_path=storage_path
        )
        self.active_sessions: Dict[str, str] = {}  # case_name -> session_id mapping

        # Subscribe to maestro events for monitoring
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Setup event handlers for maestro events"""
        self.maestro.event_bus.subscribe("workflow_started", self._on_workflow_started)
        self.maestro.event_bus.subscribe(
            "workflow_completed", self._on_workflow_completed
        )
        self.maestro.event_bus.subscribe("workflow_failed", self._on_workflow_failed)
        self.maestro.event_bus.subscribe("phase_transition", self._on_phase_transition)
        self.maestro.event_bus.subscribe("task_completed", self._on_task_completed)

    async def _on_workflow_started(self, event):
        """Handle workflow started event"""
        data = event["data"]
        logger.info(
            f"Workflow started: {data['case_name']} (Session: {data['session_id']})"
        )

    async def _on_workflow_completed(self, event):
        """Handle workflow completed event"""
        data = event["data"]
        logger.info(
            f"Workflow completed: {data['case_name']} (Session: {data['session_id']})"
        )

    async def _on_workflow_failed(self, event):
        """Handle workflow failed event"""
        data = event["data"]
        logger.error(f"Workflow failed: Session {data['session_id']} - {data['error']}")

    async def _on_phase_transition(self, event):
        """Handle phase transition event"""
        data = event["data"]
        logger.info(
            f"Phase transition: {data['from_phase']} -> {data['to_phase']} (Session: {data['session_id']})"
        )

    async def _on_task_completed(self, event):
        """Handle task completed event"""
        data = event["data"]
        logger.debug(f"Task completed: {data['task_id']} in phase {data['phase']}")

    def _batch_iterable(self, iterable: Any, batch_size: int):
        """Yield successive batches from iterable."""
        it = iter(iterable)
        while True:
            batch = list(islice(it, batch_size))
            if not batch:
                break
            yield batch

    async def _process_file_batch(self, file_batch: List[str]) -> None:
        """Process a batch of files for ingestion"""
        logger.info(f"Processing batch of {len(file_batch)} files")
        # Implement batch processing logic here
        # This could include parallel processing, indexing, etc.
        await asyncio.sleep(0.1)  # Placeholder for actual batch processing

    async def create_lawsuit_workflow(
        self,
        case_name: str,
        session_id: Optional[str] = None,
        case_folder: Optional[str] = None,
        case_description: str = "",
        uploaded_documents: Optional[List[str]] = None,
    ) -> str:
        """
        Create a new lawsuit generation workflow

        Args:
            case_name: Name of the case
            session_id: Optional session id. If None a new UUID will be generated.
            case_folder: Path to folder containing case documents (optional)
            case_description: Description of the case
            uploaded_documents: List of user-uploaded document paths (optional)
        """
        try:
            # Ensure we have a concrete session id
            if not session_id:
                session_id = str(uuid.uuid4())

            input_documents = []

            # Handle user-uploaded documents
            if uploaded_documents:
                input_documents.extend(uploaded_documents)
                logger.info(f"Added {len(uploaded_documents)} user-uploaded documents")

            # Handle documents from case folder
            if case_folder:
                case_path = Path(case_folder)
                if not case_path.exists():
                    raise ValueError(f"Case folder does not exist: {case_folder}")

                # Collect all document files from folder
                document_extensions = {".pdf", ".docx", ".doc", ".txt", ".md"}
                folder_documents = [
                    str(f)
                    for f in case_path.rglob("*")
                    if f.is_file() and f.suffix.lower() in document_extensions
                ]

                if folder_documents:
                    logger.info(
                        f"Found {len(folder_documents)} documents in case folder: {case_folder}"
                    )
                    input_documents.extend(folder_documents)

            # Check total document count
            total_documents = len(input_documents)

            if total_documents == 0:
                logger.warning(f"No documents found for case: {case_name}")
            elif total_documents > 10:
                # Batch processing for large document sets
                logger.info(
                    f"Large document set detected ({total_documents} files). Using batch processing..."
                )
                batch_size = 15  # Configurable batch size

                # Process documents in batches for better performance
                for batch_num, file_batch in enumerate(
                    self._batch_iterable(input_documents, batch_size), 1
                ):
                    logger.info(
                        f"Processing batch {batch_num} ({len(file_batch)} files)..."
                    )
                    await self._process_file_batch(file_batch)

                logger.info(
                    f"Batch processing complete for {total_documents} documents"
                )
            else:
                # Small document set - process normally
                logger.info(
                    f"Processing {total_documents} documents normally (no batching needed)"
                )

            # Prepare initial context
            initial_context = {
                "case_folder": case_folder or "user_uploaded",
                "case_description": case_description,
                "document_count": total_documents,
                "workflow_type": "lawsuit_generation",
                "batch_processed": total_documents > 10,
                "has_uploaded_documents": bool(uploaded_documents),
                "has_folder_documents": bool(
                    case_folder and total_documents > len(uploaded_documents or [])
                ),
            }

            # Start the workflow
            maestro_session_id = await self.maestro.start_workflow(
                case_name=case_name,
                session_id=session_id,
                input_documents=input_documents,
                initial_context=initial_context,
            )

            # Track the session
            self.active_sessions[case_name] = maestro_session_id

            logger.info(
                f"Created lawsuit workflow for case '{case_name}' with {total_documents} documents"
            )
            return maestro_session_id

        except Exception as e:
            logger.error(f"Failed to create lawsuit workflow: {e}")
            raise

    async def get_workflow_status(
        self, case_name: Optional[str] = None, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get the status of a workflow by case name or session ID"""
        try:
            # DEBUG: Log the parameters being passed
            logger.debug(
                f"get_workflow_status called with case_name='{case_name}', session_id='{session_id}'"
            )
            logger.debug(f"Active sessions: {self.active_sessions}")

            if session_id is None and case_name is not None:
                session_id = self.active_sessions.get(case_name)
                logger.debug(
                    f"Looking up session_id for case_name '{case_name}': {session_id}"
                )
                if not session_id:
                    raise ValueError(f"No active workflow found for case: {case_name}")
            elif session_id is None:
                raise ValueError("Either case_name or session_id must be provided")

            logger.debug(
                f"Calling maestro.get_workflow_status with session_id: {session_id}"
            )
            status = await self.maestro.get_workflow_status(session_id)

            # Add additional context
            status["case_folder"] = status.get("global_context", {}).get(
                "case_folder", "Unknown"
            )
            status["document_count"] = status.get("global_context", {}).get(
                "document_count", 0
            )

            return status

        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            raise

    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows"""
        try:
            workflows = await self.maestro.list_workflows()

            # Enhance with case name mapping
            for workflow in workflows:
                # Find case name from active sessions
                case_name = None
                for name, sid in self.active_sessions.items():
                    if sid == workflow["session_id"]:
                        case_name = name
                        break
                workflow["case_name_mapped"] = case_name

            return workflows

        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            raise

    async def pause_workflow(
        self, case_name: Optional[str] = None, session_id: Optional[str] = None
    ) -> bool:
        """Pause a workflow"""
        try:
            # ensure session_id is a concrete string
            session_id = self._require_session_id(session_id, case_name)

            # Load the workflow state and pause it
            workflow_state = await self.maestro.state_manager.load_state(session_id)
            workflow_state.overall_status = PhaseStatus.PAUSED
            workflow_state.human_feedback_required = True

            await self.maestro.state_manager.save_state(workflow_state)

            logger.info(f"Paused workflow: {session_id}")
            return True

        except Exception as exc:
            logger.error(f"Failed to pause workflow: {exc}")
            return False

    async def resume_workflow(
        self, case_name: Optional[str] = None, session_id: Optional[str] = None
    ) -> bool:
        """Resume a paused workflow"""
        try:
            # ensure session_id is a concrete string
            session_id = self._require_session_id(session_id, case_name)

            # Load the workflow state and resume it
            workflow_state = await self.maestro.state_manager.load_state(session_id)
            workflow_state.overall_status = PhaseStatus.IN_PROGRESS
            workflow_state.human_feedback_required = False

            await self.maestro.state_manager.save_state(workflow_state)

            # Restart the workflow execution
            if session_id not in self.maestro.active_workflows:
                # session_id guaranteed to be a str by helper
                self.maestro.active_workflows[session_id] = workflow_state
                asyncio.create_task(self.maestro._execute_workflow(session_id))

            logger.info(f"Resumed workflow: {session_id}")
            return True

        except Exception as exc:
            logger.error(f"Failed to resume workflow: {exc}")
            return False

    async def get_workflow_progress(
        self, case_name: Optional[str] = None, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed progress information for a workflow"""
        try:
            status = await self.get_workflow_status(case_name, session_id)

            # Calculate phase progress
            phase_progress = {}
            for phase in WorkflowPhase:
                phase_status = status.get("phases", {}).get(
                    phase.value, PhaseStatus.PENDING.value
                )
                phase_progress[phase.value] = {
                    "status": phase_status,
                    "is_current": phase.value == status["current_phase"],
                    "is_completed": phase_status == PhaseStatus.COMPLETED.value,
                }

            # Get task breakdown
            task_summary = {
                "total": status["tasks_total"],
                "completed": status["tasks_completed"],
                "failed": len([t for t in status.get("failed_tasks", [])]),
                "pending": status["tasks_total"] - status["tasks_completed"],
            }

            return {
                "session_id": status["session_id"],
                "case_name": status["case_name"],
                "overall_progress": status["progress_percentage"],
                "current_phase": status["current_phase"],
                "phases": phase_progress,
                "tasks": task_summary,
                "human_feedback_required": status["human_feedback_required"],
                "pending_approvals": status["pending_approvals"],
                "created_at": status["created_at"],
                "updated_at": status["updated_at"],
            }

        except Exception as e:
            logger.error(f"Failed to get workflow progress: {e}")
            raise

    async def submit_human_feedback(
        self,
        session_id: str,
        approved: bool,
        feedback: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Submit human feedback for a workflow awaiting approval"""
        try:
            # Load workflow state
            workflow_state = await self.maestro.state_manager.load_state(session_id)

            if not workflow_state.human_feedback_required:
                logger.warning(f"Workflow {session_id} is not awaiting human feedback")
                return False

            # Process the feedback
            workflow_state.human_feedback_required = False
            workflow_state.pending_approvals.clear()

            if approved:
                # Continue the workflow
                workflow_state.overall_status = PhaseStatus.IN_PROGRESS
                # Resume execution
                if session_id not in self.maestro.active_workflows:
                    self.maestro.active_workflows[session_id] = workflow_state
                    asyncio.create_task(self.maestro._execute_workflow(session_id))
            else:
                # Pause for revision
                workflow_state.overall_status = PhaseStatus.PAUSED
                logger.info(f"Workflow {session_id} paused based on human feedback")

            # Add feedback to global context
            workflow_state.global_context["human_feedback"] = {
                "approved": approved,
                "feedback": feedback,
                "context": context or {},
                "timestamp": workflow_state.updated_at.isoformat(),
            }

            await self.maestro.state_manager.save_state(workflow_state)

            # Emit feedback event
            await self.maestro.event_bus.emit(
                "human_feedback_submitted",
                {"session_id": session_id, "approved": approved, "feedback": feedback},
            )

            logger.info(
                f"Human feedback submitted for workflow {session_id}: {'Approved' if approved else 'Rejected'}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to submit human feedback: {e}")
            return False

    async def get_case_facts(
        self, case_name: Optional[str] = None, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get extracted case facts from the knowledge graph"""
        try:
            if session_id is None and case_name is not None:
                session_id = self.active_sessions.get(case_name)
                if not session_id:
                    raise ValueError(f"No active workflow found for case: {case_name}")

            # Ensure we pass a string identifier to the knowledge graph
            case_identifier = case_name or session_id or "unknown_case"

            # Query the knowledge graph for case facts
            facts = self.knowledge_graph.get_case_facts(case_identifier)

            return {
                "case_identifier": case_identifier,
                "facts": facts,
                "extracted_entities": len(facts.get("entities", [])),
                "relationships": len(facts.get("relationships", [])),
            }

        except Exception as e:
            logger.error(f"Failed to get case facts: {e}")
            return {"error": str(e)}

    async def export_workflow_results(
        self, session_id: str, export_format: str = "json"
    ) -> Dict[str, Any]:
        """Export workflow results and generated documents"""
        try:
            # ensure session_id is concrete (this signature already expects str, but keep defensive)
            session_id = str(session_id)

            # Get workflow status and state
            status = await self.maestro.get_workflow_status(session_id)
            workflow_state = await self.maestro.state_manager.load_state(session_id)

            # Compile results
            results = {
                "workflow_info": status,
                "generated_content": {},
                "knowledge_graph_data": {},
                "task_results": {},
            }

            # Extract task results
            for task_id, task in workflow_state.tasks.items():
                if task.output_data:
                    results["task_results"][task_id] = {
                        "phase": task.phase.value,
                        "agent_type": task.agent_type,
                        "description": task.description,
                        "output": task.output_data,
                        "duration": task.actual_duration,
                    }

            # Get case facts
            case_facts = await self.get_case_facts(session_id=session_id)
            results["knowledge_graph_data"] = case_facts

            logger.info(f"Exported workflow results for session {session_id}")
            return results

        except Exception as e:
            logger.error(f"Failed to export workflow results: {e}")
            raise

    async def create_ai_document_workflow(
        self,
        case_name: str,
        case_data: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a workflow specifically for AI document generation using Tesla case data.

        Args:
            case_name: Name of the case
            case_data: Tesla case data dictionary
            options: Optional generation options

        Returns:
            session_id of the created workflow
        """
        try:
            # Generate a session id for this workflow
            session_id = str(uuid.uuid4())

            # Convert case data to the format expected by the workflow
            initial_context = {
                "case_data": case_data,
                "case_name": case_name,
                "case_description": case_data.get("case_name", case_name),
                "workflow_type": "ai_document_generation",
                "ai_generation_options": options or {},
            }

            # Use case evidence as input documents if available
            input_documents = case_data.get("evidence", [])

            # Start the workflow with AI document generation focus
            session_id = await self.maestro.start_workflow(
                case_name=case_name,
                session_id=session_id,
                input_documents=input_documents,
                initial_context=initial_context,
            )

            # Track the session
            self.active_sessions[case_name] = session_id

            logger.info(
                f"Created AI document workflow for case '{case_name}' with Tesla case data"
            )
            return session_id

        except Exception as e:
            logger.error(f"Failed to create AI document workflow: {e}")
            raise

    async def get_ai_generation_status(
        self, case_name: Optional[str] = None, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get the status of AI document generation tasks within a workflow.

        Args:
            case_name: Name of the case
            session_id: Session ID of the workflow

        Returns:
            Dictionary containing AI generation status and results
        """
        try:
            # ensure session_id is a concrete string
            session_id = self._require_session_id(session_id, case_name)

            # Get workflow state
            workflow_state = await self.maestro.state_manager.load_state(session_id)

            # Extract AI-related task results
            ai_tasks = {}
            ai_results = {
                "case_classification": None,
                "form_processing": None,
                "field_mapping": None,
                "form_generation": None,
                "documents_generated": [],
                "overall_progress": 0.0,
            }

            for task_id, task in workflow_state.tasks.items():
                if task.agent_type == "AIDocumentAgent":
                    ai_tasks[task_id] = {
                        "description": task.description,
                        "status": task.status.value,
                        "output": task.output_data,
                        "phase": task.phase.value,
                    }

                    # Extract specific AI results based on task type
                    if task.output_data:
                        task_type = task.input_data.get("task_type", "")
                        if "classification" in task_type:
                            ai_results["case_classification"] = task.output_data
                        elif "form_processing" in task_type:
                            ai_results["form_processing"] = task.output_data
                        elif "field_mapping" in task_type:
                            ai_results["field_mapping"] = task.output_data
                        elif "form_generation" in task_type:
                            ai_results["form_generation"] = task.output_data
                            if "output_files" in task.output_data:
                                ai_results["documents_generated"].extend(
                                    task.output_data["output_files"]
                                )

            # Calculate overall progress
            completed_ai_tasks = sum(
                1 for task in ai_tasks.values() if task["status"] == "completed"
            )
            total_ai_tasks = len(ai_tasks)
            if total_ai_tasks > 0:
                ai_results["overall_progress"] = completed_ai_tasks / total_ai_tasks

            return {
                "session_id": session_id,
                "case_name": case_name,
                "ai_tasks": ai_tasks,
                "ai_results": ai_results,
                "total_ai_tasks": total_ai_tasks,
                "completed_ai_tasks": completed_ai_tasks,
            }

        except Exception as e:
            logger.error(f"Failed to get AI generation status: {e}")
            raise

    async def process_tesla_case_data(
        self, tesla_case_data: Dict[str, Any], case_name: Optional[str] = None
    ) -> str:
        """
        Process Tesla case data through the AI document generation workflow.

        Args:
            tesla_case_data: Tesla case data from tesla_case_data.py
            case_name: Optional case name, defaults to case data case_name

        Returns:
            session_id of the workflow processing the Tesla case
        """
        try:
            # Resolve a concrete case name string (avoid passing Optional[str] to typed APIs)
            resolved_case_name: str = (
                case_name or tesla_case_data.get("case_name") or "Tesla_Case_Unknown"
            )

            # Validate Tesla case data has required fields
            required_fields = ["case_name", "plaintiff_name", "defendant_name"]
            missing_fields = [
                field for field in required_fields if field not in tesla_case_data
            ]
            if missing_fields:
                logger.warning(f"Tesla case data missing fields: {missing_fields}")

            # Create AI document workflow with Tesla data
            session_id = await self.create_ai_document_workflow(
                case_name=resolved_case_name,
                case_data=tesla_case_data,
                options={
                    "tesla_case": True,
                    "auto_generate_forms": True,
                    "focus_areas": ["contract_breach", "consumer_protection"],
                },
            )

            logger.info(
                f"Started Tesla case processing: {resolved_case_name} -> {session_id}"
            )
            return session_id

        except Exception as e:
            logger.error(f"Failed to process Tesla case data: {e}")
            raise

    async def get_generated_documents(
        self, case_name: Optional[str] = None, session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of documents generated by AI agents.
        """
        try:
            # ensure session_id is a concrete string
            session_id = self._require_session_id(session_id, case_name)

            ai_status = await self.get_ai_generation_status(case_name, session_id)

            generated_docs = []
            for doc_path in ai_status["ai_results"]["documents_generated"]:
                doc_info = {
                    "file_path": doc_path,
                    "file_name": (
                        Path(doc_path).name
                        if isinstance(doc_path, str)
                        else str(doc_path)
                    ),
                    "generated_by": "AIDocumentAgent",
                    "case_name": case_name
                    or ai_status.get("case_name")
                    or "unknown_case",
                }
                generated_docs.append(doc_info)

            # Also check for any additional documents in task outputs
            for task_info in ai_status["ai_tasks"].values():
                if task_info["output"] and "output_files" in task_info["output"]:
                    for file_path in task_info["output"]["output_files"]:
                        # Avoid duplicates
                        if not any(
                            doc["file_path"] == file_path for doc in generated_docs
                        ):
                            generated_docs.append(
                                {
                                    "file_path": file_path,
                                    "file_name": (
                                        Path(file_path).name
                                        if isinstance(file_path, str)
                                        else str(file_path)
                                    ),
                                    "generated_by": "AIDocumentAgent",
                                    "case_name": case_name
                                    or ai_status.get("case_name")
                                    or "unknown_case",
                                }
                            )

            return generated_docs

        except Exception as e:
            logger.error(f"Failed to get generated documents: {e}")
            raise

    async def shutdown(self):
        """Shutdown the workflow manager and clean up resources"""
        try:
            await self.maestro.shutdown()
            self.active_sessions.clear()
            logger.info("Enhanced workflow manager shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    # NEW: helper to ensure we have a concrete session id string
    def _require_session_id(
        self, session_id: Optional[str], case_name: Optional[str] = None
    ) -> str:
        """
        Resolve and validate session_id. Prefer given session_id, fall back to active_sessions[case_name].
        Raises ValueError if neither yields a non-empty string.
        """
        if session_id is None:
            if case_name is not None:
                session_id = self.active_sessions.get(case_name)
        if not session_id:
            raise ValueError("Either case_name or session_id must be provided")
        return str(session_id)


# Compatibility functions for the existing workflow system
async def create_tesla_lawsuit_workflow(case_folder: str = "Tesla") -> str:
    """Convenience function to create a Tesla lawsuit workflow"""
    workflow_manager = EnhancedWorkflowManager()
    try:
        # generate session id implicitly (create_lawsuit_workflow handles None now)
        session_id = await workflow_manager.create_lawsuit_workflow(
            case_name="Tesla Securities Litigation",
            case_folder=case_folder,
            case_description="Securities fraud lawsuit against Tesla Inc.",
        )
        return session_id
    finally:
        await workflow_manager.shutdown()


async def get_tesla_workflow_status(session_id: str) -> Dict[str, Any]:
    """Convenience function to get Tesla workflow status"""
    workflow_manager = EnhancedWorkflowManager()
    try:
        return await workflow_manager.get_workflow_status(session_id=session_id)
    finally:
        await workflow_manager.shutdown()


# Demo function
async def demo_enhanced_workflow():
    """Demonstrate the enhanced workflow system"""
    workflow_manager = EnhancedWorkflowManager()

    try:
        print("=== Enhanced LawyerFactory Workflow Demo ===")

        # Create a workflow
        print("\n1. Creating Tesla lawsuit workflow...")
        session_id = await workflow_manager.create_lawsuit_workflow(
            case_name="Tesla Securities Litigation Demo",
            case_folder="Tesla",
            case_description="Demo of the enhanced workflow system",
        )
        print(f"Created workflow with session ID: {session_id}")

        # Wait a bit for processing
        await asyncio.sleep(3)

        # Check status
        print("\n2. Checking workflow status...")
        status = await workflow_manager.get_workflow_status(session_id=session_id)
        print(f"Current phase: {status['current_phase']}")
        print(f"Progress: {status['progress_percentage']:.1f}%")
        print(f"Tasks completed: {status['tasks_completed']}/{status['tasks_total']}")

        # Get detailed progress
        print("\n3. Getting detailed progress...")
        progress = await workflow_manager.get_workflow_progress(session_id=session_id)
        print("Phase Status:")
        for phase, info in progress["phases"].items():
            marker = (
                "➤" if info["is_current"] else ("✓" if info["is_completed"] else "○")
            )
            print(f"  {marker} {phase}: {info['status']}")

        # List all workflows
        print("\n4. Listing all workflows...")
        workflows = await workflow_manager.list_workflows()
        for workflow in workflows:
            print(
                f"  - {workflow['case_name']} ({workflow['session_id'][:8]}...): {workflow['overall_status']}"
            )

        print("\n=== Demo Complete ===")

    except Exception as e:
        print(f"Demo failed: {e}")
    finally:
        await workflow_manager.shutdown()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_enhanced_workflow())
