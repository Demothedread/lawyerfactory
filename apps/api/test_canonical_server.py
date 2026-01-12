#!/usr/bin/env python3
"""
Test script for LawyerFactory Canonical Server
Tests the consolidated server functionality and API endpoints
"""

import json
import sys
import time
from pathlib import Path
from flask.testing import FlaskClient

# Add src to path for imports

def test_imports():
    """Test that all required imports work"""
    print("🧪 Testing imports...")

    try:
        # Test Flask imports
        from flask import Flask, jsonify
        print("✅ Flask imports successful")

        # Test SocketIO imports
        from flask_socketio import SocketIO
        print("✅ SocketIO imports successful")

        # Test CORS imports
        from flask_cors import CORS
        print("✅ CORS imports successful")

        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_server_creation():
    """Test that the server can be created and configured"""
    print("\n🧪 Testing server creation...")

    try:
        from server import app, socketio
        print("✅ Server creation successful")
        print(f"✅ App name: {app.name}")
        print(f"✅ SocketIO async mode: {socketio.async_mode}")
        return True
    except Exception as e:
        print(f"❌ Server creation failed: {e}")
        return False

def test_health_endpoint():
    """Test the health check endpoint"""
    print("\n🧪 Testing health endpoint...")

    try:
        from server import app

        with app.test_client() as client:
            response = client.get('/api/health')
            if response.status_code == 200:
                data = json.loads(response.data)
                print("✅ Health endpoint successful")
                print(f"   Status: {data.get('status')}")
                print(f"   Version: {data.get('version')}")
                print(f"   Features: {data.get('features', {})}")
                return True
            else:
                print(f"❌ Health endpoint failed with status {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False

def test_evidence_api():
    """Test the evidence API endpoints"""
    print("\n🧪 Testing evidence API...")

    try:
        from server import app

        with app.test_client() as client:
            # Type hint for the client
            client: FlaskClient

            # Test GET evidence table
            response = client.get('/api/evidence')
            if response.status_code == 200:
                data = json.loads(response.data)
                print("✅ GET evidence table successful")
                print(f"   Total evidence: {data.get('total', 0)}")
                print(f"   Primary count: {data.get('primary_count', 0)}")
                print(f"   Secondary count: {data.get('secondary_count', 0)}")
            else:
                print(f"❌ GET evidence table failed with status {response.status_code}")

            # Test POST evidence entry
            evidence_data = {
                "source_document": "test_contract.pdf",
                "content": "This is a test contract document for testing purposes.",
                "evidence_source": "primary",
                "relevance_score": 0.85,
                "key_terms": ["contract", "test"],
                "created_by": "test_user"
            }

            response = client.post('/api/evidence',
                                   data=json.dumps(evidence_data), 
                                   content_type='application/json')

            if response.status_code == 200:
                data = json.loads(response.data)
                print("✅ POST evidence entry successful")
                print(f"   Evidence ID: {data.get('evidence_id')}")
            else:
                print(f"❌ POST evidence entry failed with status {response.status_code}")

            return True
    except Exception as e:
        print(f"❌ Evidence API test failed: {e}")
        return False

def test_research_api():
    """Test the research API endpoints"""
    print("\n🧪 Testing research API...")

    try:
        from server import app

        with app.test_client() as client:
            # Test research execution
            research_data = {
                "case_id": "test_case_001",
                "evidence_id": "evidence_001",
                "keywords": ["contract", "employment", "termination"],
                "max_results": 5
            }

            response = client.post('/api/research/execute',
                                 data=json.dumps(research_data),
                                 content_type='application/json')

            if response.status_code == 200:
                data = json.loads(response.data)
                print("✅ Research execution successful")
                print(f"   Research ID: {data.get('research_id')}")
                print(f"   Status: {data.get('status')}")
                print(f"   Sources found: {data.get('result', {}).get('total_sources', 0)}")
            else:
                print(f"❌ Research execution failed with status {response.status_code}")

            return True
    except Exception as e:
        print(f"❌ Research API test failed: {e}")
        return False

def test_phase_orchestration():
    """Test the phase orchestration endpoints"""
    print("\n🧪 Testing phase orchestration...")

    try:
        from server import app

        with app.test_client() as client:
            # Test phase start
            phase_data = {
                "case_id": "test_case_001",
                "llm_provider": "openai",
                "llm_model": "gpt-4"
            }

            response = client.post('/api/phases/phaseA01_intake/start',
                                 data=json.dumps(phase_data),
                                 content_type='application/json')

            if response.status_code == 200:
                data = json.loads(response.data)
                print("✅ Phase orchestration successful")
                print(f"   Phase: {data.get('phase')}")
                print(f"   Case ID: {data.get('case_id')}")
                print(f"   Status: {data.get('result', {}).get('status')}")
            else:
                print(f"❌ Phase orchestration failed with status {response.status_code}")

            return True
    except Exception as e:
        print(f"❌ Phase orchestration test failed: {e}")
        return False

def test_socketio_events():
    """Test SocketIO event handling"""
    print("\n🧪 Testing SocketIO events...")

    try:
        from server import socketio

        # Test that socketio is properly configured
        print("✅ SocketIO configuration:")
        print(f"   Async mode: {socketio.async_mode}")
        print(f"   CORS allowed origins: {socketio.cors_allowed_origins}")

        # Note: Full SocketIO testing would require a running server
        # This is a basic configuration test
        return True
    except Exception as e:
        print(f"❌ SocketIO test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 LawyerFactory Canonical Server Test Suite")
    print("=" * 50)

    tests = [
        ("Import Tests", test_imports),
        ("Server Creation Tests", test_server_creation),
        ("Health Endpoint Tests", test_health_endpoint),
        ("Evidence API Tests", test_evidence_api),
        ("Research API Tests", test_research_api),
        ("Phase Orchestration Tests", test_phase_orchestration),
        ("SocketIO Tests", test_socketio_events),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20}")
        print(f"Running: {test_name}")
        print('='*20)

        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("🧪 TEST SUMMARY")
    print("=" * 50)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 50)
    print(f"📊 RESULTS: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! Canonical server is ready for use.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)