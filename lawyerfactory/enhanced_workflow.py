"""
Enhanced workflow management for LawyerFactory.
Integrates with the new maestro orchestration system while maintaining compatibility.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

# Add maestro to the path for imports
sys.path.append(str(Path(__file__).parent.parent))

from maestro.enhanced_maestro import EnhancedMaestro
from maestro.workflow_models import WorkflowPhase, PhaseStatus, WorkflowState
from knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class EnhancedWorkflowManager:
    """Enhanced workflow manager that coordinates with the maestro orchestration"""

    def __init__(self, knowledge_graph_path: str = "knowledge_graph.db", 
                 storage_path: str = "workflow_storage"):
        """Initialize the enhanced workflow manager"""
        self.knowledge_graph = KnowledgeGraph(knowledge_graph_path)
        self.maestro = EnhancedMaestro(
            knowledge_graph=self.knowledge_graph,
            storage_path=storage_path
        )
        self.active_sessions: Dict[str, str] = {}  # case_name -> session_id mapping
        
        # Subscribe to maestro events for monitoring
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Setup event handlers for maestro events"""
        self.maestro.event_bus.subscribe('workflow_started', self._on_workflow_started)
        self.maestro.event_bus.subscribe('workflow_completed', self._on_workflow_completed)
        self.maestro.event_bus.subscribe('workflow_failed', self._on_workflow_failed)
        self.maestro.event_bus.subscribe('phase_transition', self._on_phase_transition)
        self.maestro.event_bus.subscribe('task_completed', self._on_task_completed)

    async def _on_workflow_started(self, event):
        """Handle workflow started event"""
        data = event['data']
        logger.info(f"Workflow started: {data['case_name']} (Session: {data['session_id']})")

    async def _on_workflow_completed(self, event):
        """Handle workflow completed event"""
        data = event['data']
        logger.info(f"Workflow completed: {data['case_name']} (Session: {data['session_id']})")

    async def _on_workflow_failed(self, event):
        """Handle workflow failed event"""
        data = event['data']
        logger.error(f"Workflow failed: Session {data['session_id']} - {data['error']}")

    async def _on_phase_transition(self, event):
        """Handle phase transition event"""
        data = event['data']
        logger.info(f"Phase transition: {data['from_phase']} -> {data['to_phase']} (Session: {data['session_id']})")

    async def _on_task_completed(self, event):
        """Handle task completed event"""
        data = event['data']
        logger.debug(f"Task completed: {data['task_id']} in phase {data['phase']}")

    async def create_lawsuit_workflow(self, case_name: str, case_folder: str, 
                                    case_description: str = "") -> str:
        """Create a new lawsuit generation workflow"""
        try:
            # Find all documents in the case folder
            case_path = Path(case_folder)
            if not case_path.exists():
                raise ValueError(f"Case folder does not exist: {case_folder}")
            
            # Collect all document files
            document_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md'}
            input_documents = []
            
            for file_path in case_path.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in document_extensions:
                    input_documents.append(str(file_path))
            
            if not input_documents:
                logger.warning(f"No documents found in case folder: {case_folder}")
            
            # Prepare initial context
            initial_context = {
                'case_folder': case_folder,
                'case_description': case_description,
                'document_count': len(input_documents),
                'workflow_type': 'lawsuit_generation'
            }
            
            # Start the workflow
            session_id = await self.maestro.start_workflow(
                case_name=case_name,
                input_documents=input_documents,
                initial_context=initial_context
            )
            
            # Track the session
            self.active_sessions[case_name] = session_id
            
            logger.info(f"Created lawsuit workflow for case '{case_name}' with {len(input_documents)} documents")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create lawsuit workflow: {e}")
            raise

    async def get_workflow_status(self, case_name: str = None, session_id: str = None) -> Dict[str, Any]:
        """Get the status of a workflow by case name or session ID"""
        try:
            if session_id is None and case_name is not None:
                session_id = self.active_sessions.get(case_name)
                if not session_id:
                    raise ValueError(f"No active workflow found for case: {case_name}")
            elif session_id is None:
                raise ValueError("Either case_name or session_id must be provided")
            
            status = await self.maestro.get_workflow_status(session_id)
            
            # Add additional context
            status['case_folder'] = status.get('global_context', {}).get('case_folder', 'Unknown')
            status['document_count'] = status.get('global_context', {}).get('document_count', 0)
            
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
                    if sid == workflow['session_id']:
                        case_name = name
                        break
                workflow['case_name_mapped'] = case_name
            
            return workflows
            
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            raise

    async def pause_workflow(self, case_name: str = None, session_id: str = None) -> bool:
        """Pause a workflow"""
        try:
            if session_id is None and case_name is not None:
                session_id = self.active_sessions.get(case_name)
                if not session_id:
                    raise ValueError(f"No active workflow found for case: {case_name}")
            
            # Load the workflow state and pause it
            workflow_state = await self.maestro.state_manager.load_state(session_id)
            workflow_state.overall_status = PhaseStatus.PAUSED
            workflow_state.human_feedback_required = True
            
            await self.maestro.state_manager.save_state(workflow_state)
            
            logger.info(f"Paused workflow: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause workflow: {e}")
            return False

    async def resume_workflow(self, case_name: str = None, session_id: str = None) -> bool:
        """Resume a paused workflow"""
        try:
            if session_id is None and case_name is not None:
                session_id = self.active_sessions.get(case_name)
                if not session_id:
                    raise ValueError(f"No active workflow found for case: {case_name}")
            
            # Load the workflow state and resume it
            workflow_state = await self.maestro.state_manager.load_state(session_id)
            workflow_state.overall_status = PhaseStatus.IN_PROGRESS
            workflow_state.human_feedback_required = False
            
            await self.maestro.state_manager.save_state(workflow_state)
            
            # Restart the workflow execution
            if session_id not in self.maestro.active_workflows:
                self.maestro.active_workflows[session_id] = workflow_state
                asyncio.create_task(self.maestro._execute_workflow(session_id))
            
            logger.info(f"Resumed workflow: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume workflow: {e}")
            return False

    async def get_workflow_progress(self, case_name: str = None, session_id: str = None) -> Dict[str, Any]:
        """Get detailed progress information for a workflow"""
        try:
            status = await self.get_workflow_status(case_name, session_id)
            
            # Calculate phase progress
            phase_progress = {}
            for phase in WorkflowPhase:
                phase_status = status.get('phases', {}).get(phase.value, PhaseStatus.PENDING.value)
                phase_progress[phase.value] = {
                    'status': phase_status,
                    'is_current': phase.value == status['current_phase'],
                    'is_completed': phase_status == PhaseStatus.COMPLETED.value
                }
            
            # Get task breakdown
            task_summary = {
                'total': status['tasks_total'],
                'completed': status['tasks_completed'],
                'failed': len([t for t in status.get('failed_tasks', [])]),
                'pending': status['tasks_total'] - status['tasks_completed']
            }
            
            return {
                'session_id': status['session_id'],
                'case_name': status['case_name'],
                'overall_progress': status['progress_percentage'],
                'current_phase': status['current_phase'],
                'phases': phase_progress,
                'tasks': task_summary,
                'human_feedback_required': status['human_feedback_required'],
                'pending_approvals': status['pending_approvals'],
                'created_at': status['created_at'],
                'updated_at': status['updated_at']
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow progress: {e}")
            raise

    async def submit_human_feedback(self, session_id: str, approved: bool, 
                                  feedback: str = "", context: Dict[str, Any] = None) -> bool:
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
            workflow_state.global_context['human_feedback'] = {
                'approved': approved,
                'feedback': feedback,
                'context': context or {},
                'timestamp': workflow_state.updated_at.isoformat()
            }
            
            await self.maestro.state_manager.save_state(workflow_state)
            
            # Emit feedback event
            await self.maestro.event_bus.emit('human_feedback_submitted', {
                'session_id': session_id,
                'approved': approved,
                'feedback': feedback
            })
            
            logger.info(f"Human feedback submitted for workflow {session_id}: {'Approved' if approved else 'Rejected'}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to submit human feedback: {e}")
            return False

    async def get_case_facts(self, case_name: str = None, session_id: str = None) -> Dict[str, Any]:
        """Get extracted case facts from the knowledge graph"""
        try:
            if session_id is None and case_name is not None:
                session_id = self.active_sessions.get(case_name)
                if not session_id:
                    raise ValueError(f"No active workflow found for case: {case_name}")
            
            # Query the knowledge graph for case facts
            facts = self.knowledge_graph.get_case_facts(case_name or session_id)
            
            return {
                'case_identifier': case_name or session_id,
                'facts': facts,
                'extracted_entities': len(facts.get('entities', [])),
                'relationships': len(facts.get('relationships', []))
            }
            
        except Exception as e:
            logger.error(f"Failed to get case facts: {e}")
            return {'error': str(e)}

    async def export_workflow_results(self, session_id: str, export_format: str = 'json') -> Dict[str, Any]:
        """Export workflow results and generated documents"""
        try:
            # Get workflow status and state
            status = await self.maestro.get_workflow_status(session_id)
            workflow_state = await self.maestro.state_manager.load_state(session_id)
            
            # Compile results
            results = {
                'workflow_info': status,
                'generated_content': {},
                'knowledge_graph_data': {},
                'task_results': {}
            }
            
            # Extract task results
            for task_id, task in workflow_state.tasks.items():
                if task.output_data:
                    results['task_results'][task_id] = {
                        'phase': task.phase.value,
                        'agent_type': task.agent_type,
                        'description': task.description,
                        'output': task.output_data,
                        'duration': task.actual_duration
                    }
            
            # Get case facts
            case_facts = await self.get_case_facts(session_id=session_id)
            results['knowledge_graph_data'] = case_facts
            
            logger.info(f"Exported workflow results for session {session_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to export workflow results: {e}")
            raise

    async def shutdown(self):
        """Shutdown the workflow manager and clean up resources"""
        try:
            await self.maestro.shutdown()
            self.active_sessions.clear()
            logger.info("Enhanced workflow manager shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Compatibility functions for the existing workflow system
async def create_tesla_lawsuit_workflow(case_folder: str = "Tesla") -> str:
    """Convenience function to create a Tesla lawsuit workflow"""
    workflow_manager = EnhancedWorkflowManager()
    try:
        session_id = await workflow_manager.create_lawsuit_workflow(
            case_name="Tesla Securities Litigation",
            case_folder=case_folder,
            case_description="Securities fraud lawsuit against Tesla Inc."
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
            case_description="Demo of the enhanced workflow system"
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
        for phase, info in progress['phases'].items():
            marker = "➤" if info['is_current'] else ("✓" if info['is_completed'] else "○")
            print(f"  {marker} {phase}: {info['status']}")
        
        # List all workflows
        print("\n4. Listing all workflows...")
        workflows = await workflow_manager.list_workflows()
        for workflow in workflows:
            print(f"  - {workflow['case_name']} ({workflow['session_id'][:8]}...): {workflow['overall_status']}")
        
        print(f"\n=== Demo Complete ===")
        
    except Exception as e:
        print(f"Demo failed: {e}")
    finally:
        await workflow_manager.shutdown()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_enhanced_workflow())