"""
# Script Name: legal_theory_mapping.py
# Description: Module for mapping case facts to legal elements and integrating citations.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Document Generation
#   - Group Tags: null
Module for mapping case facts to legal elements and integrating citations.
"""


def map_facts_to_elements(causes_of_action, all_facts):
    """
    Maps facts to the legal elements of each cause of action.

    Args:
        causes_of_action (list): A list of cause of action dictionaries.
        all_facts (list): A list of all fact dictionaries for the case.

    Returns:
        list: The causes_of_action list, updated with fact text.
    """
    fact_map = {fact["id"]: fact["text"] for fact in all_facts}
    for cause in causes_of_action:
        for element in cause["elements"]:
            element["fact_text"] = [
                fact_map.get(fid) for fid in element["facts"] if fact_map.get(fid)
            ]
    return causes_of_action


def integrate_citations(causes_of_action, research_findings):
    """
    Integrates relevant citations for each legal element.

    Args:
        causes_of_action (list): The causes of action, with facts mapped.
        research_findings (dict): Findings from the research bot.

    Returns:
        list: The causes_of_action list, updated with citations.
    """
    # This is a simplified integration. A real system would use more
    # sophisticated logic to match citations to specific elements.
    for cause in causes_of_action:
        for element in cause["elements"]:
            # Prioritize citations based on relevance or other metrics
            sorted_citations = sorted(
                research_findings.get("citations", []),
                key=lambda x: x.get("relevance", 0),
                reverse=True,
            )
            element["citations"] = sorted_citations
    return causes_of_action
