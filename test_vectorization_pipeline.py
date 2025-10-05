#!/usr/bin/env python3
"""
Test script for LawyerFactory vectorization and RAG pipeline
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")

    try:
        from lawyerfactory.storage.enhanced_unified_storage_api import get_enhanced_unified_storage_api
        print("✅ Unified storage import successful")

        from lawyerfactory.storage.vectors.enhanced_vector_store import EnhancedVectorStoreManager, VectorStoreType
        print("✅ Vector store import successful")

        from lawyerfactory.phases.phaseA01_intake.enhanced_document_categorizer import DocumentType
        print("✅ Document categorizer import successful")

        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vector_store():
    """Test vector store functionality"""
    print("\nTesting vector store...")

    try:
        from lawyerfactory.storage.vectors.enhanced_vector_store import EnhancedVectorStoreManager, VectorStoreType, VectorDocument
        import asyncio

        async def test_async():
            store = EnhancedVectorStoreManager()

            # Test embedding generation
            test_text = "This is a test legal document about contract breach and damages."
            vector = await store._generate_embedding(test_text)
            print(f"✅ Embedding generated: {len(vector)} dimensions")

            # Test document ingestion
            doc_id = await store.ingest_evidence(
                content=test_text,
                metadata={"case_id": "test_case_123", "source": "test"},
                store_type=VectorStoreType.PRIMARY_EVIDENCE
            )
            print(f"✅ Document ingested: {doc_id}")

            # Test semantic search
            results = await store.semantic_search("contract breach", top_k=5)
            print(f"✅ Semantic search completed: {len(results)} results")

            return True

        return asyncio.run(test_async())

    except Exception as e:
        print(f"❌ Vector store test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unified_storage():
    """Test unified storage functionality"""
    print("\nTesting unified storage...")

    try:
        from lawyerfactory.storage.enhanced_unified_storage_api import get_enhanced_unified_storage_api

        unified_storage = get_enhanced_unified_storage_api()
        print("✅ Unified storage initialized")

        # Test basic functionality
        if hasattr(unified_storage, 'search_evidence'):
            print("✅ Unified storage has search functionality")
        else:
            print("⚠️  Unified storage missing search functionality")

        return True

    except Exception as e:
        print(f"❌ Unified storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("LawyerFactory Vectorization Pipeline Test")
    print("=" * 50)

    results = []

    # Test imports
    results.append(("Imports", test_imports()))

    # Test vector store
    results.append(("Vector Store", test_vector_store()))

    # Test unified storage
    results.append(("Unified Storage", test_unified_storage()))

    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")

    all_passed = all(passed for _, passed in results)
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())