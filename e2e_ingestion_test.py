#!/usr/bin/env python3
"""
End-to-End Ingestion Test for LawyerFactory
Tests the complete workflow of file ingestion through API endpoints
"""

import requests
import json
import os
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5000"
TESLA_DATA_PATH = "./Tesla"
TEST_TIMEOUT = 30

class E2EIngestTest:
    def __init__(self):
        self.session = requests.Session()
        self.results = {}
        
    def log(self, message):
        """Log test progress"""
        print(f"[E2E TEST] {message}")
        
    def test_server_health(self):
        """Test if server is responding"""
        try:
            response = self.session.get(f"{BASE_URL}/", timeout=5)
            self.results['server_health'] = response.status_code == 200
            self.log(f"Server health: {'✓' if self.results['server_health'] else '✗'} (Status: {response.status_code})")
            return self.results['server_health']
        except Exception as e:
            self.results['server_health'] = False
            self.log(f"Server health: ✗ (Error: {e})")
            return False
            
    def test_api_endpoints(self):
        """Test all required API endpoints"""
        endpoints = [
            "/api/workflows",
            "/api/knowledge-graph/relationships", 
            "/api/evidence"
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}", timeout=10)
                success = response.status_code in [200, 404]  # 404 is OK for empty data
                self.results[f'endpoint_{endpoint.replace("/", "_")}'] = success
                self.log(f"Endpoint {endpoint}: {'✓' if success else '✗'} (Status: {response.status_code})")
            except Exception as e:
                self.results[f'endpoint_{endpoint.replace("/", "_")}'] = False
                self.log(f"Endpoint {endpoint}: ✗ (Error: {e})")
                
    def test_file_discovery(self):
        """Test if Tesla data files are discoverable"""
        try:
            tesla_path = Path(TESLA_DATA_PATH)
            if not tesla_path.exists():
                self.results['file_discovery'] = False
                self.log("File discovery: ✗ (Tesla directory not found)")
                return False
                
            # Count various file types
            pdf_files = list(tesla_path.rglob("*.pdf"))
            csv_files = list(tesla_path.rglob("*.csv"))
            total_files = len(pdf_files) + len(csv_files)
            
            self.results['file_discovery'] = total_files > 0
            self.results['discovered_files'] = {
                'pdf_count': len(pdf_files),
                'csv_count': len(csv_files),
                'total_count': total_files
            }
            
            self.log(f"File discovery: {'✓' if total_files > 0 else '✗'} ({total_files} files found)")
            self.log(f"  - PDFs: {len(pdf_files)}")
            self.log(f"  - CSVs: {len(csv_files)}")
            
            return self.results['file_discovery']
            
        except Exception as e:
            self.results['file_discovery'] = False
            self.log(f"File discovery: ✗ (Error: {e})")
            return False
            
    def test_file_upload_api(self):
        """Test file upload functionality"""
        try:
            # Find a small test file
            tesla_path = Path(TESLA_DATA_PATH)
            test_files = [f for f in tesla_path.rglob("*.csv") if f.stat().st_size < 50000]  # Small files
            
            if not test_files:
                self.log("File upload: ⚠ (No suitable test files found)")
                self.results['file_upload'] = None
                return None
                
            test_file = test_files[0]
            self.log(f"Testing upload with: {test_file.name}")
            
            # Test if upload endpoint exists
            with open(test_file, 'rb') as f:
                files = {'file': (test_file.name, f, 'text/csv')}
                response = self.session.post(f"{BASE_URL}/api/upload", files=files, timeout=15)
                
            success = response.status_code in [200, 201, 202]  # Accept various success codes
            self.results['file_upload'] = success
            self.results['upload_response'] = response.status_code
            
            self.log(f"File upload: {'✓' if success else '✗'} (Status: {response.status_code})")
            
            if success and response.text:
                try:
                    upload_data = response.json()
                    self.log(f"Upload response: {json.dumps(upload_data, indent=2)}")
                except:
                    self.log(f"Upload response: {response.text[:200]}...")
                    
            return success
            
        except Exception as e:
            self.results['file_upload'] = False
            self.log(f"File upload: ✗ (Error: {e})")
            return False
            
    def test_workflow_creation(self):
        """Test workflow creation through API"""
        try:
            workflow_data = {
                "name": "E2E Test Workflow",
                "description": "Test workflow for end-to-end validation",
                "case_type": "automotive_defect",
                "data_source": "Tesla"
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/workflows", 
                json=workflow_data,
                timeout=10
            )
            
            success = response.status_code in [200, 201, 202]
            self.results['workflow_creation'] = success
            self.results['workflow_response'] = response.status_code
            
            self.log(f"Workflow creation: {'✓' if success else '✗'} (Status: {response.status_code})")
            
            if success and response.text:
                try:
                    workflow_result = response.json()
                    self.results['workflow_id'] = workflow_result.get('id')
                    self.log(f"Created workflow ID: {self.results.get('workflow_id')}")
                except:
                    self.log(f"Workflow response: {response.text[:200]}...")
                    
            return success
            
        except Exception as e:
            self.results['workflow_creation'] = False
            self.log(f"Workflow creation: ✗ (Error: {e})")
            return False
            
    def test_knowledge_graph_integration(self):
        """Test knowledge graph functionality"""
        try:
            # Test relationship query
            response = self.session.get(
                f"{BASE_URL}/api/knowledge-graph/relationships?limit=5",
                timeout=10
            )
            
            success = response.status_code in [200, 404]  # 404 OK for empty graph
            self.results['knowledge_graph'] = success
            
            self.log(f"Knowledge graph: {'✓' if success else '✗'} (Status: {response.status_code})")
            
            if success and response.text:
                try:
                    kg_data = response.json()
                    relationship_count = len(kg_data.get('relationships', []))
                    self.log(f"Knowledge graph relationships: {relationship_count}")
                except:
                    self.log(f"KG response: {response.text[:200]}...")
                    
            return success
            
        except Exception as e:
            self.results['knowledge_graph'] = False
            self.log(f"Knowledge graph: ✗ (Error: {e})")
            return False
            
    def run_full_test(self):
        """Run complete end-to-end test suite"""
        self.log("Starting End-to-End Ingestion Test")
        self.log("=" * 50)
        
        # Test sequence
        tests = [
            ("Server Health", self.test_server_health),
            ("API Endpoints", self.test_api_endpoints),
            ("File Discovery", self.test_file_discovery),
            ("File Upload", self.test_file_upload_api),
            ("Workflow Creation", self.test_workflow_creation),
            ("Knowledge Graph", self.test_knowledge_graph_integration)
        ]
        
        for test_name, test_func in tests:
            self.log(f"\n--- {test_name} ---")
            try:
                test_func()
            except Exception as e:
                self.log(f"{test_name}: ✗ (Unexpected error: {e})")
                self.results[test_name.lower().replace(' ', '_')] = False
                
        self.generate_report()
        
    def generate_report(self):
        """Generate final test report"""
        self.log("\n" + "=" * 50)
        self.log("END-TO-END TEST RESULTS")
        self.log("=" * 50)
        
        passed = 0
        failed = 0
        skipped = 0
        
        for key, value in self.results.items():
            if key.startswith('discovered_') or key.endswith('_response') or key.endswith('_id'):
                continue  # Skip metadata
                
            if value is True:
                passed += 1
                status = "✓ PASS"
            elif value is False:
                failed += 1
                status = "✗ FAIL"
            else:
                skipped += 1
                status = "⚠ SKIP"
                
            self.log(f"{key.replace('_', ' ').title():<25} {status}")
            
        self.log("-" * 50)
        self.log(f"TOTAL TESTS: {passed + failed + skipped}")
        self.log(f"PASSED: {passed}")
        self.log(f"FAILED: {failed}")
        self.log(f"SKIPPED: {skipped}")
        
        if 'discovered_files' in self.results:
            files = self.results['discovered_files']
            self.log(f"\nFILE SUMMARY:")
            self.log(f"Total files discovered: {files['total_count']}")
            self.log(f"PDF files: {files['pdf_count']}")
            self.log(f"CSV files: {files['csv_count']}")
            
        # Overall status
        critical_tests = ['server_health', 'file_discovery']
        critical_passed = all(self.results.get(test, False) for test in critical_tests)
        
        self.log("\n" + "=" * 50)
        if failed == 0 and critical_passed:
            self.log("🎉 E2E TEST SUITE: PASSED")
            self.log("The LawyerFactory ingestion system is ready for use!")
        elif critical_passed:
            self.log("⚠️  E2E TEST SUITE: PARTIAL PASS")
            self.log("Core functionality works, some advanced features may need attention.")
        else:
            self.log("❌ E2E TEST SUITE: FAILED")
            self.log("Critical issues detected. System requires fixes before use.")
            
        return self.results

if __name__ == "__main__":
    tester = E2EIngestTest()
    results = tester.run_full_test()
    
    # Save results for analysis
    with open("e2e_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"\nDetailed results saved to: e2e_test_results.json")