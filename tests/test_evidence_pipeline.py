#!/usr/bin/env python3
"""
End-to-end test of the evidence ingestion and vectorization pipeline
"""

import sys
import os
import json
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_evidence_ingestion_pipeline():
    """Test the complete evidence ingestion pipeline"""

    print("🔍 Testing Evidence Ingestion and Vectorization Pipeline")
    print("=" * 60)

    # Test 1: Check if unified storage can be initialized
    print("\n1. Testing Unified Storage Initialization...")
    try:
        from lawyerfactory.storage.core.unified_storage_api import get_enhanced_unified_storage_api
        unified_storage = get_enhanced_unified_storage_api()
        print("✅ Unified storage initialized successfully")
    except Exception as e:
        print(f"❌ Unified storage initialization failed: {e}")
        return False

    # Test 2: Test evidence ingestion
    print("\n2. Testing Evidence Ingestion...")
    try:
        test_content = b"This is a test legal document about contract breach and negligence claims."
        test_filename = "test_contract.pdf"
        test_metadata = {
            "case_id": "test_case_123",
            "phase": "phaseA01_intake",
            "description": "Test contract document"
        }

        result = unified_storage.store_evidence(
            file_content=test_content,
            filename=test_filename,
            metadata=test_metadata,
            source_phase="phaseA01_intake"
        )

        if result.success:
            object_id = result.object_id
            print(f"✅ Evidence stored successfully with ObjectID: {object_id}")
            print(f"   - S3 URL: {result.s3_url}")
            print(f"   - Evidence ID: {result.evidence_id}")
            print(f"   - Processing time: {result.processing_time:.2f}s")
        else:
            print(f"❌ Evidence storage failed: {result.error}")
            return False

    except Exception as e:
        print(f"❌ Evidence ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: Test evidence retrieval
    print("\n3. Testing Evidence Retrieval...")
    try:
        evidence_data = unified_storage.retrieve_evidence_by_id(object_id)
        if evidence_data:
            print("✅ Evidence retrieved successfully")
            print(f"   - Retrieved data keys: {list(evidence_data.keys())}")
        else:
            print("❌ Evidence retrieval failed - no data returned")
            return False
    except Exception as e:
        print(f"❌ Evidence retrieval failed: {e}")
        return False

    # Test 4: Test vector search
    print("\n4. Testing Vector Search...")
    try:
        search_results = unified_storage.search_evidence("contract breach", search_tier="vector")
        print(f"✅ Vector search completed: {len(search_results)} results")
        if search_results:
            print(f"   - First result ObjectID: {search_results[0].get('object_id', 'N/A')}")
            print(f"   - Relevance score: {search_results[0].get('relevance_score', 'N/A')}")
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
        return False

    # Test 5: Test claims matrix generation
    print("\n5. Testing Claims Matrix Generation...")
    try:
        # Get evidence for the test case
        case_documents = unified_storage.search_evidence_by_metadata({"case_id": "test_case_123"})
        print(f"✅ Found {len(case_documents)} documents for test case")

        # Generate claims matrix
        from apps.api.server import generate_claims_matrix_from_evidence
        claims_matrix = generate_claims_matrix_from_evidence("test_case_123", [test_content.decode('utf-8', errors='replace')])

        if claims_matrix:
            print(f"✅ Claims matrix generated: {len(claims_matrix)} claims")
            for claim in claims_matrix[:2]:  # Show first 2 claims
                print(f"   - {claim.get('name', 'Unknown')}: {claim.get('confidence_score', 0):.2f} confidence")
        else:
            print("❌ Claims matrix generation failed - no claims returned")
            return False

    except Exception as e:
        print(f"❌ Claims matrix generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 6: Test RAG context retrieval
    print("\n6. Testing RAG Context Retrieval...")
    try:
        from apps.api.server import get_rag_context_for_outline
        rag_context = get_rag_context_for_outline("test_case_123", claims_matrix, [])

        print(f"✅ RAG context retrieved: {len(rag_context)} context chunks")
        if rag_context:
            print(f"   - Sample context: {rag_context[0][:100]}...")

    except Exception as e:
        print(f"❌ RAG context retrieval failed: {e}")
        return False

    # Test 7: Test skeletal outline generation
    print("\n7. Testing Skeletal Outline Generation...")
    try:
        from apps.api.server import generate_rag_enhanced_outline
        outline = generate_rag_enhanced_outline("test_case_123", claims_matrix, [], rag_context)

        if outline and outline.get('sections'):
            print(f"✅ Skeletal outline generated: {len(outline['sections'])} sections")
            print(f"   - Total estimated words: {outline.get('totalEstimatedWords', 0)}")
            print(f"   - RAG context used: {outline.get('rag_context_used', 0)}")
        else:
            print("❌ Skeletal outline generation failed - no outline returned")
            return False

    except Exception as e:
        print(f"❌ Skeletal outline generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("✅ Evidence ingestion pipeline is working correctly")
    print("✅ Vectorization and storage are functioning")
    print("✅ RAG-enhanced claims matrix generation works")
    print("✅ Skeletal outline generation with RAG context works")
    print("\n📊 Pipeline Summary:")
    print(f"   - ObjectID: {object_id}")
    print(f"   - Claims Generated: {len(claims_matrix)}")
    print(f"   - Outline Sections: {len(outline.get('sections', []))}")
    print(f"   - Vector Search Results: {len(search_results)}")

    return True

def main():
    """Main test function"""
    success = test_evidence_ingestion_pipeline()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())