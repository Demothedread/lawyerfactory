#!/usr/bin/env python3
"""
Court Authority Helper Usage Example

This script demonstrates how to use the CourtAuthorityHelper to:
1. Determine jurisdiction context from intake form data
2. Get optimized search hierarchy for caselaw research
3. Assess authority levels of found cases
4. Generate 0-6 star ratings for evidence table
"""

import asyncio
import json
from pathlib import Path

# Import the court authority helper
from src.lawyerfactory.agents.research.court_authority_helper import (
    CourtAuthorityHelper,
    JurisdictionContext,
    LegalQuestionType,
)


async def demonstrate_court_authority_helper():
    """Demonstrate the CourtAuthorityHelper functionality"""

    print("=== COURT AUTHORITY HELPER DEMONSTRATION ===\n")

    # Initialize the helper
    helper = CourtAuthorityHelper()

    # Example 1: Federal Procedural Question
    print("1. FEDERAL PROCEDURAL QUESTION")
    print("-" * 40)

    context = helper.determine_jurisdiction_context(
        jurisdiction="federal",
        question_type="procedural"
    )

    print(f"Context: {context.primary_jurisdiction} {context.question_type.value}")
    print(f"Court Type: {context.court_type}")

    hierarchy = helper.get_search_hierarchy(context)
    print("
Search Hierarchy (Priority Order):")
    for item in hierarchy:
        print(f"  Priority {item['priority']}: {item['jurisdiction']} {item['court']} ({item['authority']})")

    # Example 2: Federal Substantive Question with Event Location
    print("
2. FEDERAL SUBSTANTIVE QUESTION (DIVERSITY)")
    print("-" * 50)

    context2 = helper.determine_jurisdiction_context(
        jurisdiction="federal",
        question_type="substantive",
        event_location="California"  # From intake form
    )

    print(f"Context: {context2.primary_jurisdiction} {context2.question_type.value}")
    print(f"Event Location: {context2.event_location}")

    hierarchy2 = helper.get_search_hierarchy(context2)
    print("
Search Hierarchy:")
    for item in hierarchy2:
        print(f"  Priority {item['priority']}: {item['jurisdiction']} {item['court']} ({item['authority']})")

    # Example 3: State Law Question
    print("
3. STATE LAW QUESTION")
    print("-" * 25)

    context3 = helper.determine_jurisdiction_context(
        jurisdiction="california",
        question_type="substantive"
    )

    hierarchy3 = helper.get_search_hierarchy(context3)
    print("
Search Hierarchy:")
    for item in hierarchy3:
        print(f"  Priority {item['priority']}: {item['jurisdiction']} {item['court']} ({item['authority']})")

    # Example 4: Authority Assessment
    print("
4. AUTHORITY ASSESSMENT EXAMPLES")
    print("-" * 40)

    test_cases = [
        {
            "citation": "123 U.S. 456 (2023)",
            "court": "U.S. Supreme Court",
            "jurisdiction": "federal",
            "context": context,
            "description": "U.S. Supreme Court Case"
        },
        {
            "citation": "456 F.3d 789 (2022)",
            "court": "9th Circuit Court of Appeals",
            "jurisdiction": "federal",
            "context": context,
            "description": "Federal Circuit Court Case"
        },
        {
            "citation": "789 Cal.4th 123 (2021)",
            "court": "California Supreme Court",
            "jurisdiction": "california",
            "context": context3,
            "description": "State Supreme Court Case"
        },
        {
            "citation": "321 F. Supp. 654 (2020)",
            "court": "U.S. District Court",
            "jurisdiction": "federal",
            "context": context,
            "description": "Federal District Court Case"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        authority = helper.assess_caselaw_authority(
            case_citation=test_case["citation"],
            case_court=test_case["court"],
            case_jurisdiction=test_case["jurisdiction"],
            context=test_case["context"]
        )

        print(f"{i}. {test_case['description']}")
        print(f"   Citation: {test_case['citation']}")
        print(f"   Authority Level: {authority.authority_level.name}")
        print(f"   Star Rating: {'★' * authority.star_rating}")
        print(f"   Binding: {authority.is_binding}")
        print(f"   Reasoning: {authority.reasoning}")
        print(f"   Search Priority: {authority.search_priority}")
        print()

    # Example 5: Evidence Table Integration
    print("5. EVIDENCE TABLE INTEGRATION")
    print("-" * 35)

    # Create sample evidence table entry
    sample_evidence = {
        "evidence_entries": [
            {
                "evidence_id": "sample_1",
                "source_document": "Legal Brief",
                "content": "The court cited Smith v. Jones, 123 U.S. 456 (2023) for the proposition that...",
                "bluebook_citation": "Smith v. Jones, 123 U.S. 456 (2023)",
                "relevance_score": 0.8
            }
        ]
    }

    # Save sample evidence table
    evidence_path = "sample_evidence_table.json"
    with open(evidence_path, 'w') as f:
        json.dump(sample_evidence, f, indent=2)

    print(f"Created sample evidence table: {evidence_path}")

    # Assess authority for the evidence
    evidence_entry = sample_evidence["evidence_entries"][0]
    authority = helper.assess_caselaw_authority(
        case_citation=evidence_entry["bluebook_citation"],
        case_court="U.S. Supreme Court",  # Extracted from citation
        case_jurisdiction="federal",
        context=context
    )

    # Add authority rating to evidence entry
    evidence_entry["authority_rating"] = {
        "stars": authority.star_rating,
        "level": authority.authority_level.name,
        "is_binding": authority.is_binding,
        "reasoning": authority.reasoning,
        "color_code": "jade" if authority.star_rating >= 4 else "copper"
    }

    print("
Evidence Entry with Authority Rating:")
    print(json.dumps(evidence_entry, indent=2))

    # Example 6: Search Optimization
    print("
6. SEARCH OPTIMIZATION")
    print("-" * 25)

    # Simulate search results
    found_cases = 1  # Only found 1 case
    min_needed = 2   # Need at least 2 cases

    recommendations = helper.optimize_search_parameters(
        context=context,
        found_cases=found_cases,
        min_cases_needed=min_needed
    )

    print(f"Found {found_cases} cases, need {min_needed} cases")
    print("Search expansion recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. Search {rec['jurisdiction']} {rec['court']} ({rec['authority']})")

    print("
=== DEMONSTRATION COMPLETE ===")
    print("\nThe CourtAuthorityHelper provides:")
    print("✅ Jurisdiction-aware search optimization")
    print("✅ Authority level assessment (0-6 stars)")
    print("✅ Binding vs persuasive authority determination")
    print("✅ Evidence table integration with color coding")
    print("✅ Search parameter expansion when needed")
    print("✅ Integration with legal intake form data")


if __name__ == "__main__":
    asyncio.run(demonstrate_court_authority_helper())