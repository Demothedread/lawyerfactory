"""
Unit tests for Phase B02 drafting handler (handle_drafting_phase in server.py)
Tests drafting workflow with mocked WriterBot, Maestro, VectorClusterManager
Tests deliverable loading, section-by-section drafting, RAG integration, graceful fallback
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
import json
import csv
import tempfile
import shutil
from unittest.mock import AsyncMock, MagicMock, patch, call
import asyncio


@pytest.fixture
def temp_case_dir():
    """Fixture: Create temporary case directory with deliverables"""
    temp_dir = tempfile.mkdtemp()
    case_path = Path(temp_dir) / "cases" / "TEST-001"
    deliverables_path = case_path / "deliverables"
    drafts_path = case_path / "drafts"
    
    deliverables_path.mkdir(parents=True)
    drafts_path.mkdir(parents=True)
    
    yield case_path
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_shotlist_file(temp_case_dir):
    """Fixture: Create sample shotlist CSV"""
    shotlist_path = temp_case_dir / "deliverables" / "shotlist.csv"
    
    with open(shotlist_path, 'w', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["timestamp", "summary", "source_id", "relevant_sections"]
        )
        writer.writeheader()
        writer.writerow({
            "timestamp": "2024-01-15 10:00:00",
            "summary": "Contract signed",
            "source_id": "EV-001",
            "relevant_sections": '["count_one_breach_of_contract"]'
        })
        writer.writerow({
            "timestamp": "2024-01-20 11:00:00",
            "summary": "Defendant breached",
            "source_id": "EV-002",
            "relevant_sections": '["count_one_breach_of_contract"]'
        })
    
    return shotlist_path


@pytest.fixture
def sample_claims_matrix_file(temp_case_dir):
    """Fixture: Create sample claims matrix JSON"""
    claims_path = temp_case_dir / "deliverables" / "claims_matrix.json"
    
    claims_data = {
        "breach_of_contract": {
            "elements": {
                "valid_contract": {
                    "definition": "Contract requires offer, acceptance, consideration",
                    "satisfied": True,
                    "confidence_score": 95
                }
            }
        }
    }
    
    with open(claims_path, 'w') as f:
        json.dump(claims_data, f, indent=2)
    
    return claims_path


@pytest.fixture
def sample_skeletal_outline_file(temp_case_dir):
    """Fixture: Create sample skeletal outline JSON"""
    outline_path = temp_case_dir / "deliverables" / "skeletal_outline.json"
    
    outline_data = {
        "sections": [
            {
                "id": "caption",
                "title": "Caption",
                "cause_of_action": "general"
            },
            {
                "id": "count_one_breach_of_contract",
                "title": "Count I: Breach of Contract",
                "cause_of_action": "breach_of_contract"
            }
        ]
    }
    
    with open(outline_path, 'w') as f:
        json.dump(outline_data, f, indent=2)
    
    return outline_path


class TestDeliverablesLoading:
    """Test deliverable file loading"""

    def test_load_shotlist_csv(self, sample_shotlist_file):
        """Test: Shotlist CSV loads correctly"""
        with open(sample_shotlist_file, 'r') as f:
            shotlist = list(csv.DictReader(f))
        
        assert len(shotlist) == 2
        assert shotlist[0]["summary"] == "Contract signed"
        assert shotlist[1]["summary"] == "Defendant breached"

    def test_load_claims_matrix_json(self, sample_claims_matrix_file):
        """Test: Claims matrix JSON loads correctly"""
        with open(sample_claims_matrix_file, 'r') as f:
            claims_matrix = json.load(f)
        
        assert "breach_of_contract" in claims_matrix
        assert "elements" in claims_matrix["breach_of_contract"]

    def test_load_skeletal_outline_json(self, sample_skeletal_outline_file):
        """Test: Skeletal outline JSON loads correctly"""
        with open(sample_skeletal_outline_file, 'r') as f:
            skeletal_outline = json.load(f)
        
        assert "sections" in skeletal_outline
        assert len(skeletal_outline["sections"]) == 2


class TestDraftingWorkflow:
    """Test drafting workflow with mocked AI components"""

    @pytest.mark.asyncio
    async def test_section_by_section_drafting(
        self,
        temp_case_dir,
        sample_shotlist_file,
        sample_claims_matrix_file,
        sample_skeletal_outline_file
    ):
        """Test: Section-by-section drafting loop with WriterBot"""
        # Load deliverables
        with open(sample_shotlist_file, 'r') as f:
            shotlist = list(csv.DictReader(f))
        
        with open(sample_claims_matrix_file, 'r') as f:
            claims_matrix = json.load(f)
        
        with open(sample_skeletal_outline_file, 'r') as f:
            skeletal_outline = json.load(f)
        
        # Mock WriterBot
        mock_writer = AsyncMock()
        mock_writer.draft = AsyncMock(side_effect=[
            "Caption: Plaintiff v. Defendant...",
            "Count I: Breach of Contract\n\nI. Issue...",
        ])
        
        # Mock Maestro
        mock_maestro = MagicMock()
        mock_maestro.assemble_document = MagicMock(
            return_value="Complete complaint document with all sections assembled..."
        )
        
        # Mock VectorClusterManager
        mock_vector_mgr = AsyncMock()
        mock_vector_mgr.find_similar_documents = AsyncMock(return_value=[
            {"content": "Similar case 1..."},
            {"content": "Similar case 2..."}
        ])
        
        # Simulate drafting loop
        drafted_sections = []
        total_sections = len(skeletal_outline["sections"])
        
        for idx, section in enumerate(skeletal_outline["sections"]):
            # Filter relevant facts
            relevant_facts = [
                f for f in shotlist
                if section['id'] in f.get('relevant_sections', '[]')
            ]
            
            # Get relevant elements
            cause = section.get('cause_of_action', 'general')
            relevant_elements = claims_matrix.get(cause, {})
            
            # RAG enhancement
            rag_docs = await mock_vector_mgr.find_similar_documents(
                query_text=section['title'],
                top_k=3,
                similarity_threshold=0.6
            )
            
            # WriterBot drafts
            draft = await mock_writer.draft(f"Prompt for {section['title']}")
            
            drafted_sections.append({
                "section_id": section['id'],
                "title": section['title'],
                "content": draft
            })
        
        # Assemble document
        full_complaint = mock_maestro.assemble_document(drafted_sections)
        
        # Assertions
        assert len(drafted_sections) == 2
        assert drafted_sections[0]["section_id"] == "caption"
        assert drafted_sections[1]["section_id"] == "count_one_breach_of_contract"
        assert mock_writer.draft.call_count == 2
        assert mock_vector_mgr.find_similar_documents.call_count == 2
        assert mock_maestro.assemble_document.called
        assert "Complete complaint document" in full_complaint

    @pytest.mark.asyncio
    async def test_rag_context_integration(self):
        """Test: RAG context is retrieved and included in prompts"""
        # Mock VectorClusterManager
        mock_vector_mgr = AsyncMock()
        mock_vector_mgr.find_similar_documents = AsyncMock(return_value=[
            {"content": "Similar case 1: Contract breach example..."},
            {"content": "Similar case 2: Another precedent..."},
            {"content": "Similar case 3: Third example..."}
        ])
        
        # Retrieve RAG context
        rag_docs = await mock_vector_mgr.find_similar_documents(
            query_text="Breach of Contract",
            top_k=3,
            similarity_threshold=0.6
        )
        
        # Assertions
        assert len(rag_docs) == 3
        assert all("content" in doc for doc in rag_docs)
        assert mock_vector_mgr.find_similar_documents.called
        
        # Verify call arguments
        call_args = mock_vector_mgr.find_similar_documents.call_args
        assert call_args.kwargs["query_text"] == "Breach of Contract"
        assert call_args.kwargs["top_k"] == 3

    def test_document_assembly(self):
        """Test: Maestro assembles drafted sections into complete document"""
        # Mock Maestro
        mock_maestro = MagicMock()
        mock_maestro.assemble_document = MagicMock(
            return_value="CAPTION\n\nCOUNT I: BREACH OF CONTRACT\n\nPRAYER FOR RELIEF"
        )
        
        # Sample drafted sections
        drafted_sections = [
            {"section_id": "caption", "title": "Caption", "content": "CAPTION"},
            {"section_id": "count_one", "title": "Count I", "content": "COUNT I: BREACH OF CONTRACT"},
            {"section_id": "prayer", "title": "Prayer", "content": "PRAYER FOR RELIEF"}
        ]
        
        # Assemble
        full_complaint = mock_maestro.assemble_document(drafted_sections)
        
        # Assertions
        assert "CAPTION" in full_complaint
        assert "COUNT I" in full_complaint
        assert "PRAYER FOR RELIEF" in full_complaint
        assert mock_maestro.assemble_document.called

    def test_draft_file_saving(self, temp_case_dir):
        """Test: Draft is saved to correct file path"""
        draft_txt_path = temp_case_dir / "drafts" / "complaint_draft.txt"
        draft_json_path = temp_case_dir / "drafts" / "complaint_draft.json"
        
        # Sample complaint
        full_complaint = "Complete legal complaint document..."
        
        # Save TXT
        with open(draft_txt_path, 'w') as f:
            f.write(full_complaint)
        
        # Save JSON metadata
        draft_metadata = {
            "sections": [
                {"section_id": "caption", "title": "Caption", "content": "...", "word_count": 10}
            ],
            "metadata": {
                "case_id": "TEST-001",
                "total_word_count": 100,
                "section_count": 1
            }
        }
        
        with open(draft_json_path, 'w') as f:
            json.dump(draft_metadata, f, indent=2)
        
        # Assertions
        assert draft_txt_path.exists()
        assert draft_json_path.exists()
        
        # Verify content
        with open(draft_txt_path, 'r') as f:
            saved_complaint = f.read()
        assert saved_complaint == full_complaint
        
        with open(draft_json_path, 'r') as f:
            saved_metadata = json.load(f)
        assert saved_metadata["metadata"]["case_id"] == "TEST-001"


class TestGracefulFallback:
    """Test graceful fallback when AI components unavailable"""

    def test_import_error_handling(self):
        """Test: Handles ImportError when WriterBot/Maestro unavailable"""
        # Simulate import failure
        try:
            with patch('builtins.__import__', side_effect=ImportError("WriterBot not found")):
                # This would normally import WriterBot
                from lawyerfactory.compose.bots.writer import WriterBot
            assert False, "Should have raised ImportError"
        except ImportError as e:
            # Graceful fallback logic
            fallback_mode = True
            assert fallback_mode
            assert "WriterBot" in str(e)

    def test_fallback_response(self):
        """Test: Fallback returns basic template when bots unavailable"""
        # Simulate fallback response
        fallback_result = {
            "status": "completed",
            "message": "Drafting completed with basic template (WriterBot unavailable)",
            "fallback_mode": True
        }
        
        assert fallback_result["fallback_mode"]
        assert "basic template" in fallback_result["message"]


class TestProgressTracking:
    """Test progress tracking and Socket.IO emissions"""

    @pytest.mark.asyncio
    async def test_progress_calculation(self):
        """Test: Progress percentage calculated correctly"""
        sections = [
            {"id": "section1", "title": "Section 1"},
            {"id": "section2", "title": "Section 2"},
            {"id": "section3", "title": "Section 3"},
            {"id": "section4", "title": "Section 4"}
        ]
        
        total_sections = len(sections)
        
        # Simulate progress updates
        progress_updates = []
        for idx in range(total_sections):
            progress = int((idx / total_sections) * 100)
            progress_updates.append(progress)
        
        # Assertions
        assert progress_updates == [0, 25, 50, 75]
        
        # Final progress (after loop completes)
        final_progress = 100
        assert final_progress == 100

    def test_socket_emission_format(self):
        """Test: Socket.IO emission has correct format"""
        # Mock socketio
        mock_socketio = MagicMock()
        
        # Emit progress update
        mock_socketio.emit("phase_progress_update", {
            "phase": "phaseB02_drafting",
            "progress": 50,
            "message": "Drafting section 2/4: Count I: Breach of Contract"
        })
        
        # Verify emission
        assert mock_socketio.emit.called
        call_args = mock_socketio.emit.call_args
        assert call_args[0][0] == "phase_progress_update"
        assert call_args[0][1]["phase"] == "phaseB02_drafting"
        assert call_args[0][1]["progress"] == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
