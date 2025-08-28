# Script Name: test_integration_runner.py
# Description: Simple test runner to validate the AI Document Integration
# Relationships:
#   - Entity Type: Test
#   - Directory Group: Orchestration
#   - Group Tags: testing
Simple test runner to validate the AI Document Integration
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

async def main():
    """Run the integration test"""
    try:
        print("=== AI Document Integration Test Runner ===\n")
        
        # Import and run the integration test
        from tests.test_ai_document_integration import run_integration_test
        
        print("Starting AI Document Integration Test...")
        results = await run_integration_test()
        
        print("\n=== Final Results ===")
        print(f"Success: {results['success']}")
        print(f"Passed: {results['passed']}/{results['total']} tests")
        
        if results['success']:
            print("\n🎉 All integration tests PASSED!")
            print("\nThe AI Document Generation system has been successfully integrated")
            print("with the LawyerFactory multi-agent orchestration system.")
            
            print("\n✅ Integration Features Validated:")
            print("  • AI Document Agent creation and registration")
            print("  • Enhanced workflow phases with AI tasks")
            print("  • Tesla case data processing")
            print("  • AI generation status tracking")
            print("  • Multi-agent orchestration coordination")
            
        else:
            print(f"\n❌ Integration test FAILED ({results['passed']}/{results['total']} passed)")
            print("\nFailed tests:")
            for test_name, passed, details in results['details']:
                if not passed:
                    print(f"  • {test_name}: {details}")
        
        return results['success']
        
    except Exception as e:
        print(f"\n❌ Integration test runner failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)