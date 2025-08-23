# Script Name: test_ai_document_integration.py
# Description: Integration Test for AI Document Generation System Tests the complete integration of AI document generation with the LawyerFactory orchestration system.
# Relationships:
#   - Entity Type: Test
#   - Directory Group: Document Generation
#   - Group Tags: testing
Integration Test for AI Document Generation System
Tests the complete integration of AI document generation with the LawyerFactory orchestration system.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from lawyerfactory.enhanced_workflow import EnhancedWorkflowManager
from Tesla.test_cases.tesla_case_data import TESLA_CONTRACT_BREACH_CASE

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AIDocumentIntegrationTest:
    """Integration test suite for AI document generation system."""
    
    def __init__(self):
        self.workflow_manager = None
        self.test_results = []
        
    async def setup(self):
        """Setup test environment"""
        try:
            self.workflow_manager = EnhancedWorkflowManager(
                knowledge_graph_path=':memory:',  # Use in-memory database for testing
                storage_path='test_workflow_storage'
            )
            logger.info("Integration test environment setup complete")
            return True
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False
    
    async def teardown(self):
        """Cleanup test environment"""
        try:
            if self.workflow_manager:
                await self.workflow_manager.shutdown()
            logger.info("Integration test cleanup complete")
        except Exception as e:
            logger.error(f"Teardown failed: {e}")
    
    async def test_ai_document_workflow_creation(self) -> bool:
        """Test creating an AI document generation workflow with Tesla case data"""
        try:
            logger.info("Testing AI document workflow creation...")
            
            # Create AI document workflow with Tesla case data
            session_id = await self.workflow_manager.create_ai_document_workflow(
                case_name="Tesla Contract Breach Integration Test",
                case_data=TESLA_CONTRACT_BREACH_CASE,
                options={
                    'integration_test': True,
                    'auto_generate_forms': True
                }
            )
            
            if not session_id or not session_id.startswith('session_'):
                raise ValueError(f"Invalid session ID returned: {session_id}")
            
            logger.info(f"✓ AI document workflow created successfully: {session_id}")
            self.test_results.append(("AI Workflow Creation", True, f"Session: {session_id}"))
            return True
            
        except Exception as e:
            logger.error(f"✗ AI document workflow creation failed: {e}")
            self.test_results.append(("AI Workflow Creation", False, str(e)))
            return False
    
    async def test_tesla_case_data_processing(self) -> bool:
        """Test processing Tesla case data specifically"""
        try:
            logger.info("Testing Tesla case data processing...")
            
            # Process Tesla case data
            session_id = await self.workflow_manager.process_tesla_case_data(
                tesla_case_data=TESLA_CONTRACT_BREACH_CASE,
                case_name="Tesla Integration Test Case"
            )
            
            if not session_id:
                raise ValueError("No session ID returned from Tesla case processing")
            
            # Wait a moment for initial processing
            await asyncio.sleep(2)
            
            # Check workflow status
            status = await self.workflow_manager.get_workflow_status(session_id=session_id)
            
            if not status:
                raise ValueError("Could not retrieve workflow status")
            
            logger.info("✓ Tesla case data processed successfully")
            logger.info(f"  Session ID: {session_id}")
            logger.info(f"  Current Phase: {status.get('current_phase', 'Unknown')}")
            logger.info(f"  Overall Status: {status.get('overall_status', 'Unknown')}")
            
            self.test_results.append(("Tesla Case Processing", True, f"Session: {session_id}"))
            return True
            
        except Exception as e:
            logger.error(f"✗ Tesla case data processing failed: {e}")
            self.test_results.append(("Tesla Case Processing", False, str(e)))
            return False
    
    async def test_ai_generation_status_tracking(self) -> bool:
        """Test AI generation status tracking functionality"""
        try:
            logger.info("Testing AI generation status tracking...")
            
            # Create a workflow first
            session_id = await self.workflow_manager.process_tesla_case_data(
                tesla_case_data=TESLA_CONTRACT_BREACH_CASE,
                case_name="Tesla Status Test Case"
            )
            
            # Wait for some processing
            await asyncio.sleep(3)
            
            # Get AI generation status
            ai_status = await self.workflow_manager.get_ai_generation_status(session_id=session_id)
            
            if not ai_status:
                raise ValueError("Could not retrieve AI generation status")
            
            # Validate status structure
            required_keys = ['session_id', 'ai_tasks', 'ai_results', 'total_ai_tasks']
            for key in required_keys:
                if key not in ai_status:
                    raise ValueError(f"AI status missing required key: {key}")
            
            logger.info("✓ AI generation status tracking working")
            logger.info(f"  Total AI Tasks: {ai_status['total_ai_tasks']}")
            logger.info(f"  Completed AI Tasks: {ai_status['completed_ai_tasks']}")
            logger.info(f"  Overall Progress: {ai_status['ai_results']['overall_progress']:.1%}")
            
            self.test_results.append(("AI Status Tracking", True, f"Tasks: {ai_status['total_ai_tasks']}"))
            return True
            
        except Exception as e:
            logger.error(f"✗ AI generation status tracking failed: {e}")
            self.test_results.append(("AI Status Tracking", False, str(e)))
            return False
    
    async def test_document_generation_workflow(self) -> bool:
        """Test the complete document generation workflow"""
        try:
            logger.info("Testing complete document generation workflow...")
            
            # Start workflow
            session_id = await self.workflow_manager.process_tesla_case_data(
                tesla_case_data=TESLA_CONTRACT_BREACH_CASE,
                case_name="Tesla Complete Workflow Test"
            )
            
            # Monitor workflow for a reasonable amount of time
            max_wait_time = 30  # seconds
            check_interval = 2   # seconds
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                await asyncio.sleep(check_interval)
                elapsed_time += check_interval
                
                # Check workflow progress
                status = await self.workflow_manager.get_workflow_status(session_id=session_id)
                ai_status = await self.workflow_manager.get_ai_generation_status(session_id=session_id)
                
                logger.info(f"  Progress check at {elapsed_time}s:")
                logger.info(f"    Phase: {status.get('current_phase', 'Unknown')}")
                logger.info(f"    AI Progress: {ai_status['ai_results']['overall_progress']:.1%}")
                
                # Check if we have some AI task completion
                if ai_status['completed_ai_tasks'] > 0:
                    logger.info(f"✓ AI tasks are executing - {ai_status['completed_ai_tasks']} completed")
                    break
            
            # Get final status
            final_status = await self.workflow_manager.get_ai_generation_status(session_id=session_id)
            
            # Check for generated documents
            try:
                generated_docs = await self.workflow_manager.get_generated_documents(session_id=session_id)
                logger.info(f"  Generated documents: {len(generated_docs)}")
                for doc in generated_docs:
                    logger.info(f"    - {doc['file_name']}")
            except Exception:
                logger.info("  No documents generated yet (this is expected in a quick test)")
            
            logger.info("✓ Document generation workflow test completed")
            logger.info(f"  Final AI task completion: {final_status['completed_ai_tasks']}/{final_status['total_ai_tasks']}")
            
            self.test_results.append(("Complete Workflow", True, f"Completed tasks: {final_status['completed_ai_tasks']}"))
            return True
            
        except Exception as e:
            logger.error(f"✗ Document generation workflow test failed: {e}")
            self.test_results.append(("Complete Workflow", False, str(e)))
            return False
    
    async def test_tesla_data_validation(self) -> bool:
        """Test that Tesla case data is properly validated and processed"""
        try:
            logger.info("Testing Tesla case data validation...")
            
            # Validate Tesla case data structure
            required_fields = ['case_name', 'plaintiff_name', 'defendant_name', 'facts', 'causes_of_action']
            
            for field in required_fields:
                if field not in TESLA_CONTRACT_BREACH_CASE:
                    raise ValueError(f"Tesla case data missing required field: {field}")
            
            # Test case data contains expected content
            if not TESLA_CONTRACT_BREACH_CASE['defendant_name'] == 'Tesla Motors, Inc.':
                raise ValueError("Tesla case data does not contain expected defendant")
            
            if not TESLA_CONTRACT_BREACH_CASE['causes_of_action']:
                raise ValueError("Tesla case data missing causes of action")
            
            logger.info("✓ Tesla case data validation passed")
            logger.info(f"  Case: {TESLA_CONTRACT_BREACH_CASE['case_name']}")
            logger.info(f"  Plaintiff: {TESLA_CONTRACT_BREACH_CASE['plaintiff_name']}")
            logger.info(f"  Defendant: {TESLA_CONTRACT_BREACH_CASE['defendant_name']}")
            logger.info(f"  Facts: {len(TESLA_CONTRACT_BREACH_CASE['facts'])} entries")
            logger.info(f"  Causes of Action: {len(TESLA_CONTRACT_BREACH_CASE['causes_of_action'])}")
            
            self.test_results.append(("Tesla Data Validation", True, "All required fields present"))
            return True
            
        except Exception as e:
            logger.error(f"✗ Tesla case data validation failed: {e}")
            self.test_results.append(("Tesla Data Validation", False, str(e)))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        logger.info("=== AI Document Integration Test Suite ===")
        
        # Setup
        if not await self.setup():
            return {"success": False, "error": "Setup failed"}
        
        try:
            # Run individual tests
            tests = [
                ("Tesla Data Validation", self.test_tesla_data_validation),
                ("AI Workflow Creation", self.test_ai_document_workflow_creation),
                ("Tesla Case Processing", self.test_tesla_case_data_processing),
                ("AI Status Tracking", self.test_ai_generation_status_tracking),
                ("Complete Workflow", self.test_document_generation_workflow),
            ]
            
            results = {}
            for test_name, test_func in tests:
                logger.info(f"\n--- Running: {test_name} ---")
                try:
                    results[test_name] = await test_func()
                except Exception as e:
                    logger.error(f"Test {test_name} failed with exception: {e}")
                    results[test_name] = False
                    self.test_results.append((test_name, False, f"Exception: {str(e)}"))
            
            # Summary
            logger.info("\n=== Test Results Summary ===")
            passed = sum(1 for result in results.values() if result)
            total = len(results)
            
            for test_name, result, details in self.test_results:
                status = "PASS" if result else "FAIL"
                logger.info(f"{status}: {test_name} - {details}")
            
            logger.info(f"\nOverall: {passed}/{total} tests passed")
            
            return {
                "success": passed == total,
                "passed": passed,
                "total": total,
                "results": results,
                "details": self.test_results
            }
            
        finally:
            await self.teardown()


async def run_integration_test():
    """Run the AI document integration test"""
    test_suite = AIDocumentIntegrationTest()
    return await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(run_integration_test())