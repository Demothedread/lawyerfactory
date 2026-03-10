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
#!/usr/bin/env python3
"""Pytest smoke tests for the canonical LawyerFactory API server."""

import importlib

import pytest
from flask.testing import FlaskClient


@pytest.fixture
def server_module(monkeypatch):
    """Import the canonical server with eventlet disabled for deterministic tests."""
    monkeypatch.setenv("LF_DISABLE_EVENTLET", "1")
    return importlib.import_module("server")


@pytest.fixture
def client(server_module) -> FlaskClient:
    """Return a Flask test client for the canonical server."""
    return server_module.app.test_client()


def test_imports():
    """Core Flask dependencies should import successfully."""
    from flask import Flask, jsonify
    from flask_cors import CORS
    from flask_socketio import SocketIO

    assert Flask is not None
    assert jsonify is not None
    assert CORS is not None
    assert SocketIO is not None


def test_server_creation(server_module):
    """The server app and Socket.IO instance should initialize."""
    assert server_module.app.name
    assert server_module.socketio.async_mode == "threading"


def test_health_endpoint(client: FlaskClient):
    """Health endpoint should return the expected metadata."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert isinstance(data.get("features"), list)
    assert "evidence_management" in data["features"]


def test_evidence_api(client: FlaskClient):
    """Evidence listing and creation endpoints should work."""
    list_response = client.get("/api/evidence")
    assert list_response.status_code == 200
    list_payload = list_response.get_json()
    assert list_payload["success"] is True
    assert "evidence" in list_payload

    create_response = client.post(
        "/api/evidence",
        json={
            "source_document": "test_contract.pdf",
            "content": "This is a test contract document for testing purposes.",
            "evidence_type": "documentary",
            "evidence_source": "primary",
            "relevance_score": 0.85,
            "key_terms": ["contract", "test"],
            "created_by": "test_user",
        },
    )

    assert create_response.status_code == 201
    create_payload = create_response.get_json()
    assert create_payload["success"] is True
    assert create_payload["evidence_id"]


def test_research_api(client: FlaskClient):
    """Research execution should succeed when called with an existing evidence item."""
    create_response = client.post(
        "/api/evidence",
        json={
            "source_document": "research_seed.txt",
            "content": "Seed evidence for research execution.",
            "evidence_type": "documentary",
            "evidence_source": "primary",
        },
    )
    evidence_id = create_response.get_json()["evidence_id"]

    response = client.post(
        "/api/research/execute",
        json={
            "case_id": "test_case_001",
            "evidence_id": evidence_id,
            "keywords": ["contract", "employment", "termination"],
            "max_results": 5,
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["evidence_id"] == evidence_id
    assert len(payload["results"]) > 0


def test_phase_orchestration(client: FlaskClient):
    """Phase orchestration should create a task for the requested phase."""
    response = client.post(
        "/api/phases/phaseA01_intake/start",
        json={"case_id": "test_case_001", "llm_provider": "openai", "llm_model": "gpt-4"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["phase_id"] == "phaseA01_intake"
    assert payload["case_id"] == "test_case_001"
    assert payload["status"] == "started"
    assert payload["task_id"]


def test_socketio_events(server_module):
    """Socket.IO should initialize with the expected backend manager."""
    assert server_module.socketio.async_mode == "threading"
    assert server_module.socketio.server is not None
    assert type(server_module.socketio.server.manager).__name__ == "Manager"