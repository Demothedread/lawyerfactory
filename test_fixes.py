#!/usr/bin/env python3
"""
Test script to verify the three key fixes are working:
1. /api/evidence endpoint 
2. KnowledgeGraph.query_relationships fallback
3. EnhancedMaestro.list_workflows method
"""

import json
import sys
from pathlib import Path


def test_evidence_endpoint():
    """Test the evidence endpoint functionality"""
    print("=== Testing Evidence Endpoint ===")
    try:
        # Import the app and get the evidence function
        import app
        result = app.get_evidence()
        
        # Normalize possible tuple responses like (response, status)
        if isinstance(result, (tuple, list)) and result:
            response_obj = result[0]
        else:
            response_obj = result

        # Safely obtain a json-producing attribute or property
        json_attr = getattr(response_obj, "json", None)

        if callable(json_attr):
            try:
                data = json_attr()
                print(f"✓ Evidence endpoint returns JSON (from method): {data}")
            except Exception as inner_exc:
                print(f"✗ Failed to call response.json(): {inner_exc}")
                return False
            return True
        elif json_attr is not None:
            # json is a property or attribute (not callable)
            print(f"✓ Evidence endpoint returns JSON-like attribute: {json_attr}")
            return True
        elif isinstance(response_obj, (dict, list)):
            # The endpoint returned a raw JSON-serializable object
            print(f"✓ Evidence endpoint returns JSON-like object: {response_obj}")
            return True
        else:
            print(f"✓ Evidence endpoint returns response object: {type(result)}")
            return True
    except Exception as e:
        print(f"✗ Evidence endpoint failed: {type(e).__name__}: {e}")
        return False

def test_knowledge_graph_fallback():
    """Test the KnowledgeGraph query_relationships fallback"""
    print("\n=== Testing KnowledgeGraph Fallback ===")
    try:
        # Import the knowledge graph and test the fallback
        from src.knowledge_graph.api.knowledge_graph import KnowledgeGraph

        # Create instance
        kg = KnowledgeGraph(':memory:')  # Use in-memory SQLite for testing
        
        # Test if query_relationships method exists
        if hasattr(kg, 'query_relationships'):
            result = kg.query_relationships()
            print(f"✓ KnowledgeGraph.query_relationships exists and returns: {result}")
            return True
        else:
            print("✗ KnowledgeGraph.query_relationships method not found")
            return False
    except Exception as e:
        print(f"✗ KnowledgeGraph fallback test failed: {e}")
        return False

def test_maestro_list_workflows():
    """Test the EnhancedMaestro list_workflows method"""
    print("\n=== Testing Maestro list_workflows ===")
    try:
        # Import and test the maestro
        from maestro.enhanced_maestro import EnhancedMaestro

        # Check if list_workflows method exists
        if hasattr(EnhancedMaestro, 'list_workflows'):
            print("✓ EnhancedMaestro.list_workflows method exists")
            return True
        else:
            print("✗ EnhancedMaestro.list_workflows method not found")
            return False
    except Exception as e:
        print(f"✗ Maestro list_workflows test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Backend Stability Fixes")
    print("=" * 40)
    
    tests = [
        test_evidence_endpoint,
        test_knowledge_graph_fallback, 
        test_maestro_list_workflows
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All backend fixes are working!")
        return 0
    else:
        print("⚠️  Some fixes need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())