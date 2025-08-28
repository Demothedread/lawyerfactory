#!/usr/bin/env python3
"""
Test Script for LawyerFactory Vector Store System

This script validates the multi-purpose vector store system by:
1. Testing evidence ingestion from the test.pdf file
2. Validating vector store functionality
3. Testing semantic search capabilities
4. Demonstrating RAG integration
5. Testing validation type filtering

Usage:
    python test_vector_store.py

Requirements:
    - Run from law_venv environment
    - test.pdf file in root directory
    - All vector store modules properly installed
"""

import asyncio
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from lawyerfactory.vectors.enhanced_vector_store import (
        EnhancedVectorStoreManager,
        ValidationType,
        VectorStoreType,
    )
    from lawyerfactory.vectors.evidence_ingestion import EvidenceIngestionPipeline
    from lawyerfactory.vectors.llm_rag_integration import LegalDocumentGenerator
    from lawyerfactory.vectors.research_integration import ResearchRoundsManager
    print("✅ Successfully imported vector store modules")
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


class VectorStoreTestSuite:
    """Comprehensive test suite for vector store functionality"""

    def __init__(self):
        self.vector_store = None
        self.evidence_pipeline = None
        self.document_generator = None
        self.research_manager = None
        self.test_results = []

    async def setup(self):
        """Initialize all vector store components"""
        print("\n🔧 Setting up vector store components...")

        try:
            # Initialize vector store manager
            self.vector_store = EnhancedVectorStoreManager(
                storage_path="test_vector_stores"
            )
            print("✅ Vector store manager initialized")

            # Initialize evidence ingestion pipeline
            self.evidence_pipeline = EvidenceIngestionPipeline(self.vector_store)
            print("✅ Evidence ingestion pipeline initialized")

            # Initialize document generator
            self.document_generator = LegalDocumentGenerator(self.vector_store)
            print("✅ Legal document generator initialized")

            # Initialize research manager
            self.research_manager = ResearchRoundsManager(self.vector_store)
            print("✅ Research rounds manager initialized")

            self.test_results.append(("setup", "success", "All components initialized successfully"))

        except Exception as e:
            print(f"❌ Setup failed: {e}")
            self.test_results.append(("setup", "failed", str(e)))
            raise

    async def test_pdf_ingestion(self):
        """Test ingesting the test.pdf file"""
        print("\n📄 Testing PDF evidence ingestion...")

        try:
            # Check if test.pdf exists
            test_pdf_path = Path("test.pdf")
            if not test_pdf_path.exists():
                raise FileNotFoundError("test.pdf not found in root directory")

            print(f"📁 Found test.pdf: {test_pdf_path.absolute()}")

            # Create test metadata
            test_metadata = {
                "source": "test_document",
                "case_id": "TEST_CASE_001",
                "document_type": "news_article",
                "title": "Jeffrey Epstein Tapes: Claims About Donald Trump",
                "description": "Article about Jeffrey Epstein's recorded conversations regarding Donald Trump",
                "ingestion_date": datetime.now().isoformat(),
                "word_count": len(test_pdf_path.read_text().split()) if test_pdf_path.suffix == '.txt' else "unknown"
            }

            # Ingest the document
            doc_id = await self.evidence_pipeline.process_document_evidence(
                file_path=str(test_pdf_path),
                metadata=test_metadata
            )

            if doc_id.get("success"):
                print(f"✅ Document ingested successfully: {doc_id.get('document_id')}")
                print(f"   📊 Document type: {doc_id.get('document_type')}")
                print(f"   🏪 Vector store: {doc_id.get('vector_store')}")
                print(f"   ⚡ Processing time: {doc_id.get('processing_time'):.2f}s")

                self.test_results.append(("pdf_ingestion", "success", f"Document ID: {doc_id.get('document_id')}"))
                return doc_id.get('document_id')
            else:
                raise Exception(f"Ingestion failed: {doc_id.get('error')}")

        except Exception as e:
            print(f"❌ PDF ingestion test failed: {e}")
            self.test_results.append(("pdf_ingestion", "failed", str(e)))
            return None

    async def test_semantic_search(self, doc_id: str = None):
        """Test semantic search functionality"""
        print("\n🔍 Testing semantic search...")

        try:
            # Test queries related to the PDF content
            test_queries = [
                "Jeffrey Epstein and Donald Trump relationship",
                "Epstein tapes content",
                "Trump's personal conduct allegations",
                "friendship between Epstein and Trump"
            ]

            for query in test_queries:
                print(f"\n   Searching: '{query}'")

                # Perform semantic search
                results = await self.vector_store.semantic_search(
                    query=query,
                    store_type=VectorStoreType.GENERAL_RAG,
                    top_k=3
                )

                if results:
                    print(f"   ✅ Found {len(results)} results")
                    for i, (doc, score) in enumerate(results[:2], 1):
                        print(f"      {i}. Similarity: {score:.3f}")
                        print(f"         Content: {doc.content[:100]}...")
                else:
                    print("   ⚠️  No results found")

            self.test_results.append(("semantic_search", "success", f"Tested {len(test_queries)} queries"))

        except Exception as e:
            print(f"❌ Semantic search test failed: {e}")
            self.test_results.append(("semantic_search", "failed", str(e)))

    async def test_validation_filtering(self):
        """Test validation type filtering"""
        print("\n🎯 Testing validation type filtering...")

        try:
            # Test different validation types
            validation_types_to_test = [
                ValidationType.COMPLAINTS_AGAINST_TESLA,
                ValidationType.PERSONAL_INJURY,
                ValidationType.EMPLOYMENT_CLAIMS
            ]

            for validation_type in validation_types_to_test:
                print(f"\n   Testing {validation_type.value}...")

                # Get filtered sub-vector
                filtered_docs = await self.vector_store.get_validation_sub_vector(
                    validation_type=validation_type,
                    min_quality_score=0.0  # Accept any quality for testing
                )

                print(f"   📊 Found {len(filtered_docs)} documents for {validation_type.value}")

                if filtered_docs:
                    # Show first document info
                    first_doc = filtered_docs[0]
                    print(f"   📄 Sample document: {first_doc.metadata.get('title', 'Unknown')[:50]}...")
                    print(f"   🏷️  Validation types: {[vt.value for vt in first_doc.validation_types]}")

            self.test_results.append(("validation_filtering", "success", f"Tested {len(validation_types_to_test)} validation types"))

        except Exception as e:
            print(f"❌ Validation filtering test failed: {e}")
            self.test_results.append(("validation_filtering", "failed", str(e)))

    async def test_rag_context_retrieval(self):
        """Test RAG context retrieval"""
        print("\n🧠 Testing RAG context retrieval...")

        try:
            # Test RAG queries
            rag_queries = [
                "What did Jeffrey Epstein say about Donald Trump's personal life?",
                "Describe the relationship between Epstein and Trump",
                "What allegations were made about Trump's conduct?"
            ]

            for query in rag_queries:
                print(f"\n   RAG Query: '{query}'")

                # Get RAG context
                contexts = await self.vector_store.rag_retrieve_context(
                    query=query,
                    max_contexts=2,
                    context_window=500
                )

                if contexts:
                    print(f"   ✅ Retrieved {len(contexts)} context chunks")
                    for i, context in enumerate(contexts, 1):
                        print(f"      {i}. Context length: {len(context)} characters")
                        print(f"         Preview: {context[:100]}...")
                else:
                    print("   ⚠️  No context retrieved")

            self.test_results.append(("rag_context", "success", f"Tested {len(rag_queries)} RAG queries"))

        except Exception as e:
            print(f"❌ RAG context test failed: {e}")
            self.test_results.append(("rag_context", "failed", str(e)))

    async def test_research_round_integration(self):
        """Test research rounds integration"""
        print("\n🔬 Testing research rounds integration...")

        try:
            case_id = "TEST_CASE_001"
            round_number = 1

            # Start research round
            round_id = await self.research_manager.start_research_round(
                case_id=case_id,
                round_number=round_number,
                research_type="legal_research"
            )
            print(f"✅ Started research round: {round_id}")

            # Add research findings
            findings = [
                "Jeffrey Epstein claimed to be Donald Trump's closest friend for 10 years",
                "Epstein alleged Trump had a pattern of infidelity with friends' wives",
                "The relationship between Epstein and Trump ended around 2004",
                "Epstein claimed Trump first slept with Melania on his plane"
            ]

            for finding in findings:
                await self.research_manager.add_research_finding(
                    round_id=round_id,
                    finding=finding,
                    source="Epstein interview tapes",
                    confidence=0.8
                )

            # Add citations
            citations = [
                "Daily Beast article - Epstein Tapes (2024)",
                "Michael Wolff recordings (2017)",
                "Trump's public statements about Epstein"
            ]

            for citation in citations:
                await self.research_manager.add_research_citation(
                    round_id=round_id,
                    citation=citation,
                    authority_level="secondary",
                    relevance_score=0.7
                )

            # Complete research round
            success = await self.research_manager.complete_research_round(
                round_id=round_id,
                questions_answered=["What was Epstein's relationship with Trump?"],
                new_questions=["What evidence supports Epstein's claims?"]
            )

            if success:
                print("✅ Research round completed successfully")
                self.test_results.append(("research_rounds", "success", f"Completed round {round_id}"))
            else:
                raise Exception("Failed to complete research round")

        except Exception as e:
            print(f"❌ Research rounds test failed: {e}")
            self.test_results.append(("research_rounds", "failed", str(e)))

    async def test_legal_document_generation(self):
        """Test legal document generation with RAG"""
        print("\n📝 Testing legal document generation...")

        try:
            # Test case data
            case_data = {
                "case_name": "Epstein v. Trump Claims Analysis",
                "plaintiff_name": "Jeffrey Epstein (deceased)",
                "defendant_name": "Donald Trump",
                "case_number": "TEST-2024-001",
                "jurisdiction": "federal_court",
                "cause_of_action": "Defamation and Character Assassination",
                "claim_description": "Analysis of Epstein's claims about Trump's personal conduct and character"
            }

            # Generate complaint
            result = await self.document_generator.generate_legal_document(
                document_type="complaint",
                case_data=case_data,
                context_query="Epstein's allegations about Trump's personal life and conduct",
                use_rag=True
            )

            if result.get("success"):
                print("✅ Legal document generated successfully")
                print(f"   📊 Word count: {result.get('word_count')}")
                print(f"   ⏱️  Generation time: {result.get('generation_time'):.2f}s")
                print(f"   🧠 RAG context used: {result.get('rag_context_used')}")
                print(f"   📄 Citations found: {result.get('citations_found')}")

                # Show preview of generated content
                content = result.get('content', '')
                if len(content) > 500:
                    print(f"   📋 Content preview: {content[:500]}...")
                else:
                    print(f"   📋 Content: {content}")

                self.test_results.append(("document_generation", "success", f"Generated {result.get('word_count')} words"))
            else:
                raise Exception(f"Document generation failed: {result.get('error')}")

        except Exception as e:
            print(f"❌ Document generation test failed: {e}")
            self.test_results.append(("document_generation", "failed", str(e)))

    async def test_vector_store_metrics(self):
        """Test vector store metrics and health"""
        print("\n📊 Testing vector store metrics...")

        try:
            # Get store metrics
            metrics = await self.vector_store.get_store_metrics()

            print("✅ Vector store metrics retrieved")
            print(f"   📈 Total documents: {metrics.get('overall', {}).get('total_documents', 0)}")
            print(f"   🧠 Total vectors: {metrics.get('overall', {}).get('total_vectors', 0)}")
            print(f"   📁 Validation sub-vectors: {metrics.get('overall', {}).get('validation_sub_vectors', 0)}")

            # Show store-specific metrics
            for store_name, store_data in metrics.get('stores', {}).items():
                print(f"   🏪 {store_name}: {store_data.get('documents', 0)} documents")

            self.test_results.append(("store_metrics", "success", f"Metrics retrieved for {len(metrics.get('stores', {}))} stores"))

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
            # Setup
            await self.setup()

            # Test PDF ingestion
            doc_id = await self.test_pdf_ingestion()

            if doc_id:
                # Test semantic search
                await self.test_semantic_search(doc_id)

                # Test validation filtering
                await self.test_validation_filtering()

                # Test RAG context retrieval
                await self.test_rag_context_retrieval()

            # Test research rounds
            await self.test_research_round_integration()

            # Test document generation
            await self.test_legal_document_generation()

            # Test metrics
            await self.test_vector_store_metrics()

        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            self.test_results.append(("test_suite", "failed", str(e)))

        finally:
            # Print summary
            self.print_test_summary()


async def main():
    """Main test execution function"""
    print("🔬 LawyerFactory Vector Store Validation Test")
    print("Running from law_venv environment")

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