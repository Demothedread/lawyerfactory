#!/usr/bin/env python3
"""
Simple Test Script for LLM Integration Functions

This script tests the LLM integration functions without requiring pytest.
"""

import os
from pathlib import Path
import sys


# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from lawyerfactory.phases.phaseA01_intake.assessor import simple_categorize, LLM_INTEGRATION_AVAILABLE, ingest_files
from lawyerfactory.phases.phaseA01_intake.llm_integration import (
    llm_classify_evidence as llm_categorize_document,
    llm_extract_metadata as llm_extract_document_metadata,
    llm_summarize_text as llm_generate_summary
)

print("✅ Successfully imported test functions")


def test_simple_categorize():
    """Test the enhanced simple_categorize function."""
    print("\n🧪 Testing simple_categorize function...")

    test_cases = [
        # (input_text, expected_category)
        ("This contract agreement between parties", "contract"),
        ("Plaintiff files complaint against defendant", "litigation"),
        ("Invoice for services rendered", "financial"),
        ("Email correspondence regarding the matter", "correspondence"),
        ("Compliance with regulations required", "regulatory"),
        ("Employment contract terms", "employment"),
        ("Property lease agreement", "real_estate"),
        ("Patent application filed", "intellectual_property"),
        ("Medical treatment records", "medical"),
        ("This is a general document", "general"),
        ("", "general"),
        ("No specific legal keywords here", "general"),
    ]

    passed = 0
    failed = 0

    for text, expected in test_cases:
        result = simple_categorize(text)
        if result == expected:
            print(f"✅ '{text[:30]}...' → {result}")
            passed += 1
        else:
            print(f"❌ '{text[:30]}...' → {result} (expected {expected})")
            failed += 1

    print(f"simple_categorize: {passed} passed, {failed} failed")
    return failed == 0


def test_llm_functions():
    """Test LLM functions and their fallback mechanisms."""
    print("\n🧪 Testing LLM functions...")

    test_text = "This is a sample legal document for testing purposes."
    test_filename = "test_document.txt"

    tests_passed = 0
    tests_failed = 0

    try:
        # Test llm_categorize_document
        result = llm_categorize_document(test_text, test_filename)
        if isinstance(result, dict) and "document_type" in result:
            print("✅ llm_categorize_document works")
            tests_passed += 1
        else:
            print("❌ llm_categorize_document failed")
            tests_failed += 1
    except Exception as e:
        print(f"❌ llm_categorize_document error: {e}")
        tests_failed += 1

    try:
        # Test llm_extract_document_metadata
        result = llm_extract_document_metadata(test_text, test_filename)
        if isinstance(result, dict) and "title" in result:
            print("✅ llm_extract_document_metadata works")
            tests_passed += 1
        else:
            print("❌ llm_extract_document_metadata failed")
            tests_failed += 1
    except Exception as e:
        print(f"❌ llm_extract_document_metadata error: {e}")
        tests_failed += 1

    try:
        # Test llm_generate_summary
        result = llm_generate_summary(test_text)
        if isinstance(result, str) and len(result) > 0:
            print("✅ llm_generate_summary works")
            tests_passed += 1
        else:
            print("❌ llm_generate_summary failed")
            tests_failed += 1
    except Exception as e:
        print(f"❌ llm_generate_summary error: {e}")
        tests_failed += 1

    print(f"LLM functions: {tests_passed} passed, {tests_failed} failed")
    print(f"LLM Integration Available: {LLM_INTEGRATION_AVAILABLE}")

    return tests_failed == 0


def test_file_processing():
    """Test file processing functions."""
    print("\n🧪 Testing file processing...")

    try:
        # Test with empty list
        results = ingest_files([])
        if results == []:
            print("✅ ingest_files handles empty list")
            return True
        else:
            print("❌ ingest_files failed on empty list")
            return False
    except Exception as e:
        print(f"❌ ingest_files error: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting LLM Integration Tests")
    print("=" * 50)

    all_passed = True

    # Test simple_categorize
    if not test_simple_categorize():
        all_passed = False

    # Test LLM functions
    if not test_llm_functions():
        all_passed = False

    # Test file processing
    if not test_file_processing():
        all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
