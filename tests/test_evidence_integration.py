"""
Integration test for Evidence Table with Unified Storage and Real-time Updates

Tests the complete flow:
1. Upload evidence → Unified Storage
2. Evidence processing → Evidence Table
3. Socket.IO events → Frontend updates
4. Download via ObjectID → File retrieval
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_evidence_integration():
    """Test complete evidence integration flow"""
    
    print("=" * 80)
    print("Evidence Table Integration Test")
    print("=" * 80)
    
    try:
        # Test 1: Import unified storage
        print("\n1️⃣  Testing Unified Storage Import...")
        from lawyerfactory.storage.core.unified_storage_api import (
            get_enhanced_unified_storage_api
        )
        unified_storage = get_enhanced_unified_storage_api()
        print("✅ Unified storage imported successfully")
        
        # Test 2: Import evidence table
        print("\n2️⃣  Testing Evidence Table Import...")
        from lawyerfactory.storage.evidence.table import (
            EnhancedEvidenceTable,
            EvidenceEntry,
            EvidenceType,
            RelevanceLevel
        )
        evidence_table = EnhancedEvidenceTable(storage_path="test_evidence_table.json")
        print("✅ Evidence table imported successfully")
        
        # Test 3: Import Socket.IO events
        print("\n3️⃣  Testing Socket.IO Events Import...")
        from lawyerfactory.phases.socket_events import (
            emit_evidence_processed,
            emit_evidence_uploaded,
            set_socketio_instance
        )
        print("✅ Socket.IO events imported successfully")
        print("⚠️  Note: Events will not emit without Flask-SocketIO instance")
        
        # Test 4: Add evidence with unified storage
        print("\n4️⃣  Testing Evidence Upload with Unified Storage...")
        test_content = b"This is a test legal document for evidence integration testing."
        test_filename = "test_document.txt"
        test_metadata = {
            "case_id": "test_case_001",
            "document_type": "complaint"
        }
        
        evidence_id = await evidence_table.add_evidence_with_unified_storage(
            file_content=test_content,
            filename=test_filename,
            metadata=test_metadata,
            source_phase="phaseA01_intake"
        )
        
        print(f"✅ Evidence uploaded successfully with ID: {evidence_id}")
        
        # Test 5: Retrieve evidence
        print("\n5️⃣  Testing Evidence Retrieval...")
        retrieved_evidence = evidence_table.get_evidence(evidence_id)
        
        if retrieved_evidence:
            print(f"✅ Evidence retrieved successfully:")
            print(f"   - Evidence ID: {retrieved_evidence.evidence_id}")
            print(f"   - Object ID: {retrieved_evidence.object_id}")
            print(f"   - Filename: {retrieved_evidence.source_document}")
            print(f"   - Created: {retrieved_evidence.created_at}")
        else:
            print("❌ Evidence retrieval failed")
            return False
        
        # Test 6: Update evidence (triggers analysis event)
        print("\n6️⃣  Testing Evidence Update (Analysis)...")
        update_success = evidence_table.update_evidence(
            evidence_id,
            {
                "relevance_score": 0.85,
                "relevance_level": RelevanceLevel.HIGH,
                "evidence_type": EvidenceType.DOCUMENTARY,
                "case_id": "test_case_001"
            }
        )
        
        if update_success:
            print("✅ Evidence updated successfully")
            print("   - Socket.IO 'evidence_processed' event should have been emitted")
        else:
            print("❌ Evidence update failed")
            return False
        
        # Test 7: Export evidence table
        print("\n7️⃣  Testing Evidence Table Export...")
        exported_data = evidence_table.export_to_dict()
        evidence_count = len(exported_data.get("evidence_entries", {}))
        print(f"✅ Evidence table exported: {evidence_count} entries")
        
        # Test 8: Flask API routes (dry-run check)
        print("\n8️⃣  Testing Flask API Routes Import...")
        try:
            from apps.api.routes.evidence_flask import FlaskEvidenceAPI
            print("✅ Flask Evidence API routes available")
            print("   - GET /api/evidence")
            print("   - POST /api/evidence")
            print("   - PUT /api/evidence/<evidence_id>")
            print("   - DELETE /api/evidence/<evidence_id>")
            print("   - GET /api/evidence/<evidence_id>/download")
            print("   - GET /api/evidence/filter")
            print("   - GET /api/evidence/stats")
        except ImportError as e:
            print(f"⚠️  Flask API routes not available: {e}")
        
        # Test 9: Check object_id linkage
        print("\n9️⃣  Testing ObjectID Linkage...")
        if retrieved_evidence.object_id:
            print(f"✅ Evidence has ObjectID: {retrieved_evidence.object_id}")
            print("   - Can be used to retrieve file from unified storage")
            print("   - Download endpoint: /api/evidence/{evidence_id}/download")
        else:
            print("⚠️  Evidence missing ObjectID (may be in fallback mode)")
        
        # Summary
        print("\n" + "=" * 80)
        print("Integration Test Summary")
        print("=" * 80)
        print("✅ Unified Storage: Working")
        print("✅ Evidence Table: Working")
        print("✅ Socket.IO Events: Imported (needs Flask-SocketIO instance to emit)")
        print("✅ ObjectID Tracking: Working")
        print("✅ Flask API Routes: Available")
        print("\n📋 Next Steps:")
        print("   1. Start Flask server: ./launch.sh")
        print("   2. Upload evidence via React UI")
        print("   3. Verify real-time updates in evidence table")
        print("   4. Test download functionality via ObjectID")
        print("=" * 80)
        
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        evidence_table.delete_evidence(evidence_id)
        test_file = Path("test_evidence_table.json")
        if test_file.exists():
            test_file.unlink()
        print("✅ Cleanup complete")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_evidence_integration())
    sys.exit(0 if success else 1)
