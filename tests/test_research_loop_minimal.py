# Script Name: test_research_loop_minimal.py
# Description: Minimal tests for iterative research loop functionality.  This module tests the research loop logic independently of the full EnhancedMaestro to validate the core functionality without import dependencies.
# Relationships:
#   - Entity Type: Test
#   - Directory Group: Research
#   - Group Tags: legal-research, testing
Minimal tests for iterative research loop functionality.

This module tests the research loop logic independently of the full EnhancedMaestro
to validate the core functionality without import dependencies.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock

import pytest

# Import only the workflow models which should be available
from src.lawyerfactory.phases.07_orchestration.workflow_models import (PhaseStatus,
                                                               TaskPriority,
                                                               WorkflowPhase,
                                                               WorkflowState,
                                                               WorkflowTask)


class MockEnhancedMaestro:
    """Mock version of EnhancedMaestro with only the research loop methods."""
    
    def __init__(self):
        self.knowledge_graph = Mock()
        self.logger = Mock()
    
    async def _check_research_needed(self, workflow_state: WorkflowState) -> bool:
        """Check if any current phase tasks need research."""
        current_phase = workflow_state.current_phase
        
        # Find tasks for current phase that need research
        for task_id, task in workflow_state.tasks.items():
            if (task.phase == current_phase and
                task.status in [PhaseStatus.IN_PROGRESS, PhaseStatus.PENDING] and
                getattr(task, 'research_needed', False)):
                return True
        
        return False
    
    async def _initiate_research_loop(self, workflow_state: WorkflowState):
        """Initiate a research loop by transitioning to RESEARCH phase."""
        # Store the current phase as the source for return
        source_phase = workflow_state.current_phase
        
        # Increment research loop count
        workflow_state.research_loop_count += 1
        
        # Collect research questions from tasks that need research
        research_questions = []
        for task_id, task in workflow_state.tasks.items():
            if (task.phase == source_phase and
                getattr(task, 'research_needed', False) and
                getattr(task, 'research_questions', [])):
                research_questions.extend(task.research_questions)
        
        # Create research loop history entry
        loop_entry = {
            "loop_number": workflow_state.research_loop_count,
            "source_phase": source_phase.value,
            "research_questions": research_questions,
            "started_at": datetime.now().isoformat(),
            "status": "active"
        }
        workflow_state.research_loop_history.append(loop_entry)
        
        # Set pending research questions
        workflow_state.pending_research_questions = research_questions
        
        # Transition to RESEARCH phase
        workflow_state.current_phase = WorkflowPhase.RESEARCH
        workflow_state.phases[WorkflowPhase.RESEARCH] = PhaseStatus.IN_PROGRESS
    
    async def _complete_research_loop(self, workflow_state: WorkflowState, source_phase: str):
        """Complete the research loop and return to the source phase."""
        # Convert source_phase string back to WorkflowPhase enum
        try:
            return_phase = WorkflowPhase(source_phase)
        except ValueError:
            return_phase = WorkflowPhase.OUTLINE
        
        # Update workflow state to return to source phase
        workflow_state.current_phase = return_phase
        workflow_state.phases[return_phase] = PhaseStatus.IN_PROGRESS
        workflow_state.phases[WorkflowPhase.RESEARCH] = PhaseStatus.COMPLETED
        
        # Update research loop history
        if workflow_state.research_loop_history:
            workflow_state.research_loop_history[-1]["completed_at"] = datetime.now().isoformat()
            workflow_state.research_loop_history[-1]["status"] = "completed"


@pytest.fixture
def sample_workflow_state():
    """Create a sample workflow state for testing research loops."""
    task_1 = WorkflowTask(
        id="task-1",
        phase=WorkflowPhase.DRAFTING,
        agent_type="draft_bot",
        description="Draft complaint document",
        status=PhaseStatus.IN_PROGRESS,
        research_needed=True,
        research_questions=[
            "What is the statute of limitations for contract disputes in California?",
            "Are there recent precedents for similar breach of contract cases?"
        ]
    )
    
    return WorkflowState(
        session_id="test-research-loop-001",
        case_name="Test Contract Dispute",
        current_phase=WorkflowPhase.DRAFTING,
        overall_status=PhaseStatus.IN_PROGRESS,
        phases={
            WorkflowPhase.INTAKE: PhaseStatus.COMPLETED,
            WorkflowPhase.RESEARCH: PhaseStatus.COMPLETED,
            WorkflowPhase.OUTLINE: PhaseStatus.COMPLETED,
            WorkflowPhase.DRAFTING: PhaseStatus.IN_PROGRESS,
            WorkflowPhase.POST_PRODUCTION: PhaseStatus.PENDING
        },
        tasks={
            "task-1": task_1
        },
        global_context={
            "jurisdiction": "california",
            "case_type": "contract_dispute",
            "evidence_table": [
                {"citation": "Original Contract", "title": "Service Agreement", "source": "client"}
            ]
        },
        research_loop_count=0,
        research_loop_history=[],
        pending_research_questions=[]
    )

@pytest.fixture
def mock_maestro():
    """Create MockEnhancedMaestro instance for testing."""
    return MockEnhancedMaestro()


class TestResearchLoopCore:
    """Test core research loop functionality."""
    
    @pytest.mark.asyncio
    async def test_workflow_models_have_research_fields(self, sample_workflow_state):
        """Test that workflow models have the required research loop fields."""
        # Check WorkflowState has research loop fields
        assert hasattr(sample_workflow_state, 'research_loop_count')
        assert hasattr(sample_workflow_state, 'research_loop_history')
        assert hasattr(sample_workflow_state, 'pending_research_questions')
        
        # Check WorkflowTask has research fields
        task = list(sample_workflow_state.tasks.values())[0]
        assert hasattr(task, 'research_needed')
        assert hasattr(task, 'research_questions')
        
        # Check values are correct
        assert sample_workflow_state.research_loop_count == 0
        assert sample_workflow_state.research_loop_history == []
        assert sample_workflow_state.pending_research_questions == []
        assert task.research_needed is True
        assert len(task.research_questions) == 2
    
    @pytest.mark.asyncio
    async def test_post_production_phase_exists(self):
        """Test that POST_PRODUCTION phase was added to WorkflowPhase enum."""
        # Should be able to create POST_PRODUCTION phase
        phase = WorkflowPhase.POST_PRODUCTION
        assert phase.value == "post_production"
        
        # Should be in the enum
        all_phases = list(WorkflowPhase)
        assert WorkflowPhase.POST_PRODUCTION in all_phases
    
    @pytest.mark.asyncio
    async def test_research_needed_detection(self, mock_maestro, sample_workflow_state):
        """Test detection of research_needed flags."""
        # Should detect research needed
        result = await mock_maestro._check_research_needed(sample_workflow_state)
        assert result is True
        
        # Remove research flag and test again
        list(sample_workflow_state.tasks.values())[0].research_needed = False
        result = await mock_maestro._check_research_needed(sample_workflow_state)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_research_loop_initiation(self, mock_maestro, sample_workflow_state):
        """Test research loop initiation."""
        original_phase = sample_workflow_state.current_phase
        
        # Initiate research loop
        await mock_maestro._initiate_research_loop(sample_workflow_state)
        
        # Verify state changes
        assert sample_workflow_state.current_phase == WorkflowPhase.RESEARCH
        assert sample_workflow_state.research_loop_count == 1
        assert len(sample_workflow_state.research_loop_history) == 1
        
        # Verify research loop history
        loop_entry = sample_workflow_state.research_loop_history[0]
        assert loop_entry["source_phase"] == original_phase.value
        assert loop_entry["loop_number"] == 1
        assert loop_entry["status"] == "active"
        assert "started_at" in loop_entry
        
        # Verify pending research questions
        expected_questions = [
            "What is the statute of limitations for contract disputes in California?",
            "Are there recent precedents for similar breach of contract cases?"
        ]
        assert sample_workflow_state.pending_research_questions == expected_questions
    
    @pytest.mark.asyncio
    async def test_research_loop_completion(self, mock_maestro, sample_workflow_state):
        """Test research loop completion."""
        # Set up as if we're in a research loop
        sample_workflow_state.current_phase = WorkflowPhase.RESEARCH
        sample_workflow_state.phases[WorkflowPhase.RESEARCH] = PhaseStatus.IN_PROGRESS
        sample_workflow_state.research_loop_history = [{
            "source_phase": "drafting",
            "loop_number": 1,
            "status": "active"
        }]
        
        # Complete the research loop
        await mock_maestro._complete_research_loop(sample_workflow_state, "drafting")
        
        # Verify return to DRAFTING phase
        assert sample_workflow_state.current_phase == WorkflowPhase.DRAFTING
        assert sample_workflow_state.phases[WorkflowPhase.DRAFTING] == PhaseStatus.IN_PROGRESS
        assert sample_workflow_state.phases[WorkflowPhase.RESEARCH] == PhaseStatus.COMPLETED
        
        # Verify research loop history is updated
        loop_entry = sample_workflow_state.research_loop_history[0]
        assert loop_entry["status"] == "completed"
        assert "completed_at" in loop_entry
    
    @pytest.mark.asyncio
    async def test_multiple_research_loops(self, mock_maestro, sample_workflow_state):
        """Test handling of multiple research loops."""
        # First research loop
        await mock_maestro._initiate_research_loop(sample_workflow_state)
        assert sample_workflow_state.research_loop_count == 1
        
        # Complete first loop
        await mock_maestro._complete_research_loop(sample_workflow_state, "drafting")
        
        # Start second research loop
        await mock_maestro._initiate_research_loop(sample_workflow_state)
        assert sample_workflow_state.research_loop_count == 2
        assert len(sample_workflow_state.research_loop_history) == 2
        
        # Verify both loops in history
        assert sample_workflow_state.research_loop_history[0]["status"] == "completed"
        assert sample_workflow_state.research_loop_history[1]["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_research_loop_with_no_questions(self, mock_maestro):
        """Test research loop initiation when task has no questions."""
        # Create workflow state with task that needs research but has no questions
        task_no_questions = WorkflowTask(
            id="task-1",
            phase=WorkflowPhase.DRAFTING,
            agent_type="draft_bot",
            description="Task with no questions",
            status=PhaseStatus.IN_PROGRESS,
            research_needed=True,
            research_questions=[]  # Empty list
        )
        
        workflow_state = WorkflowState(
            session_id="test-no-questions",
            case_name="Test No Questions",
            current_phase=WorkflowPhase.DRAFTING,
            overall_status=PhaseStatus.IN_PROGRESS,
            phases={WorkflowPhase.DRAFTING: PhaseStatus.IN_PROGRESS},
            tasks={
                "task-1": task_no_questions
            },
            global_context={},
            research_loop_count=0,
            research_loop_history=[],
            pending_research_questions=[]
        )
        
        # Should still be able to initiate research loop
        await mock_maestro._initiate_research_loop(workflow_state)
        
        # Verify it worked
        assert workflow_state.current_phase == WorkflowPhase.RESEARCH
        assert workflow_state.research_loop_count == 1
        assert workflow_state.pending_research_questions == []


class TestWorkflowStateIntegrity:
    """Test workflow state integrity during research loops."""
    
    @pytest.mark.asyncio
    async def test_workflow_state_preservation(self, mock_maestro, sample_workflow_state):
        """Test that important workflow state is preserved during research loops."""
        # Store original state
        original_tasks = len(sample_workflow_state.tasks)
        original_context = sample_workflow_state.global_context.copy()
        original_session_id = sample_workflow_state.session_id
        
        # Do a full research loop cycle
        await mock_maestro._initiate_research_loop(sample_workflow_state)
        await mock_maestro._complete_research_loop(sample_workflow_state, "drafting")
        
        # Verify important state is preserved
        assert len(sample_workflow_state.tasks) == original_tasks
        assert sample_workflow_state.session_id == original_session_id
        assert sample_workflow_state.global_context == original_context
    
    @pytest.mark.asyncio
    async def test_phase_status_consistency(self, mock_maestro, sample_workflow_state):
        """Test that phase statuses remain consistent during research loops."""
        # Record original phase statuses
        original_phases = sample_workflow_state.phases.copy()
        
        # Do research loop
        await mock_maestro._initiate_research_loop(sample_workflow_state)
        
        # RESEARCH should be IN_PROGRESS, others unchanged except source phase
        assert sample_workflow_state.phases[WorkflowPhase.RESEARCH] == PhaseStatus.IN_PROGRESS
        
        # Complete research loop
        await mock_maestro._complete_research_loop(sample_workflow_state, "drafting")
        
        # Should return to original state (plus RESEARCH completed)
        assert sample_workflow_state.phases[WorkflowPhase.DRAFTING] == PhaseStatus.IN_PROGRESS
        assert sample_workflow_state.phases[WorkflowPhase.RESEARCH] == PhaseStatus.COMPLETED


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])