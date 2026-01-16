#!/usr/bin/env python3
"""
Diagnostic script to test LawyerFactory component imports
"""

import sys
import os
from pathlib import Path

# Add src to path for lawyerfactory imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

print(f"Python path: {sys.path[:3]}")
print(f"Source path: {src_path}")
print(f"Source path exists: {src_path.exists()}")

# Test each import individually
imports_to_test = [
    ("lawyerfactory.agents.research.court_authority_helper", ["CourtAuthorityHelper", "JurisdictionContext", "LegalQuestionType"]),
    ("lawyerfactory.agents.research.research", ["ResearchBot"]),
    ("lawyerfactory.evidence.table", ["EnhancedEvidenceTable"]),
    ("lawyerfactory.phases.phaseA01_intake.enhanced_document_categorizer", ["DocumentMetadata", "DocumentType", "EnhancedDocumentCategorizer"]),
    ("lawyerfactory.phases.phaseA01_intake.intake_processor", ["EnhancedIntakeProcessor"]),
    ("lawyerfactory.outline.enhanced_generator", ["EnhancedSkeletalOutlineGenerator"]),
    ("lawyerfactory.claims.matrix", ["ComprehensiveClaimsMatrixIntegration"]),
    ("lawyerfactory.storage.enhanced_unified_storage_api", ["get_enhanced_unified_storage_api"]),
    ("lawyerfactory.kg.enhanced_graph", ["EnhancedKnowledgeGraph"]),
    ("lawyerfactory.phases.phaseA01_intake.evidence_routes", ["EvidenceAPI"]),
]

failed_imports = []
successful_imports = []

for module_name, expected_classes in imports_to_test:
    try:
        print(f"\n--- Testing {module_name} ---")
        module = __import__(module_name, fromlist=expected_classes)

        # Check if expected classes exist
        missing_classes = []
        for class_name in expected_classes:
            if not hasattr(module, class_name):
                missing_classes.append(class_name)

        if missing_classes:
            print(f"❌ Module imported but missing classes: {missing_classes}")
            failed_imports.append((module_name, f"Missing classes: {missing_classes}"))
        else:
            print(f"✅ Module imported successfully with all expected classes")
            successful_imports.append(module_name)

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        failed_imports.append((module_name, str(e)))
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        failed_imports.append((module_name, str(e)))

print("\n=== SUMMARY ===")
print(f"Successful imports: {len(successful_imports)}")
for module in successful_imports:
    print(f"  ✅ {module}")

print(f"\nFailed imports: {len(failed_imports)}")
for module, error in failed_imports:
    print(f"  ❌ {module}: {error}")

if failed_imports:
    print("\n=== DETAILED ANALYSIS ===")
    for module_name, error in failed_imports:
        print(f"\nAnalyzing {module_name}:")
        try:
            # Try to import just the parent modules to see where it fails
            parts = module_name.split('.')
            for i in range(1, len(parts) + 1):
                partial_name = '.'.join(parts[:i])
                try:
                    __import__(partial_name)
                    print(f"  ✅ {partial_name}")
                except ImportError as e:
                    print(f"  ❌ {partial_name}: {e}")
                    break
        except Exception as e:
            print(f"  ❌ Error analyzing {module_name}: {e}")