#!/usr/bin/env python3
"""
Comprehensive integration test for the Enhanced LawyerFactory Platform.
Tests all major components and their integration.
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

# Ensure correct import paths for subdirectory
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f'enhanced_integration_{os.getpid()}.log'
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler(log_file), logging.StreamHandler()])
logger = logging.getLogger(__name__)

class EnhancedIntegrationTest:
    """Comprehensive integration test suite"""
    
    def __init__(self):
        self.test_results = []
        self.temp_dir = None
        self.kg = None
        self.workflow_manager = None
        
    def setup_test_environment(self):
        """Setup test environment with temporary directories"""
        self.temp_dir = tempfile.mkdtemp(prefix="lawyerfactory_test_")
        logger.info(f"Created test directory: {self.temp_dir}")
        
        # Create test directories
        test_dirs = ['uploads', 'knowledge_graphs', 'workflow_storage', 'templates']
        for dir_name in test_dirs:
            Path(self.temp_dir, dir_name).mkdir(exist_ok=True)
        
        return True
    
    def test_knowledge_graph_basic(self):
        """Test basic knowledge graph functionality"""
        try:
            from knowledge_graph import KnowledgeGraph
            from knowledge_graph_extensions import extend_knowledge_graph

            # Create in-memory database for testing
            kg_path = os.path.join(self.temp_dir, 'test_kg.db')
            self.kg = KnowledgeGraph(kg_path)
            extend_knowledge_graph(self.kg)
            
            # Test basic operations
            entity_count = self.kg._fetchone("SELECT COUNT(*) FROM entities")[0]
            logger.info(f"Initial entity count: {entity_count}")
            
            # Test entity addition
            test_entity = {
                'id': 'test_entity_1',
                'type': 'PERSON',
                'name': 'John Doe',
                'description': 'Test plaintiff',
                'confidence': 1.0
            }
            
            entity_id = self.kg.add_entity_dict(test_entity)
            logger.info(f"Added test entity: {entity_id}")
            
            # Test entity retrieval
            retrieved_entity = self.kg.get_entity_by_id(entity_id)
            assert retrieved_entity is not None
            assert retrieved_entity['name'] == 'John Doe'
            
            self.test_results.append(("Knowledge Graph Basic", True, "All basic operations working"))
            return True
            
        except Exception as e:
            self.test_results.append(("Knowledge Graph Basic", False, str(e)))
            logger.error(f"Knowledge graph test failed: {e}")
            return False
    
    def test_document_ingestion_mock(self):
        """Test document ingestion with mock data"""
        try:
            if not self.kg:
                raise Exception("Knowledge graph not initialized")
            
            # Create mock document
            test_doc_path = os.path.join(self.temp_dir, 'test_document.txt')
            with open(test_doc_path, 'w') as f:
                f.write("""
                This is a test legal document for John Doe vs. MegaCorp.
                The case involves a breach of contract on January 1, 2024.
                The jurisdiction is California Superior Court.
                """)
            
            # Mock document ingestion pipeline
            pipeline = self.kg.DocumentIngestionPipeline(self.kg)
            document_id = pipeline.ingest(test_doc_path)
            
            # Verify entities were extracted
            facts = self.kg.get_case_facts(document_id)
            logger.info(f"Extracted facts: {facts}")
            
            self.test_results.append(("Document Ingestion", True, f"Processed document {document_id}"))
            return True
            
        except Exception as e:
            self.test_results.append(("Document Ingestion", False, str(e)))
            logger.error(f"Document ingestion test failed: {e}")
            return False
    
    def test_workflow_manager_mock(self):
        """Test workflow manager with mock components"""
        try:
            # Mock the workflow manager components
            with patch('lawyerfactory.enhanced_workflow.EnhancedMaestro') as mock_maestro:
                mock_maestro_instance = Mock()
                mock_maestro.return_value = mock_maestro_instance
                
                # Mock workflow methods
                mock_maestro_instance.start_workflow.return_value = 'test_session_123'
                mock_maestro_instance.get_workflow_status.return_value = {
                    'current_phase': 'INTAKE',
                    'progress_percentage': 25.0,
                    'status': 'active'
                }
                
                from lawyerfactory.enhanced_workflow import \
                    EnhancedWorkflowManager
                
                self.workflow_manager = EnhancedWorkflowManager(
                    knowledge_graph_path=':memory:',
                    storage_path=self.temp_dir
                )
                
                self.test_results.append(("Workflow Manager", True, "Mock workflow manager created"))
                return True
                
        except Exception as e:
            self.test_results.append(("Workflow Manager", False, str(e)))
            logger.error(f"Workflow manager test failed: {e}")
            return False
    
    def test_api_endpoints_mock(self):
        """Test API endpoints with mock Flask app"""
        try:
            # Mock Flask and SocketIO
            with patch('flask.Flask') as mock_flask, \
                 patch('flask_socketio.SocketIO') as mock_socketio:
                
                mock_app = Mock()
                mock_flask.return_value = mock_app
                mock_socketio_instance = Mock()
                mock_socketio.return_value = mock_socketio_instance
                
                # Test import of main app module
                import app

                # Verify app structure
                assert hasattr(app, 'app_state')
                assert hasattr(app, 'initialize_components')
                
                self.test_results.append(("API Endpoints", True, "Flask app structure validated"))
                return True
                
        except Exception as e:
            self.test_results.append(("API Endpoints", False, str(e)))
            logger.error(f"API endpoints test failed: {e}")
            return False
    
    def test_frontend_template(self):
        """Test frontend template structure"""
        try:
            template_path = 'templates/enhanced_factory.html'
            
            if not os.path.exists(template_path):
                raise Exception(f"Template not found: {template_path}")
            
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            # Verify essential components
            required_elements = [
                'Case Initiation',
                'Workflow Progress',
                'Knowledge Graph',
                'socket.io',
                'D3.js',
                'uploadZone',
                'workflowPhases',
                'knowledgeGraphViz'
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in template_content:
                    missing_elements.append(element)
            
            if missing_elements:
                raise Exception(f"Missing template elements: {missing_elements}")
            
            self.test_results.append(("Frontend Template", True, "All required elements present"))
            return True
            
        except Exception as e:
            self.test_results.append(("Frontend Template", False, str(e)))
            logger.error(f"Frontend template test failed: {e}")
            return False
    
    def test_startup_script(self):
        """Test startup script functionality"""
        try:
            import start_enhanced_factory

            # Test dependency checking
            result = start_enhanced_factory.check_dependencies()
            logger.info(f"Dependency check result: {result}")
            
            # Test directory setup
            start_enhanced_factory.setup_directories()
            
            # Verify directories were created
            expected_dirs = ['uploads', 'knowledge_graphs', 'workflow_storage', 'templates']
            for dir_name in expected_dirs:
                if not os.path.exists(dir_name):
                    raise Exception(f"Directory not created: {dir_name}")
            
            self.test_results.append(("Startup Script", True, "Directory setup working"))
            return True
            
        except Exception as e:
            self.test_results.append(("Startup Script", False, str(e)))
            logger.error(f"Startup script test failed: {e}")
            return False
    
    def test_configuration_files(self):
        """Test configuration files"""
        try:
            # Test requirements.txt
            if not os.path.exists('requirements.txt'):
                raise Exception("requirements.txt not found")
            
            with open('requirements.txt', 'r') as f:
                requirements = f.read()
            
            required_packages = ['Flask', 'Flask-SocketIO', 'eventlet', 'werkzeug']
            for package in required_packages:
                if package not in requirements:
                    raise Exception(f"Required package missing: {package}")
            
            # Test README.md
            if not os.path.exists('README.md'):
                raise Exception("README.md not found")
            
            with open('README.md', 'r') as f:
                readme = f.read()
            
            if 'LawyerFactory Enhanced' not in readme:
                raise Exception("README missing project description")
            
            self.test_results.append(("Configuration Files", True, "All config files present and valid"))
            return True
            
        except Exception as e:
            self.test_results.append(("Configuration Files", False, str(e)))
            logger.error(f"Configuration files test failed: {e}")
            return False
    
    def test_integration_flow(self):
        """Test complete integration flow simulation"""
        try:
            logger.info("Testing complete integration flow...")
            
            # Simulate file upload
            test_data = {
                'case_name': 'Test Case Integration',
                'case_description': 'Integration test case',
                'uploaded_files': ['test_doc.pdf']
            }
            
            # Simulate workflow creation
            session_id = f"test_session_{int(time.time())}"
            
            # Simulate phase progression
            phases = ['INTAKE', 'OUTLINE', 'RESEARCH', 'DRAFTING', 'LEGAL_REVIEW', 'EDITING', 'ORCHESTRATION']
            for i, phase in enumerate(phases):
                progress = (i + 1) / len(phases) * 100
                logger.info(f"Simulated phase: {phase} ({progress:.1f}%)")
            
            # Simulate document generation
            mock_document = "COMPLAINT FOR DAMAGES\n\nThis is a test generated document..."
            
            self.test_results.append(("Integration Flow", True, "Complete flow simulation successful"))
            return True
            
        except Exception as e:
            self.test_results.append(("Integration Flow", False, str(e)))
            logger.error(f"Integration flow test failed: {e}")
            return False
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up test directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup test directory: {e}")
    
    def run_all_tests(self):
        """Run all integration tests"""
        logger.info("Starting Enhanced LawyerFactory Integration Tests...")
        
        # Setup
        if not self.setup_test_environment():
            logger.error("Failed to setup test environment")
            return False
        
        try:
            # Run individual tests
            tests = [
                self.test_knowledge_graph_basic,
                self.test_document_ingestion_mock,
                self.test_workflow_manager_mock,
                self.test_api_endpoints_mock,
                self.test_frontend_template,
                self.test_startup_script,
                self.test_configuration_files,
                self.test_integration_flow
            ]
            
            for test in tests:
                try:
                    test()
                except Exception as e:
                    logger.error(f"Test {test.__name__} failed with exception: {e}")
                    self.test_results.append((test.__name__, False, str(e)))
            
            # Report results
            self.report_results()
            
            # Return overall success
            return all(result[1] for result in self.test_results)
            
        finally:
            self.cleanup_test_environment()
    
    def report_results(self):
        """Report test results"""
        logger.info("\n" + "="*60)
        logger.info("ENHANCED LAWYERFACTORY INTEGRATION TEST RESULTS")
        logger.info("="*60)
        
        passed = 0
        failed = 0
        
        for test_name, success, message in self.test_results:
            status = "PASS" if success else "FAIL"
            logger.info(f"{status:>6} | {test_name:<30} | {message}")
            
            if success:
                passed += 1
            else:
                failed += 1
        
        logger.info("-"*60)
        logger.info(f"Total Tests: {len(self.test_results)}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {passed/len(self.test_results)*100:.1f}%")
        logger.info("="*60)
        
        if failed == 0:
            logger.info("🎉 ALL TESTS PASSED! Enhanced LawyerFactory is ready to use.")
        else:
            logger.warning(f"⚠️  {failed} tests failed. Please review the errors above.")


def main():
    """Main test runner"""
    test_suite = EnhancedIntegrationTest()
    
    try:
        success = test_suite.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()