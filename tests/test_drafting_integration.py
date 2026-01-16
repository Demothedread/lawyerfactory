#!/usr/bin/env python3
"""
Simple Drafting Phase Integration Test
Tests the drafting phase components we implemented
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_drafting_imports():
    """Test that our drafting phase components can be imported"""
    print("🧪 Testing Drafting Phase Integration...")

    try:
        # Test unified storage
        from lawyerfactory.storage.core.unified_storage_api import get_enhanced_unified_storage_api
        print("✅ Unified storage API imported")

        # Test WriterBot import
        from lawyerfactory.compose.bots.writer import WriterBot
        print("✅ WriterBot imported")

        # Test AgentConfig import
        from lawyerfactory.compose.maestro.registry import AgentConfig
        print("✅ AgentConfig imported")

        # Test WorkflowTask import
        from lawyerfactory.compose.maestro.workflow_models import WorkflowTask
        print("✅ WorkflowTask imported")

        # Test storage initialization
        storage = get_enhanced_unified_storage_api()
        print("✅ Unified storage initialized")

        # Test WriterBot creation
        config = AgentConfig(
            agent_type='LegalWriterBot',
            model_name='gpt-4',
            temperature=0.1,
            max_tokens=2000
        )
        writer_bot = WriterBot(config)
        print("✅ WriterBot instance created")

        print("🎉 Drafting phase components ready!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_drafting_imports()
    print("\n" + "="*50)
    if success:
        print("✅ DRAFTING PHASE INTEGRATION TEST PASSED")
    else:
        print("❌ DRAFTING PHASE INTEGRATION TEST FAILED")
    print("="*50)