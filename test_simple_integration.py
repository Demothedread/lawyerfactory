#!/usr/bin/env python3
"""
Simple Integration Test for LawyerFactory Unified Storage
Tests only the core unified storage functionality without complex imports.
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_core_storage():
    """Test core unified storage functionality"""
    logger.info("Testing core unified storage...")

    try:
        # Test 1: Import unified storage API
        logger.info("Test 1: Testing unified storage API import...")
        from lawyerfactory.storage.enhanced_unified_storage_api import (
            EnhancedUnifiedStorageAPI,
            EvidenceMetadata,
            get_enhanced_unified_storage_api,
        )
        logger.info("✓ Unified storage API imported successfully")

        # Test 2: Initialize unified storage
        logger.info("Test 2: Testing unified storage initialization...")
        unified_storage = get_enhanced_unified_storage_api()
        logger.info("✓ Unified storage initialized successfully")

        # Test 3: Test basic storage operation
        logger.info("Test 3: Testing basic storage operation...")
        test_content = b"Test document content for simple integration testing"
        test_filename = "test_simple_integration.txt"

        metadata = {
            "case_id": "test_case_simple",
            "source_phase": "simple_integration_test",
            "content_type": "text/plain"
        }

        storage_result = await unified_storage.store_evidence(
            file_content=test_content,
            filename=test_filename,
            metadata=metadata,
            source_phase="simple_integration_test"
        )

        if storage_result.success:
            logger.info(f"✓ Storage operation successful, ObjectID: {storage_result.object_id}")

            # Test retrieval
            retrieval_result = await unified_storage.get_evidence(storage_result.object_id)
            if "error" not in retrieval_result:
                logger.info("✓ Retrieval operation successful")
            else:
                logger.error(f"✗ Retrieval failed: {retrieval_result['error']}")
                return False
        else:
            logger.error(f"✗ Storage operation failed: {storage_result.error}")
            return False

        logger.info("🎉 Core storage integration test passed!")
        return True

    except ImportError as e:
        logger.error(f"✗ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Integration test failed: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("LawyerFactory Simple Storage Integration Test")
    logger.info("=" * 60)

    success = await test_core_storage()

    logger.info("=" * 60)
    if success:
        logger.info("✅ SIMPLE INTEGRATION TEST PASSED")
        logger.info("Core unified storage is working correctly!")
    else:
        logger.info("❌ SIMPLE INTEGRATION TEST FAILED")
        logger.info("Please check the error messages above.")
    logger.info("=" * 60)

    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)