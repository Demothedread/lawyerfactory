# Script Name: test_claims_matrix.py
# Description: !/usr/bin/env python3
# Relationships:
#   - Entity Type: Test
#   - Directory Group: Core
#   - Group Tags: claims-analysis, testing
Test script for Claims Matrix Interactive Frontend
Tests the integration between frontend JavaScript and backend API
"""

import logging
import os
import sys

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test server configuration
TEST_SERVER_URL = os.getenv('TEST_SERVER_URL', 'http://localhost:5000')


class ClaimsMatrixTester:
    """Test harness for Claims Matrix functionality"""
    
    def __init__(self, base_url: str = TEST_SERVER_URL):
        self.base_url = base_url
        self.session_id = None
        
    def test_server_health(self) -> bool:
        """Test if server is running and responsive"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Server is running and responsive")
                return True
            else:
                logger.error(f"❌ Server returned status code: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to server: {e}")
            return False
    
    def test_start_analysis(self) -> bool:
        """Test starting Claims Matrix analysis"""
        try:
            payload = {
                'jurisdiction': 'ca_state',
                'cause_of_action': 'negligence',
                'case_facts': []
            }
            
            response = requests.post(
                f"{self.base_url}/api/claims-matrix/analysis/start",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.session_id = data.get('session_id')
                    logger.info(f"✅ Analysis started successfully with session ID: {self.session_id}")
                    return True
                else:
                    logger.error(f"❌ Analysis start failed: {data.get('error')}")
                    return False
            else:
                logger.error(f"❌ Analysis start returned status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start analysis: {e}")
            return False
    
    def test_get_definition(self) -> bool:
        """Test getting comprehensive definition"""
        if not self.session_id:
            logger.error("❌ No session ID available for definition test")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/api/claims-matrix/definition/{self.session_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    definition = data.get('data', {})
                    elements_count = len(definition.get('elements', []))
                    logger.info(f"✅ Definition retrieved with {elements_count} elements")
                    logger.info(f"   Cause of Action: {definition.get('cause_of_action')}")
                    logger.info(f"   Jurisdiction: {definition.get('jurisdiction')}")
                    return True
                else:
                    logger.error(f"❌ Definition retrieval failed: {data.get('error')}")
                    return False
            else:
                logger.error(f"❌ Definition request returned status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to get definition: {e}")
            return False
    
    def test_get_decision_tree(self) -> bool:
        """Test getting decision tree for element"""
        if not self.session_id:
            logger.error("❌ No session ID available for decision tree test")
            return False
        
        try:
            element_id = "element_duty"  # Test with duty element
            response = requests.get(
                f"{self.base_url}/api/claims-matrix/decision-tree/{self.session_id}/{element_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    tree_data = data.get('data', {})
                    questions_count = len(tree_data.get('questions', []))
                    logger.info(f"✅ Decision tree retrieved with {questions_count} questions")
                    logger.info(f"   Element: {tree_data.get('element_name')}")
                    return True
                else:
                    logger.error(f"❌ Decision tree retrieval failed: {data.get('error')}")
                    return False
            else:
                logger.error(f"❌ Decision tree request returned status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to get decision tree: {e}")
            return False
    
    def test_get_facts(self) -> bool:
        """Test getting knowledge graph facts"""
        try:
            response = requests.get(
                f"{self.base_url}/api/knowledge-graph/facts",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    facts_count = len(data.get('facts', []))
                    logger.info(f"✅ Facts retrieved: {facts_count} available")
                    return True
                else:
                    logger.error(f"❌ Facts retrieval failed: {data.get('error')}")
                    return False
            else:
                logger.error(f"❌ Facts request returned status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to get facts: {e}")
            return False
    
    def test_frontend_resources(self) -> bool:
        """Test that frontend resources are accessible"""
        try:
            # Test main HTML page
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code != 200:
                logger.error(f"❌ Main page not accessible: {response.status_code}")
                return False
            
            # Check if Claims Matrix tab is present in HTML
            if 'Claims Matrix' not in response.text:
                logger.error("❌ Claims Matrix tab not found in HTML")
                return False
            
            # Test Claims Matrix JavaScript module
            response = requests.get(f"{self.base_url}/static/js/claims-matrix.js", timeout=5)
            if response.status_code != 200:
                logger.error(f"❌ Claims Matrix JS module not accessible: {response.status_code}")
                return False
            
            # Check if ClaimsMatrixManager class is present
            if 'class ClaimsMatrixManager' not in response.text:
                logger.error("❌ ClaimsMatrixManager class not found in JS module")
                return False
            
            logger.info("✅ Frontend resources accessible")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to test frontend resources: {e}")
            return False
    
    def test_term_expansion(self) -> bool:
        """Test clickable term expansion"""
        try:
            term_text = "negligence"
            response = requests.get(
                f"{self.base_url}/api/claims-matrix/term/{term_text}",
                params={'context': 'tort_law'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    term_data = data.get('data', {})
                    logger.info(f"✅ Term expansion successful for: {term_data.get('term_text')}")
                    return True
                else:
                    logger.error(f"❌ Term expansion failed: {data.get('error')}")
                    return False
            else:
                logger.error(f"❌ Term expansion returned status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to test term expansion: {e}")
            return False
    
    def run_all_tests(self) -> dict:
        """Run comprehensive test suite"""
        logger.info("🚀 Starting Claims Matrix Test Suite")
        logger.info("=" * 50)
        
        results = {
            'server_health': self.test_server_health(),
            'frontend_resources': self.test_frontend_resources(),
            'start_analysis': self.test_start_analysis(),
            'get_definition': self.test_get_definition(),
            'get_decision_tree': self.test_get_decision_tree(),
            'get_facts': self.test_get_facts(),
            'term_expansion': self.test_term_expansion()
        }
        
        # Summary
        passed = sum(results.values())
        total = len(results)
        
        logger.info("=" * 50)
        logger.info(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Claims Matrix is ready for use.")
        else:
            logger.warning("⚠️  Some tests failed. Check the logs above for details.")
            for test_name, result in results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"   {test_name}: {status}")
        
        return results


def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    else:
        server_url = TEST_SERVER_URL
    
    logger.info(f"Testing Claims Matrix at: {server_url}")
    
    tester = ClaimsMatrixTester(server_url)
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure


if __name__ == '__main__':
    main()