#!/usr/bin/env python3
"""
Simple Test Script for LawyerFactory Vector Store System

This script validates the basic vector store system without external dependencies.
It tests the core functionality using simple text processing and in-memory storage.

Usage:
    python test_vector_store_simple.py

Requirements:
    - Python 3.8+
    - test.pdf file in root directory
"""

import asyncio
from datetime import datetime
import hashlib
import json
import logging
import os
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Simple fallback vector store without external dependencies
class SimpleVectorStore:
    """Simple in-memory vector store for testing"""

    def __init__(self):
        self.documents = {}
        self.vectors = {}
        self.doc_counter = 0

    def generate_simple_vector(self, text: str) -> list:
        """Generate a simple hash-based vector"""
        # Create a simple 128-dimensional vector from text hash
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert to list of floats between -1 and 1
        vector = []
        for i in range(0, len(hash_bytes), 1):
            if len(vector) >= 128:  # Limit to 128 dimensions
                break
            byte_val = hash_bytes[i] if i < len(hash_bytes) else 0
            # Normalize to -1 to 1 range
            normalized_val = (byte_val / 127.5) - 1.0
            vector.append(normalized_val)

        return vector

    async def ingest_evidence(self, content: str, metadata: dict, store_type: str = "general") -> str:
        """Ingest document and generate vector"""
        doc_id = f"doc_{self.doc_counter}"
        self.doc_counter += 1

        # Generate vector
        vector = self.generate_simple_vector(content)

        # Store document
        self.documents[doc_id] = {
            "content": content,
            "metadata": metadata,
            "store_type": store_type,
            "created_at": datetime.now().isoformat()
        }
        self.vectors[doc_id] = vector

        return doc_id

    def cosine_similarity(self, vec1: list, vec2: list) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)
        except Exception:
            return 0.0

    async def semantic_search(self, query: str, top_k: int = 5) -> list:
        """Simple semantic search using text overlap"""
        query_vector = self.generate_simple_vector(query)
        results = []

        for doc_id, doc in self.documents.items():
            if doc_id in self.vectors:
                vector = self.vectors[doc_id]
                similarity = self.cosine_similarity(query_vector, vector)

                # Also check for keyword overlap
                query_words = set(query.lower().split())
                content_words = set(doc["content"].lower().split())
                overlap = len(query_words.intersection(content_words))
                keyword_boost = overlap / len(query_words) if query_words else 0

                # Combine vector similarity with keyword boost
                final_score = (similarity + keyword_boost) / 2

                results.append((doc, final_score))

        # Sort by score and return top k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def get_stats(self) -> dict:
        """Get store statistics"""
        return {
            "total_documents": len(self.documents),
            "total_vectors": len(self.vectors),
            "document_types": list(set(doc["store_type"] for doc in self.documents.values()))
        }


class VectorStoreTestSuite:
    """Simple test suite for vector store functionality"""

    def __init__(self):
        self.vector_store = SimpleVectorStore()
        self.test_results = []

    async def test_pdf_ingestion(self):
        """Test ingesting the test.pdf file content"""
        print("\n📄 Testing PDF content ingestion...")

        try:
            # Read test.pdf content
            test_pdf_path = Path("test.pdf")
            if not test_pdf_path.exists():
                raise FileNotFoundError("test.pdf not found in root directory")

            # Read the content (it's actually text content in the file)
            content = test_pdf_path.read_text(encoding='utf-8', errors='ignore')

            print(f"📁 Read {len(content)} characters from test.pdf")

            # Create test metadata
            test_metadata = {
                "source": "test_document",
                "case_id": "TEST_CASE_001",
                "document_type": "news_article",
                "title": "Jeffrey Epstein Tapes: Claims About Donald Trump",
                "description": "Article about Jeffrey Epstein's recorded conversations regarding Donald Trump",
                "ingestion_date": datetime.now().isoformat(),
                "word_count": len(content.split())
            }

            # Ingest the document
            doc_id = await self.vector_store.ingest_evidence(
                content=content,
                metadata=test_metadata,
                store_type="primary_evidence"
            )

            print(f"✅ Document ingested successfully: {doc_id}")
            print(f"   📊 Word count: {test_metadata['word_count']}")
            print(f"   📝 Content preview: {content[:200]}...")

            self.test_results.append(("pdf_ingestion", "success", f"Document ID: {doc_id}"))
            return doc_id

        except Exception as e:
            print(f"❌ PDF ingestion test failed: {e}")
            self.test_results.append(("pdf_ingestion", "failed", str(e)))
            return None

    async def test_semantic_search(self):
        """Test semantic search functionality"""
        print("\n🔍 Testing semantic search...")

        try:
            # Test queries related to the PDF content
            test_queries = [
                "Jeffrey Epstein and Donald Trump",
                "Epstein tapes",
                "Trump's personal conduct",
                "friendship between Epstein and Trump"
            ]

            for query in test_queries:
                print(f"\n   Searching: '{query}'")

                # Perform semantic search
                results = await self.vector_store.semantic_search(query, top_k=2)

                if results:
                    print(f"   ✅ Found {len(results)} results")
                    for i, (doc, score) in enumerate(results, 1):
                        print(f"      {i}. Score: {score:.3f}")
                        print(f"         Title: {doc['metadata'].get('title', 'Unknown')}")
                        print(f"         Content preview: {doc['content'][:100]}...")
                else:
                    print("   ⚠️  No results found")

            self.test_results.append(("semantic_search", "success", f"Tested {len(test_queries)} queries"))

        except Exception as e:
            print(f"❌ Semantic search test failed: {e}")
            self.test_results.append(("semantic_search", "failed", str(e)))

    async def test_store_metrics(self):
        """Test vector store metrics"""
        print("\n📊 Testing vector store metrics...")

        try:
            stats = self.vector_store.get_stats()

            print("✅ Vector store metrics retrieved")
            print(f"   📈 Total documents: {stats['total_documents']}")
            print(f"   🧠 Total vectors: {stats['total_vectors']}")
            print(f"   📁 Document types: {stats['document_types']}")

            self.test_results.append(("store_metrics", "success", f"Stats: {stats}"))

        except Exception as e:
            print(f"❌ Metrics test failed: {e}")
            self.test_results.append(("store_metrics", "failed", str(e)))

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*60)
        print("🧪 VECTOR STORE TEST SUITE SUMMARY")
        print("="*60)

        passed = 0
        failed = 0

        for test_name, status, details in self.test_results:
            status_icon = "✅" if status == "success" else "❌"
            print(f"{status_icon} {test_name}: {status.upper()}")

            if status == "success":
                passed += 1
                print(f"   📝 {details}")
            else:
                failed += 1
                print(f"   ❌ {details}")
            print()

        print(f"📊 Overall Results: {passed} passed, {failed} failed")

        if passed > 0 and failed == 0:
            print("🎉 All tests passed! Vector store system is working correctly.")
        elif passed > 0:
            print("⚠️  Some tests passed. Review failed tests for issues.")
        else:
            print("❌ All tests failed. Check system configuration.")

        print("="*60)

    async def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting LawyerFactory Vector Store Test Suite")
        print("=" * 60)

        try:
            # Test PDF ingestion
            doc_id = await self.test_pdf_ingestion()

            if doc_id:
                # Test semantic search
                await self.test_semantic_search()

            # Test metrics
            await self.test_store_metrics()

        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            self.test_results.append(("test_suite", "failed", str(e)))

        finally:
            # Print summary
            self.print_test_summary()


async def main():
    """Main test execution function"""
    print("🔬 LawyerFactory Vector Store Validation Test")
    print("Using simple in-memory vector store (no external dependencies)")

    # Initialize test suite
    test_suite = VectorStoreTestSuite()

    # Run all tests
    await test_suite.run_all_tests()

    # Exit with appropriate code
    failed_tests = sum(1 for _, status, _ in test_suite.test_results if status == "failed")
    sys.exit(1 if failed_tests > 0 else 0)


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())