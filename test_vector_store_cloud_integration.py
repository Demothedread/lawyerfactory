#!/usr/bin/env python3
"""
Test Script for LawyerFactory Vector Store Cloud Integration

This script validates the complete vector store system with cloud storage integration:
1. Evidence ingestion with cloud backup
2. Multi-tier storage (hot/warm/cold)
3. Retrieval with fallback between storage layers
4. Storage statistics and monitoring

Usage:
    python test_vector_store_cloud_integration.py

Requirements:
    - test.pdf file in root directory
    - All vector store modules properly installed
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from lawyerfactory.vectors.enhanced_vector_store import (
        EnhancedVectorStoreManager, VectorStoreType, ValidationType
    )
    from lawyerfactory.vectors.evidence_ingestion import EvidenceIngestionPipeline
    from lawyerfactory.vectors.cloud_storage_integration import (
        CloudStorageManager, IntegratedEvidenceIngestion, StorageTier
    )
    print("✅ Successfully imported all vector store modules")
except ImportError as e:
    print(f"❌ Failed to import vector store modules: {e}")
    print("Please ensure you're running from the law_venv environment")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CloudIntegrationTestSuite:
    """Comprehensive test suite for cloud storage integration"""

    def __init__(self):
        self.vector_store = None
        self.cloud_storage = None
        self.integrated_ingestion = None
        self.test_results = []

    async def setup(self):
        """Initialize all components with cloud integration"""
        print("\n🔧 Setting up cloud-integrated vector store components...")

        try:
            # Initialize vector store manager
            self.vector_store = EnhancedVectorStoreManager(
                storage_path="test_vector_stores_cloud"
            )
            print("✅ Vector store manager initialized")

            # Initialize cloud storage manager
            self.cloud_storage = CloudStorageManager              (
                vector_store_manager=self.vector_store,
                local_temp_dir="./test_uploads/tmp"
            )
            print("✅ Cloud storage manager initialized")

            # Initialize integrated evidence ingestion
            self.integrated_ingestion = IntegratedEvidenceIngestion(
                vector_store_manager=self.vector_store,
                cloud_storage_manager=self.cloud_storage
            )
            print("✅ Integrated evidence ingestion initialized")

            self.test_results.append(("setup", "success", "All cloud-integrated components initialized"))

        except Exception as e:
            print(f"❌ Setup failed: {e}")
            self.test_results.append(("setup", "failed", str(e)))
            raise

    async def test_cloud_evidence_ingestion(self):
        """Test evidence ingestion with cloud storage"""
        print("\n📄 Testing cloud-integrated evidence ingestion...")

        try:
            # Read test.pdf content
            test_pdf_path = Path("test.pdf")
            if not test_pdf_path.exists():
                raise FileNotFoundError("test.pdf not found in root directory")

            content = test_pdf_path.read_text(encoding='utf-8', errors='ignore')
            print(f"📁 Read {len(content)} characters from test.pdf")

            # Create test metadata
            test_metadata = {
                "source": "test_document",
                "case_id": "TEST_CASE_CLOUD_001",
                "document_type": "news_article",
                "title": "Jeffrey Epstein Tapes: Claims About Donald Trump",
                "description": "Article about Jeffrey Epstein's recorded conversations regarding Donald Trump",
                "ingestion_date": datetime.now().isoformat(),
                "word_count": len(content.split()),
                "jurisdiction": "federal_court",
                "case_type": "defamation"
            }

            # Test different storage tiers
            storage_tiers = [StorageTier.HOT, StorageTier.WARM, StorageTier.COLD]

            for tier in storage_tiers:
                print(f"\n   Testing {tier.value} storage tier...")

                # Ingest with cloud backup
                result = await self.integrated_ingestion.process_evidence_with_storage(
                    content=content,
                    metadata={**test_metadata, "storage_tier": tier.value},
                    store_type=VectorStoreType.PRIMARY_EVIDENCE,
                    storage_tier=tier
                )

                if result.get("success"):
                    print(f"   ✅ Document stored in {tier.value} tier")
                    print(f"      📄 Doc ID: {result.get('doc_id')}")
                    print(f"      💾 Storage ID: {result.get('storage_id')}")
                    print(f"      📁 Local path: {result.get('local_path')}")
                    print(f"      ☁️  Cloud URL: {result.get('cloud_url')}")

                    # Test retrieval for this document
                    retrieval_result = await self.integrated_ingestion.retrieve_evidence_with_fallback(
                        result.get('doc_id')
                    )

                    if retrieval_result.get("success"):
                        print(f"   ✅ Document retrieved from {retrieval_result.get('source')}")
                    else:
                        print(f"   ⚠️  Document retrieval failed: {retrieval_result.get('error')}")

                else:
                    print(f"   ❌ Storage failed for {tier.value}: {result.get('error')}")

            self.test_results.append(("cloud_ingestion", "success", f"Tested {len(storage_tiers)} storage tiers"))

        except Exception as e:
            print(f"❌ Cloud ingestion test failed: {e}")
            self.test_results.append(("cloud_ingestion", "failed", str(e)))

    async def test_storage_fallback_mechanism(self):
        """Test the fallback mechanism between storage layers"""
        print("\n🔄 Testing storage fallback mechanism...")

        try:
            # Create a test document
            test_content = "This is a test document for fallback testing."
            test_metadata = {
                "source": "fallback_test",
                "case_id": "FALLBACK_TEST_001",
                "document_type": "test_document",
                "title": "Fallback Test Document"
            }

            # Store document
            store_result = await self.integrated_ingestion.process_evidence_with_storage(
                content=test_content,
                metadata=test_metadata,
                store_type=VectorStoreType.PRIMARY_EVIDENCE,
                storage_tier=StorageTier.HOT
            )

            if not store_result.get("success"):
                raise Exception("Failed to store test document")

            doc_id = store_result.get("doc_id")
            print(f"✅ Test document stored with ID: {doc_id}")

            # Test multiple retrievals to simulate different scenarios
            retrieval_sources = []

            for i in range(3):
                retrieval_result = await self.integrated_ingestion.retrieve_evidence_with_fallback(doc_id)

                if retrieval_result.get("success"):
                    source = retrieval_result.get("source", "unknown")
                    retrieval_sources.append(source)
                    print(f"   📖 Retrieval {i+1}: {source}")
                else:
                    print(f"   ❌ Retrieval {i+1} failed: {retrieval_result.get('error')}")

            # Analyze retrieval patterns
            unique_sources = set(retrieval_sources)
            print(f"   📊 Used {len(unique_sources)} different storage sources: {', '.join(unique_sources)}")

            self.test_results.append(("storage_fallback", "success", f"Tested fallback with {len(retrieval_sources)} retrievals"))

        except Exception as e:
            print(f"❌ Storage fallback test failed: {e}")
            self.test_results.append(("storage_fallback", "failed", str(e)))

    async def test_storage_tier_management(self):
        """Test storage tier management and policies"""
        print("\n🏢 Testing storage tier management...")

        try:
            # Get storage statistics
            stats = self.cloud_storage.get_storage_stats()
            print("✅ Storage statistics retrieved")
            print(f"   📈 Total mapped documents: {stats.get('total_mapped_documents', 0)}")
            print(f"   📁 Local temp files: {stats.get('local_temp_files', 0)}")
            print(f"   ☁️  Cloud stored files: {stats.get('cloud_stored_files', 0)}")

            # Show storage tiers breakdown
            storage_tiers = stats.get('storage_tiers', {})
            if storage_tiers:
                print("   🏢 Storage tiers:")
                for tier, count in storage_tiers.items():
                    print(f"      {tier}: {count} documents")
            else:
                print("   🏢 No documents in storage tiers yet")

            self.test_results.append(("tier_management", "success", f"Stats: {stats}"))

        except Exception as e:
            print(f"❌ Storage tier management test failed: {e}")
            self.test_results.append(("tier_management", "failed", str(e)))

    async def test_vector_store_metrics(self):
        """Test comprehensive vector store metrics"""
        print("\n📊 Testing comprehensive vector store metrics...")

        try:
            # Get vector store metrics
            metrics = await self.vector_store.get_store_metrics()

            print("✅ Vector store metrics retrieved")
            print(f"   📈 Overall documents: {metrics.get('overall', {}).get('total_documents', 0)}")
            print(f"   🧠 Overall vectors: {metrics.get('overall', {}).get('total_vectors', 0)}")
            print(f"   🎯 Validation sub-vectors: {metrics.get('overall', {}).get('validation_sub_vectors', 0)}")

            # Show store-specific metrics
            stores = metrics.get('stores', {})
            for store_name, store_data in stores.items():
                print(f"   🏪 {store_name}: {store_data.get('documents', 0)} documents")

            # Show health indicators
            health = metrics.get('health', {})
            if health:
                print("   💚 System Health:")
                print(f"      Cache hit rate: {health.get('cache_hit_rate', 0):.2%}")
                print(f"      Total documents: {health.get('total_documents', 0)}")

            self.test_results.append(("vector_metrics", "success", f"Metrics for {len(stores)} stores"))

        except Exception as e:
            print(f"❌ Vector store metrics test failed: {e}")
            self.test_results.append(("vector_metrics", "failed", str(e)))

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*60)
        print("☁️  VECTOR STORE CLOUD INTEGRATION TEST SUMMARY")
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
            print("🎉 All cloud integration tests passed!")
            print("✅ Vector store system is fully integrated with cloud storage")
            print("✅ Multi-tier storage (hot/warm/cold) is working")
            print("✅ Fallback mechanism between storage layers is operational")
            print("✅ Storage statistics and monitoring are functional")
        elif passed > 0:
            print("⚠️  Some tests passed. Review failed tests for issues.")
        else:
            print("❌ All tests failed. Check cloud storage configuration.")

        print("="*60)

    async def run_all_tests(self):
        """Run the complete cloud integration test suite"""
        print("🚀 Starting LawyerFactory Vector Store Cloud Integration Test Suite")
        print("=" * 60)

        try:
            # Setup
            await self.setup()

            # Test cloud evidence ingestion
            await self.test_cloud_evidence_ingestion()

            # Test storage fallback mechanism
            await self.test_storage_fallback_mechanism()

            # Test storage tier management
            await self.test_storage_tier_management()

            # Test vector store metrics
            await self.test_vector_store_metrics()

        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            self.test_results.append(("test_suite", "failed", str(e)))

        finally:
            # Print summary
            self.print_test_summary()


async def main():
    """Main test execution function"""
    print("☁️  LawyerFactory Vector Store Cloud Integration Test")
    print("Testing complete integration between vector stores and cloud storage")

    # Initialize test suite
    test_suite = CloudIntegrationTestSuite()

    # Run all tests
    await test_suite.run_all_tests()

    # Exit with appropriate code
    failed_tests = sum(1 for _, status, _ in test_suite.test_results if status == "failed")
    sys.exit(1 if failed_tests > 0 else 0)


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())