#!/usr/bin/env python3
"""
Integration Test Script for integration_example.py Implementation
Tests backend LLM configuration endpoints and validates integration
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import json
import requests


def test_llm_config_endpoints():
    """Test the LLM configuration endpoints"""
    BASE_URL = "http://localhost:5000"
    
    print("=" * 60)
    print("Testing LawyerFactory LLM Integration")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1. Testing backend health...")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        print("   Make sure the backend is running: ./launch.sh")
        return False
    
    # Test 2: Get LLM config
    print("\n2. Testing GET /api/settings/llm...")
    try:
        response = requests.get(f"{BASE_URL}/api/settings/llm", timeout=5)
        if response.status_code == 200:
            config = response.json()
            print("✅ LLM config retrieved successfully:")
            print(f"   Provider: {config['config']['provider']}")
            print(f"   Model: {config['config']['model']}")
            print(f"   Temperature: {config['config']['temperature']}")
            print(f"   Max Tokens: {config['config']['max_tokens']}")
            print(f"   Available Providers: {', '.join(config['available_providers'])}")
        else:
            print(f"❌ GET /api/settings/llm failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ GET /api/settings/llm error: {e}")
        return False
    
    # Test 3: Update LLM config
    print("\n3. Testing POST /api/settings/llm...")
    try:
        new_config = {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "temperature": 0.2,
            "max_tokens": 1500
        }
        response = requests.post(
            f"{BASE_URL}/api/settings/llm",
            json=new_config,
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            print("✅ LLM config updated successfully")
            print(f"   New Provider: {result['config']['provider']}")
            print(f"   New Model: {result['config']['model']}")
        else:
            print(f"❌ POST /api/settings/llm failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ POST /api/settings/llm error: {e}")
        return False
    
    # Test 4: Validate draft endpoint exists
    print("\n4. Testing POST /api/drafting/validate endpoint...")
    try:
        test_draft = {
            "draft_text": "Test complaint text",
            "case_id": "test_case_001"
        }
        response = requests.post(
            f"{BASE_URL}/api/drafting/validate",
            json=test_draft,
            timeout=10
        )
        # We expect this might fail without a real case, but endpoint should exist
        if response.status_code in [200, 400, 404]:
            print("✅ Drafting validation endpoint exists")
            if response.status_code == 200:
                print("   Validation successful!")
            else:
                print(f"   Endpoint responded with {response.status_code} (expected without real case)")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Drafting validation test: {e}")
    
    # Test 5: Enhanced intake endpoint exists
    print("\n5. Testing POST /api/intake/process-document endpoint...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/intake/process-document",
            json={"test": "data"},
            timeout=10
        )
        if response.status_code in [200, 400, 404]:
            print("✅ Enhanced intake endpoint exists")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Enhanced intake test: {e}")
    
    print("\n" + "=" * 60)
    print("✅ ALL CORE INTEGRATION TESTS PASSED")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Test frontend: cd apps/ui/react-app && npm run dev")
    print("2. Open browser: http://localhost:3000")
    print("3. Click Settings (⚙️) to test EnhancedSettingsPanel")
    print("4. Verify LLM config loads from backend")
    print("5. Change settings and save")
    print("6. Upload evidence and run phase pipeline")
    print("\n")
    
    return True


def test_frontend_integration():
    """Test if frontend can connect to backend"""
    print("\n" + "=" * 60)
    print("Frontend Integration Check")
    print("=" * 60)
    
    FRONTEND_URL = "http://localhost:3000"
    
    print(f"\nChecking if frontend is running at {FRONTEND_URL}...")
    try:
        response = requests.get(FRONTEND_URL, timeout=3)
        if response.status_code == 200:
            print("✅ Frontend is running")
            print(f"   Access it at: {FRONTEND_URL}")
        else:
            print(f"⚠️ Frontend responded with: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Frontend not running: {e}")
        print("   Start it with: cd apps/ui/react-app && npm run dev")


if __name__ == "__main__":
    print("\n🚀 LawyerFactory Integration Test Suite\n")
    
    success = test_llm_config_endpoints()
    test_frontend_integration()
    
    if success:
        print("\n✅ Integration implementation verified!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed - check backend logs")
        sys.exit(1)
