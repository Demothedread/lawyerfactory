"""
# Script Name: fact_synthesis.py
# Description: Module for synthesizing a compelling narrative from structured case facts. This module ensures facts are presented in a clear, chronological order.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Document Generation
#   - Group Tags: null
Module for synthesizing a compelling narrative from structured case facts.
This module ensures facts are presented in a clear, chronological order.
"""
from datetime import datetime


def synthesize_facts(case_facts):
    """
    Transforms a list of fact dictionaries into a coherent, chronological narrative.

    Args:
        case_facts (list): A list of fact dictionaries from the knowledge graph.
                           Each fact can have an optional 'date' in ISO format.

    Returns:
        str: A formatted string representing the statement of facts.
    """
    # Sort facts by date, if available
    try:
        case_facts.sort(key=lambda x: datetime.fromisoformat(x.get('date', '')))
    except (ValueError, TypeError):
        # Handle cases where date is missing or malformed
        pass

    narrative = []
    for i, fact in enumerate(case_facts, 1):
        # More sophisticated narrative construction can be added here
        narrative.append(f"    {i}. {fact['text']}")
    
    return "\\n".join(narrative)
