# Script Name: test_research_loop_integration.py
# Description: Integration tests for iterative research loop functionality in EnhancedMaestro.  This module tests the ability of the workflow to transition backward from later phases (like DRAFTING) to the RESEARCH phase when research_needed flags are detected.
# Relationships:
#   - Entity Type: Test
#   - Directory Group: Research
#   - Group Tags: legal-research, testing
Integration tests for iterative research loop functionality in EnhancedMaestro.

This module tests the ability of the workflow to transition backward from later phases
(like DRAFTING) to the RESEARCH phase when research_needed flags are detected.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# Import the workflow components
from src.lawyerfactory.compose.maestro.enhanced_maestro import EnhancedMaestro
from src.lawyerfactory.phases.phaseC02_orchestration.workflow_models import (
    WorkflowState, WorkflowTask, WorkflowPhase, PhaseStatus, TaskStatus
)


@pytest.fixture
def mock_knowledge_graph():
    """Mock knowledge graph for testing."""
    kg = Mock()
    kg.get_entities.return_value = []
    kg.add_entity = Mock()
    kg.query = Mock(return_value=[])
    return kg


@pytest.fixture
def sample_workflow_state():
    """Create a sample workflow state for testing research loops."""
    return WorkflowState(
        workflow_id="test-research-loop-001",
        current_phase=WorkflowPhase.DRAFTING,
        phases={
            WorkflowPhase.INTAKE: PhaseStatus.COMPLETED,
            WorkflowPhase.RESEARCH: PhaseStatus.COMPLETED,
            WorkflowPhase.OUTLINE: PhaseStatus.COMPLETED,
            WorkflowPhase.DRAFTING: PhaseStatus.IN_PROGRESS,
            WorkflowPhase.POST_PRODUCTION: PhaseStatus.PENDING
        },
        tasks=[
            WorkflowTask(
                id="task-1",
                phase=WorkflowPhase.DRAFTING,
                title="Draft complaint document",
                status=TaskStatus.IN_PROGRESS,
                research_needed=True,  # This should trigger research loop
                research_questions=[
                    "What is the statute of limitations for contract disputes in California?",
                    "Are there recent precedents for similar breach of contract cases?"
                ]
            )
        ],
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
def enhanced_maestro(mock_knowledge_graph):
    """Create EnhancedMaestro instance for testing."""
    maestro = EnhancedMaestro(knowledge_graph=mock_knowledge_graph)
    return maestro


class TestResearchLoopDetection:
    """Test detection of research_needed flags in workflow tasks."""
    
    @pytest.mark.asyncio
    async def test_check_research_needed_with_flagged_task(self, enhanced_maestro, sample_workflow_state):
        """Test that _check_research_needed detects tasks with research_needed=True."""
        # Call the method
        result = await enhanced_maestro._check_research_needed(sample_workflow_state)
        
        # Should return True because task-1 has research_needed=True
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_research_needed_no_flagged_tasks(self, enhanced_maestro, sample_workflow_state):
        """Test that _check_research_needed returns False when no tasks need research."""
        # Modify the task to not need research
        sample_workflow_state.tasks[0].research_needed = False
        
        # Call the method
        result = await enhanced_maestro._check_research_needed(sample_workflow_state)
        
        # Should return False
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_research_needed_empty_tasks(self, enhanced_maestro, mock_knowledge_graph):
        """Test behavior with no tasks in the workflow state."""
        empty_state = WorkflowState(
            workflow_id="empty-test",
            current_phase=WorkflowPhase.DRAFTING,
            phases={WorkflowPhase.DRAFTING: PhaseStatus.IN_PROGRESS},
            tasks=[],
            global_context={},
            research_loop_count=0,
            research_loop_history=[],
            pending_research_questions=[]
        )
        
        result = await enhanced_maestro._check_research_needed(empty_state)
        assert result is False


class TestResearchLoopInitiation:
    """Test initiation of research loops when needed."""
    
    @pytest.mark.asyncio
    async def test_initiate_research_loop_basic(self, enhanced_maestro, sample_workflow_state):
        """Test basic research loop initiation."""
        original_phase = sample_workflow_state.current_phase
        
        # Call initiate research loop
        await enhanced_maestro._initiate_research_loop(sample_workflow_state)
        
        # Verify state changes
        assert sample_workflow_state.current_phase == WorkflowPhase.RESEARCH
        assert sample_workflow_state.research_loop_count == 1
        assert len(sample_workflow_state.research_loop_history) == 1
        
        # Verify research loop history entry
        loop_entry = sample_workflow_state.research_loop_history[0]
        assert loop_entry["source_phase"] == original_phase.value
        assert loop_entry["loop_number"] == 1
        assert loop_entry["status"] == "active"
        assert "started_at" in loop_entry
        
        # Verify pending research questions are populated
        expected_questions = [
            "What is the statute of limitations for contract disputes in California?",
            "Are there recent precedents for similar breach of contract cases?"
        ]
        assert sample_workflow_state.pending_research_questions == expected_questions
    
    @pytest.mark.asyncio
    async def test_initiate_research_loop_multiple_iterations(self, enhanced_maestro, sample_workflow_state):
        """Test that research loop count increments properly on multiple loops."""
        # Simulate previous research loop
        sample_workflow_state.research_loop_count = 2
        sample_workflow_state.research_loop_history = [
            {"loop_number": 1, "status": "completed"},
            {"loop_number": 2, "status": "completed"}
        ]
        
        await enhanced_maestro._initiate_research_loop(sample_workflow_state)
        
        # Should increment to 3
        assert sample_workflow_state.research_loop_count == 3
        assert len(sample_workflow_state.research_loop_history) == 3


class TestResearchLoopExecution:
    """Test execution of research loops."""
    
    @pytest.mark.asyncio
    async def test_handle_research_loop_execution_fallback(self, enhanced_maestro, sample_workflow_state):
        """Test research loop execution with fallback when ResearchBot unavailable."""
        # Set up research loop state
        sample_workflow_state.research_loop_history = [{
            "source_phase": "drafting",
            "research_questions": ["Test question 1", "Test question 2"],
            "loop_number": 1,
            "status": "active"
        }]
        
        # Mock the _complete_research_loop method
        enhanced_maestro._complete_research_loop = AsyncMock()
        
        # Call the method (should use fallback since ResearchBot likely not available)
        await enhanced_maestro._handle_research_loop_execution(sample_workflow_state)
        
        # Verify _complete_research_loop was called
        enhanced_maestro._complete_research_loop.assert_called_once_with(
            sample_workflow_state, "drafting"
        )
    
    @pytest.mark.asyncio
    async def test_handle_research_loop_execution_no_history(self, enhanced_maestro, sample_workflow_state):
        """Test handling when no research loop history exists."""
        # Clear research loop history
        sample_workflow_state.research_loop_history = []
        
        # Should handle gracefully and not crash
        await enhanced_maestro._handle_research_loop_execution(sample_workflow_state)
        
        # No assertions needed - just verify it doesn't crash


class TestResearchLoopCompletion:
    """Test completion and return from research loops."""
    
    @pytest.mark.asyncio
    async def test_complete_research_loop_return_to_drafting(self, enhanced_maestro, sample_workflow_state):
        """Test successful return from research loop to DRAFTING phase."""
        # Set up as if we're in a research loop
        sample_workflow_state.current_phase = WorkflowPhase.RESEARCH
        sample_workflow_state.phases[WorkflowPhase.RESEARCH] = PhaseStatus.IN_PROGRESS
        sample_workflow_state.research_loop_history = [{
            "source_phase": "drafting",
            "loop_number": 1,
            "status": "active"
        }]
        
        # Complete the research loop
        await enhanced_maestro._complete_research_loop(sample_workflow_state, "drafting")
        
        # Verify return to DRAFTING phase
        assert sample_workflow_state.current_phase == WorkflowPhase.DRAFTING
        assert sample_workflow_state.phases[WorkflowPhase.DRAFTING] == PhaseStatus.IN_PROGRESS
        assert sample_workflow_state.phases[WorkflowPhase.RESEARCH] == PhaseStatus.COMPLETED
        
        # Verify research loop history is updated
        loop_entry = sample_workflow_state.research_loop_history[0]
        assert loop_entry["status"] == "completed"
        assert "completed_at" in loop_entry
    
    @pytest.mark.asyncio
    async def test_complete_research_loop_invalid_source_phase(self, enhanced_maestro, sample_workflow_state):
        """Test handling of invalid source phase during research loop completion."""
        sample_workflow_state.current_phase = WorkflowPhase.RESEARCH
        
        # Use invalid source phase
        await enhanced_maestro._complete_research_loop(sample_workflow_state, "invalid_phase")
        
        # Should default to OUTLINE phase
        assert sample_workflow_state.current_phase == WorkflowPhase.OUTLINE


class TestPhaseTransitionWithResearchLoop:
    """Test phase transition logic that includes research loop checks."""
    
    @pytest.mark.asyncio
    async def test_phase_transition_triggers_research_loop(self, enhanced_maestro, sample_workflow_state):
        """Test that phase transitions check for research needs and trigger loops."""
        # Mock the methods that would be called
        enhanced_maestro._check_research_needed = AsyncMock(return_value=True)
        enhanced_maestro._initiate_research_loop = AsyncMock()
        enhanced_maestro._get_next_phase = Mock(return_value=WorkflowPhase.POST_PRODUCTION)
        
        # Call the phase transition method
        await enhanced_maestro._check_phase_transitions(sample_workflow_state)
        
        # Verify research loop was initiated instead of normal phase progression
        enhanced_maestro._check_research_needed.assert_called_once()
        enhanced_maestro._initiate_research_loop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_phase_transition_no_research_needed(self, enhanced_maestro, sample_workflow_state):
        """Test normal phase transition when no research is needed."""
        # Mock the methods
        enhanced_maestro._check_research_needed = AsyncMock(return_value=False)
        enhanced_maestro._initiate_research_loop = AsyncMock()
        enhanced_maestro._get_next_phase = Mock(return_value=WorkflowPhase.POST_PRODUCTION)
        
        # Mark the current phase as complete
        sample_workflow_state.phases[WorkflowPhase.DRAFTING] = PhaseStatus.COMPLETED
        
        # Call the phase transition method
        await enhanced_maestro._check_phase_transitions(sample_workflow_state)
        
        # Verify normal progression occurred
        enhanced_maestro._check_research_needed.assert_called_once()
        enhanced_maestro._initiate_research_loop.assert_not_called()
        
        # Should have moved to next phase
        assert sample_workflow_state.current_phase == WorkflowPhase.POST_PRODUCTION


class TestResearchLoopIntegration:
    """End-to-end integration tests for research loop functionality."""
    
    @pytest.mark.asyncio
    async def test_full_research_loop_cycle(self, enhanced_maestro, sample_workflow_state):
        """Test a complete research loop cycle: detection -> initiation -> execution -> completion."""
        original_phase = sample_workflow_state.current_phase
        
        # Step 1: Check research needed (should be True)
        research_needed = await enhanced_maestro._check_research_needed(sample_workflow_state)
        assert research_needed is True
        
        # Step 2: Initiate research loop
        await enhanced_maestro._initiate_research_loop(sample_workflow_state)
        assert sample_workflow_state.current_phase == WorkflowPhase.RESEARCH
        assert sample_workflow_state.research_loop_count == 1
        
        # Step 3: Execute research loop (with fallback)
        enhanced_maestro._complete_research_loop = AsyncMock()
        await enhanced_maestro._handle_research_loop_execution(sample_workflow_state)
        
        # Step 4: Complete research loop
        await enhanced_maestro._complete_research_loop(sample_workflow_state, original_phase.value)
        assert sample_workflow_state.current_phase == original_phase
        
        # Verify final state
        assert len(sample_workflow_state.research_loop_history) == 1
        assert sample_workflow_state.research_loop_history[0]["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_research_loop_with_evidence_update(self, enhanced_maestro, sample_workflow_state):
        """Test that research loops can update the evidence table."""
        original_evidence_count = len(sample_workflow_state.global_context.get("evidence_table", []))
        
        # Set up research loop state
        sample_workflow_state.research_loop_history = [{
            "source_phase": "drafting",
            "research_questions": ["Test legal question"],
            "loop_number": 1,
            "status": "active"
        }]
        
        # Mock evidence update during research loop execution
        sample_workflow_state.global_context["evidence_table"] = [
            {"citation": "Original Contract", "title": "Service Agreement", "source": "client"},
            {"citation": "New Research Case", "title": "Similar Contract Dispute", "source": "research_loop"}
        ]
        
        # Complete the research loop
        await enhanced_maestro._complete_research_loop(sample_workflow_state, "drafting")
        
        # Verify evidence was preserved
        evidence_table = sample_workflow_state.global_context.get("evidence_table", [])
        assert len(evidence_table) >= original_evidence_count


if __name__ == "__main__":
    # Run basic tests if executed directly
    pytest.main([__file__, "-v"])