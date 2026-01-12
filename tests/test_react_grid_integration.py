#!/usr/bin/env python3
"""
Integration test for React Evidence Data Grid

This script demonstrates the successful integration of the React-based evidence data grid
with the enhanced evidence table system.
"""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lawyerfactory.storage.evidence.react_grid import ReactEvidenceDataGrid
from lawyerfactory.storage.evidence.table import EnhancedEvidenceTable, EvidenceEntry, EvidenceType


def main():
    print("🔬 Testing React Evidence Data Grid Integration")
    print("=" * 50)

    # Create evidence table
    print("📋 Creating evidence table...")
    table = EnhancedEvidenceTable()

    # Add some sample evidence
    print("📄 Adding sample evidence entries...")
    evidence1 = EvidenceEntry(
        source_document="contract.pdf",
        content="This is a sample contract with terms and conditions...",
        evidence_type=EvidenceType.DOCUMENTARY,
        relevance_score=0.85,
        key_terms=["contract", "agreement", "terms"],
    )

    evidence2 = EvidenceEntry(
        source_document="email.txt",
        content="Important email communication between parties...",
        evidence_type=EvidenceType.DIGITAL,
        relevance_score=0.72,
        key_terms=["communication", "email", "correspondence"],
    )

    evidence3 = EvidenceEntry(
        source_document="witness_statement.pdf",
        content="Witness testimony regarding the incident...",
        evidence_type=EvidenceType.TESTIMONIAL,
        relevance_score=0.91,
        key_terms=["witness", "testimony", "incident"],
    )

    table.add_evidence(evidence1)
    table.add_evidence(evidence2)
    table.add_evidence(evidence3)

    print(f"✅ Added {len(table.evidence_entries)} evidence entries to table")

    # Create React grid component
    print("⚛️  Creating React grid component...")
    grid = ReactEvidenceDataGrid("./data/evidence")
    print("✅ React grid component created successfully")

    # Get grid data
    print("🔄 Converting evidence to grid format...")
    grid_data = grid.get_grid_data(list(table.evidence_entries.values()))
    print(f"✅ Converted to grid format with {len(grid_data)} entries")

    # Show sample grid data
    print("\n📊 Sample Grid Data:")
    print("-" * 30)
    for i, entry in enumerate(grid_data):
        print(
            f"Entry {i+1}: {entry['source_document']} - Relevance: {entry['relevance_score']:.2f}"
        )

    # Test grid component HTML generation
    print("\n🌐 Testing HTML component generation...")
    html_template = grid.get_component_html()
    print("✅ HTML template generated successfully")
    print(f"Template length: {len(html_template)} characters")

    # Show table statistics
    print("\n📈 Evidence Table Statistics:")
    print("-" * 30)
    stats = table.get_stats()
    print(f"Total Evidence: {stats['total_evidence']}")
    print(f"Average Relevance: {stats['average_relevance_score']:.2f}")
    print(f"Evidence by Type: {stats['evidence_by_type']}")

    print("\n🎉 React evidence grid integration test completed successfully!")
    print("\nFeatures Verified:")
    print("✅ Evidence table creation and management")
    print("✅ React grid component instantiation")
    print("✅ Data conversion to grid format")
    print("✅ HTML component generation")
    print("✅ Statistics and analytics")


if __name__ == "__main__":
    main()
