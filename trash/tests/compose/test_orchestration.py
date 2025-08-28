# Script Name: test_orchestration.py
# Description: Test script for the enhanced maestro orchestration system. Validates the core functionality and integration with the knowledge graph.
# Relationships:
#   - Entity Type: Test
#   - Directory Group: Orchestration
#   - Group Tags: testing
Test script for the enhanced maestro orchestration system.
Validates the core functionality and integration with the knowledge graph.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Configure logging to /logs subdirectory
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f'orchestration_{os.getpid()}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add project paths for subdirectory
sys.path.append(str(Path(__file__).parent.parent))

try:
    from knowledge_graph import KnowledgeGraph
    from lawyerfactory.enhanced_workflow import EnhancedWorkflowManager
    from maestro.enhanced_maestro import EnhancedMaestro
    from maestro.workflow_models import PhaseStatus, WorkflowPhase
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info("Running simple validation instead...")

    # Provide lightweight stubs so static analysis and later references don't see these names as unbound.
    # At runtime these stubs will raise informative errors when the real modules are missing.
    class _MissingDependencyError(RuntimeError):
        pass

    class KnowledgeGraph:
        def __init__(self, *args, **kwargs):
            raise _MissingDependencyError(
                "knowledge_graph module is not available. "
                "Ensure the package is installed and PYTHONPATH includes the project root."
            )

    class EnhancedMaestro:
        def __init__(self, *args, **kwargs):
            raise _MissingDependencyError(
                "maestro.enhanced_maestro is not available. Install/enable the maestro package."
            )

        async def start_workflow(self, *args, **kwargs):
            raise _MissingDependencyError("maestro.enhanced_maestro is not available.")

        async def get_workflow_status(self, *args, **kwargs):
            raise _MissingDependencyError("maestro.enhanced_maestro is not available.")

        async def list_workflows(self, *args, **kwargs):
            raise _MissingDependencyError("maestro.enhanced_maestro is not available.")

        async def shutdown(self, *args, **kwargs):
            return

    class EnhancedWorkflowManager:
        def __init__(self, *args, **kwargs):
            raise _MissingDependencyError(
                "lawyerfactory.enhanced_workflow is not available. Ensure lawyerfactory package is importable."
            )

    # Minimal enums/constants to satisfy references in tests when real package isn't present.
    class PhaseStatus:
        PENDING = "PENDING"
        COMPLETED = "COMPLETED"
        FAILED = "FAILED"

    class WorkflowPhase:
        INTAKE = "INTAKE"
        PROCESSING = "PROCESSING"
        COMPLETED = "COMPLETED"


async def test_workflow_models():
    """Test the workflow models and state management"""
    print("\n=== Testing Workflow Models ===")
    
    try:
        from maestro.workflow_models import (TaskPriority,
                                             WorkflowStateManager,
                                             WorkflowTask)

        # Test state manager
        state_manager = WorkflowStateManager(":memory:")  # Use in-memory SQLite for testing
        
        # Create a test workflow state
        from maestro.workflow_models import WorkflowState
        workflow_state = WorkflowState(
            "test_session_123",
            "Test Case",
            WorkflowPhase.INTAKE,
            PhaseStatus.PENDING
        )
        
        # Add some test tasks
        task1 = WorkflowTask(
            id="task_1",
            phase=WorkflowPhase.INTAKE,
            agent_type="ReaderBot",
            description="Test document processing",
            priority=TaskPriority.HIGH
        )
        
        workflow_state.tasks[task1.id] = task1
        
        # Test serialization
        state_dict = workflow_state.to_dict()
        restored_state = WorkflowState.from_dict(state_dict)
        
        assert restored_state.session_id == workflow_state.session_id
        assert restored_state.case_name == workflow_state.case_name
        assert len(restored_state.tasks) == 1
        
        # Test state persistence
        await state_manager.save_state(workflow_state)
        loaded_state = await state_manager.load_state("test_session_123")
        
        assert loaded_state.session_id == workflow_state.session_id
        assert len(loaded_state.tasks) == 1
        
        print("✓ Workflow models working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Workflow models test failed: {e}")
        return False


async def test_agent_registry():
    """Test the agent registry and mock agents"""
    print("\n=== Testing Agent Registry ===")
    
    try:
        from maestro.agent_registry import AgentRegistry, MockAgentInterface
        from maestro.workflow_models import WorkflowPhase, WorkflowTask

        # Create registry
        registry = AgentRegistry()
        
        # Test getting an agent
        reader_bot = await registry.get_agent("ReaderBot")
        assert isinstance(reader_bot, MockAgentInterface)
        
        # Test agent status
        status = registry.get_agent_status()
        assert "ReaderBot" in status
        assert status["ReaderBot"]["instances"] >= 1
        
        # Test task execution
        test_task = WorkflowTask(
            id="test_task_1",
            phase=WorkflowPhase.INTAKE,
            agent_type="ReaderBot",
            description="Test task"
        )
        
        context = {
            'session_id': 'test_session',
            'case_name': 'Test Case',
            'input_documents': ['test.pdf']
        }
        
        result = await reader_bot.execute_task(test_task, context)
        assert isinstance(result, dict)
        assert 'entities_extracted' in result
        
        # Clean up
        await registry.shutdown_all_agents()
        
        print("✓ Agent registry working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Agent registry test failed: {e}")
        return False


async def test_knowledge_graph_integration():
    """Test knowledge graph integration"""
    print("\n=== Testing Knowledge Graph Integration ===")
    
    try:
        # Test basic knowledge graph functionality
        kg = KnowledgeGraph(":memory:")  # Use in-memory database for testing
        
        # Test basic operations
        count_before = kg._fetchone("SELECT COUNT(*) FROM entities")[0]
        logger.info(f"Initial entity count: {count_before}")
        
        print("✓ Knowledge graph connection working")
        return True
        
    except Exception as e:
        print(f"✗ Knowledge graph test failed: {e}")
        return False


async def test_enhanced_maestro():
    """Test the enhanced maestro orchestration"""
    print("\n=== Testing Enhanced Maestro ===")
    
    try:
        # Create a temporary knowledge graph
        kg = KnowledgeGraph(":memory:")
        
        # Create maestro instance
        maestro = EnhancedMaestro(
            knowledge_graph=kg,
            storage_path=":memory:"
        )
        
        # Test workflow creation
        session_id = await maestro.start_workflow(
            case_name="Test Orchestration Case",
            input_documents=["test1.pdf", "test2.pdf"],
            initial_context={"test": True}
        )
        
        assert session_id.startswith("session_")
        
        # Wait a moment for initial processing
        await asyncio.sleep(1)
        
        # Test status retrieval
        status = await maestro.get_workflow_status(session_id)
        assert status['case_name'] == "Test Orchestration Case"
        assert status['current_phase'] == WorkflowPhase.INTAKE.value
        
        # Test workflow listing
        workflows = await maestro.list_workflows()
        assert len(workflows) >= 1
        
        # Clean up
        await maestro.shutdown()
        
        print("✓ Enhanced maestro working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Enhanced maestro test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_workflow_manager():
    """Test the enhanced workflow manager"""
    print("\n=== Testing Enhanced Workflow Manager ===")
    
    try:
        # This would test the full workflow manager, but requires file system access
        # For now, just test that it can be imported and initialized
        workflow_manager = EnhancedWorkflowManager(
            knowledge_graph_path=":memory:",
            storage_path="test_storage"
        )
        
        # Test basic functionality
        workflows = await workflow_manager.list_workflows()
        assert isinstance(workflows, list)
        
        await workflow_manager.shutdown()
        
        print("✓ Enhanced workflow manager working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Enhanced workflow manager test failed: {e}")
        return False


async def run_integration_test():
    """Run a comprehensive integration test"""
    print("\n=== Running Integration Test ===")
    
    try:
        # Create components
        kg = KnowledgeGraph(":memory:")
        maestro = EnhancedMaestro(knowledge_graph=kg, storage_path="test_storage")
        
        # Start a workflow
        session_id = await maestro.start_workflow(
            case_name="Integration Test Case",
            input_documents=[],  # No actual files for testing
            initial_context={"test_mode": True}
        )
        
        print(f"Started integration test workflow: {session_id}")
        
        # Monitor progress for a few seconds
        for i in range(3):
            await asyncio.sleep(1)
            status = await maestro.get_workflow_status(session_id)
            print(f"  Status check {i+1}: {status['current_phase']} - {status['progress_percentage']:.1f}%")
        
        # Clean up
        await maestro.shutdown()
        
        print("✓ Integration test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("🚀 LawyerFactory Orchestration System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Workflow Models", test_workflow_models),
        ("Agent Registry", test_agent_registry),
        ("Knowledge Graph", test_knowledge_graph_integration),
        ("Enhanced Maestro", test_enhanced_maestro),
        ("Workflow Manager", test_workflow_manager),
        ("Integration Test", run_integration_test),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status:8} {test_name}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! The orchestration system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)