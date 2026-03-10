"""
Backend API Unit Tests - Test individual endpoints and business logic

Tests implemented:
- Evidence CRUD operations
- LLM configuration endpoints
- Phase status endpoints
- Health check and system endpoints
- Error handling and edge cases
"""

import json
import sys
import time
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add server to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/api"))

# Mock the LawyerFactory imports that might fail
sys.modules['lawyerfactory'] = MagicMock()
sys.modules['lawyerfactory.agents'] = MagicMock()
sys.modules['lawyerfactory.chat'] = MagicMock()
sys.modules['lawyerfactory.storage'] = MagicMock()

from server import app, evidence_store, phase_status_store


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def cleanup_evidence_store():
    """Clean up evidence store before/after tests."""
    evidence_store.clear()
    yield
    evidence_store.clear()


@pytest.fixture
def cleanup_phase_store():
    """Clean up phase store before/after tests."""
    phase_status_store.clear()
    yield
    phase_status_store.clear()


class TestHealthCheck:
    """Test health check and system endpoints."""

    def test_health_check(self, client):
        """Test /api/health endpoint returns 200."""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'timestamp' in data

    def test_llm_config_endpoint(self, client):
        """Test /api/llm/config returns valid configuration."""
        response = client.get('/api/llm/config')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'config' in data
        assert 'provider' in data['config']
        assert 'model' in data['config']
        assert 'available_models' in data


class TestEvidenceCRUD:
    """Test evidence CRUD operations."""

    def test_create_evidence_success(self, client, cleanup_evidence_store):
        """Test creating evidence with all required fields."""
        payload = {
            "source_document": "TestCase_v1.pdf",
            "content": "This is test evidence content",
            "evidence_type": "document",
            "evidence_source": "court_filing",
            "relevance_score": 0.9,
            "relevance_level": "high",
            "bluebook_citation": "Smith v. Jones, 123 F.3d 456 (2d Cir. 2021)"
        }
        
        response = client.post('/api/evidence', 
                              data=json.dumps(payload),
                              content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'evidence_id' in data
        assert data['evidence']['source_document'] == payload['source_document']

    def test_create_evidence_missing_required_field(self, client, cleanup_evidence_store):
        """Test creating evidence without required fields fails."""
        payload = {
            "source_document": "TestCase_v1.pdf",
            # Missing 'content' and 'evidence_type'
        }
        
        response = client.post('/api/evidence',
                              data=json.dumps(payload),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_get_evidence_list(self, client, cleanup_evidence_store):
        """Test retrieving all evidence."""
        # Create test evidence
        payload = {
            "source_document": "TestDoc.pdf",
            "content": "Evidence content",
            "evidence_type": "testimony"
        }
        client.post('/api/evidence',
                   data=json.dumps(payload),
                   content_type='application/json')
        
        response = client.get('/api/evidence')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['evidence']) == 1

    def test_get_evidence_by_id(self, client, cleanup_evidence_store):
        """Test retrieving specific evidence by ID."""
        # Create evidence
        payload = {
            "source_document": "TestDoc.pdf",
            "content": "Evidence content",
            "evidence_type": "testimony"
        }
        create_response = client.post('/api/evidence',
                                     data=json.dumps(payload),
                                     content_type='application/json')
        evidence_id = json.loads(create_response.data)['evidence_id']
        
        # Get by ID
        response = client.get(f'/api/evidence/{evidence_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['evidence']['evidence_id'] == evidence_id

    def test_get_nonexistent_evidence(self, client, cleanup_evidence_store):
        """Test retrieving nonexistent evidence returns 404."""
        fake_id = str(uuid.uuid4())
        response = client.get(f'/api/evidence/{fake_id}')
        assert response.status_code == 404

    def test_update_evidence(self, client, cleanup_evidence_store):
        """Test updating evidence."""
        # Create evidence
        payload = {
            "source_document": "TestDoc.pdf",
            "content": "Original content",
            "evidence_type": "testimony"
        }
        create_response = client.post('/api/evidence',
                                     data=json.dumps(payload),
                                     content_type='application/json')
        evidence_id = json.loads(create_response.data)['evidence_id']
        
        # Update it
        update_payload = {"content": "Updated content"}
        response = client.put(f'/api/evidence/{evidence_id}',
                             data=json.dumps(update_payload),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['evidence']['content'] == "Updated content"

    def test_delete_evidence(self, client, cleanup_evidence_store):
        """Test deleting evidence."""
        # Create evidence
        payload = {
            "source_document": "TestDoc.pdf",
            "content": "Content",
            "evidence_type": "testimony"
        }
        create_response = client.post('/api/evidence',
                                     data=json.dumps(payload),
                                     content_type='application/json')
        evidence_id = json.loads(create_response.data)['evidence_id']
        
        # Delete it
        response = client.delete(f'/api/evidence/{evidence_id}')
        assert response.status_code == 200
        
        # Verify it's gone
        response = client.get(f'/api/evidence/{evidence_id}')
        assert response.status_code == 404

    def test_filter_evidence_by_source(self, client, cleanup_evidence_store):
        """Test filtering evidence by source."""
        # Create evidence with different sources
        for source in ['court_filing', 'discovery', 'testimony']:
            payload = {
                "source_document": f"Doc_{source}.pdf",
                "content": f"Content from {source}",
                "evidence_type": "document",
                "evidence_source": source
            }
            client.post('/api/evidence',
                       data=json.dumps(payload),
                       content_type='application/json')
        
        # Filter by source
        response = client.get('/api/evidence?evidence_source=court_filing')
        data = json.loads(response.data)
        assert len(data['evidence']) == 1
        assert data['evidence'][0]['evidence_source'] == 'court_filing'

    def test_batch_delete_evidence(self, client, cleanup_evidence_store):
        """Test batch deletion of evidence."""
        # Create multiple evidence entries
        ids = []
        for i in range(3):
            payload = {
                "source_document": f"Doc_{i}.pdf",
                "content": f"Content {i}",
                "evidence_type": "document"
            }
            create_response = client.post('/api/evidence',
                                         data=json.dumps(payload),
                                         content_type='application/json')
            ids.append(json.loads(create_response.data)['evidence_id'])
        
        # Batch delete
        batch_payload = {
            "operation": "delete",
            "evidence_ids": ids[:2]  # Delete first 2
        }
        response = client.post('/api/evidence/batch',
                              data=json.dumps(batch_payload),
                              content_type='application/json')
        
        assert response.status_code == 200
        
        # Verify deletion
        response = client.get('/api/evidence')
        data = json.loads(response.data)
        assert len(data['evidence']) == 1

    def test_get_evidence_stats(self, client, cleanup_evidence_store):
        """Test evidence statistics endpoint."""
        # Create evidence with different types and sources
        for etype in ['document', 'testimony']:
            for source in ['court_filing', 'discovery']:
                payload = {
                    "source_document": f"{etype}_{source}.pdf",
                    "content": "Test content",
                    "evidence_type": etype,
                    "evidence_source": source,
                    "relevance_score": 0.8
                }
                client.post('/api/evidence',
                           data=json.dumps(payload),
                           content_type='application/json')
        
        response = client.get('/api/evidence/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_count'] == 4
        assert 'by_source' in data
        assert 'by_type' in data
        assert 'average_relevance_score' in data


class TestResearchPhase:
    """Test research phase endpoints."""

    def test_start_research_phase(self, client, cleanup_phase_store):
        """Test starting research phase."""
        payload = {
            "case_id": "case_123",
            "research_query": "liability in negligence cases"
        }
        
        response = client.post('/api/research/start',
                              data=json.dumps(payload),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['case_id'] == 'case_123'
        assert 'task_id' in data

    def test_start_research_missing_case_id(self, client):
        """Test starting research without case_id fails."""
        payload = {
            "research_query": "liability in negligence cases"
        }
        
        response = client.post('/api/research/start',
                              data=json.dumps(payload),
                              content_type='application/json')
        
        assert response.status_code == 400

    def test_get_research_status(self, client, cleanup_phase_store):
        """Test getting research status."""
        case_id = "case_123"
        
        response = client.get(f'/api/research/status/{case_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['case_id'] == case_id
        assert 'status' in data
        assert 'progress' in data

    def test_execute_research(self, client, cleanup_evidence_store):
        """Test executing research on evidence."""
        # Create evidence first
        payload = {
            "source_document": "TestCase.pdf",
            "content": "Test content",
            "evidence_type": "document"
        }
        create_response = client.post('/api/evidence',
                                     data=json.dumps(payload),
                                     content_type='application/json')
        evidence_id = json.loads(create_response.data)['evidence_id']
        
        # Execute research
        research_payload = {
            "evidence_id": evidence_id,
            "keywords": ["liability", "negligence"]
        }
        response = client.post('/api/research/execute',
                              data=json.dumps(research_payload),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['evidence_id'] == evidence_id
        assert 'results' in data


class TestErrorHandling:
    """Test error handling for various edge cases."""

    def test_invalid_json_payload(self, client):
        """Test handling of invalid JSON."""
        response = client.post('/api/evidence',
                              data='{"invalid json"',
                              content_type='application/json')
        
        assert response.status_code in [400, 500]

    def test_missing_content_type(self, client):
        """Test handling of missing content type."""
        response = client.post('/api/evidence',
                              data='{"test": "data"}')
        
        # Should either work or fail gracefully
        assert response.status_code in [200, 201, 400, 415]

    def test_empty_evidence_store(self, client, cleanup_evidence_store):
        """Test behavior with empty evidence store."""
        response = client.get('/api/evidence')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['evidence'] == []
        assert data['count'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
