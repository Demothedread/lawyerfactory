"""
# Script Name: court_authority_helper.py
# Description: Court Authority Helper Agent for determining caselaw binding/persuasive authority based on jurisdiction and legal context. Provides hierarchical ranking algorithm for legal research prioritization.
# Relationships:
#   - Entity Type: Agent
#   - Directory Group: Research
#   - Group Tags: legal-research, authority-ranking
Court Authority Helper Agent for LawyerFactory Research Phase.

This agent implements a sophisticated hierarchy ranking algorithm for determining
caselaw authority levels based on jurisdiction, court type, and legal context.
It provides:
- Jurisdiction-specific authority rules
- Binding vs persuasive authority determination
- Search parameter optimization
- 0-6 star rating system for evidence evaluation
- Integration with legal intake form data for event location context
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class AuthorityLevel(Enum):
    """Authority levels from highest to lowest"""
    BINDING_SUPREME = 6      # U.S. Supreme Court, State Supreme Court
    BINDING_HIGH = 5         # Circuit Courts of Appeals, State Appellate Courts
    BINDING_DISTRICT = 4     # Federal District Courts, State Trial Courts
    PERSUASIVE_STRONG = 3    # Same circuit/other high courts
    PERSUASIVE_MEDIUM = 2    # Other circuits/same state
    PERSUASIVE_WEAK = 1      # Other states/dissimilar jurisdictions
    NO_AUTHORITY = 0         # No precedential value


class LegalQuestionType(Enum):
    """Type of legal question being researched"""
    PROCEDURAL = "procedural"
    SUBSTANTIVE_FEDERAL = "substantive_federal"
    SUBSTANTIVE_STATE = "substantive_state"
    SUBSTANTIVE_FEDERAL_DIVERSITY = "substantive_federal_diversity"


@dataclass
class JurisdictionContext:
    """Context information for jurisdiction determination"""
    primary_jurisdiction: str  # e.g., "federal", "california", "new_york"
    court_type: str  # e.g., "district", "circuit", "supreme"
    event_location: Optional[str] = None  # From intake form
    venue: Optional[str] = None
    question_type: LegalQuestionType = LegalQuestionType.SUBSTANTIVE_STATE


@dataclass
class AuthorityRule:
    """Rule for determining authority level"""
    jurisdiction_type: str
    court_hierarchy: List[str]
    binding_courts: List[str]
    persuasive_courts: List[str]
    notes: str = ""


@dataclass
class CaselawAuthority:
    """Authority assessment for a specific case"""
    case_name: str
    citation: str
    court: str
    jurisdiction: str
    authority_level: AuthorityLevel
    star_rating: int
    is_binding: bool
    reasoning: str
    search_priority: int  # 1 = highest priority for search


class CourtAuthorityHelper:
    """
    Helper agent for determining caselaw authority hierarchy and search optimization.

    This agent implements the court authority rules from courtAuthority.txt as a
    Python algorithm that can be integrated with the caselaw researcher.
    """

    def __init__(self):
        self.authority_rules = self._initialize_authority_rules()
        self.jurisdiction_cache = {}

    def _initialize_authority_rules(self) -> Dict[str, AuthorityRule]:
        """Initialize authority rules based on courtAuthority.txt content"""

        return {
            "federal_procedural": AuthorityRule(
                jurisdiction_type="federal_procedural",
                court_hierarchy=[
                    "U.S. Supreme Court",
                    "Controlling Circuit (en banc > panel)",
                    "Local circuit rules, district local rules, judge standing orders",
                    "Law-of-the-case/mandate within same litigation"
                ],
                binding_courts=[
                    "U.S. Supreme Court",
                    "Controlling Circuit (en banc)",
                    "Controlling Circuit (panel)",
                    "Local circuit rules",
                    "District local rules",
                    "Judge standing orders"
                ],
                persuasive_courts=[
                    "Other circuits' decisions",
                    "Other districts' decisions",
                    "Advisory Committee Notes",
                    "Leading treatises (Wright & Miller)",
                    "State law analogies"
                ],
                notes="Federal procedural questions follow strict hierarchy"
            ),

            "federal_substantive": AuthorityRule(
                jurisdiction_type="federal_substantive",
                court_hierarchy=[
                    "U.S. Supreme Court on federal law",
                    "Controlling Circuit",
                    "Agency rules/precedents in circuit"
                ],
                binding_courts=[
                    "U.S. Supreme Court",
                    "Controlling Circuit (en banc)",
                    "Controlling Circuit (panel)"
                ],
                persuasive_courts=[
                    "Other circuits and districts",
                    "Non-controlling agency views",
                    "Restatements",
                    "Scholarly work"
                ],
                notes="Federal substantive law requires event location for diversity jurisdiction"
            ),

            "state_procedural": AuthorityRule(
                jurisdiction_type="state_procedural",
                court_hierarchy=[
                    "State supreme court",
                    "State intermediate appellate precedent",
                    "State trial courts (binding on same level)"
                ],
                binding_courts=[
                    "State supreme court",
                    "State intermediate appellate courts",
                    "State trial courts (horizontal binding)"
                ],
                persuasive_courts=[
                    "Other states' decisions",
                    "Federal cases by analogy",
                    "Treatises",
                    "Court administration guidance"
                ],
                notes="State procedural rules vary by jurisdiction"
            ),

            "state_substantive": AuthorityRule(
                jurisdiction_type="state_substantive",
                court_hierarchy=[
                    "State's highest court",
                    "State constitution & statutes",
                    "State intermediate appellate precedent"
                ],
                binding_courts=[
                    "State supreme court",
                    "State constitution",
                    "State statutes",
                    "State intermediate appellate courts"
                ],
                persuasive_courts=[
                    "Other states' courts",
                    "Federal courts applying state law",
                    "Restatements",
                    "Scholarship"
                ],
                notes="State substantive law is binding within state boundaries"
            )
        }

    def determine_jurisdiction_context(
        self,
        jurisdiction: str,
        question_type: str = "substantive",
        event_location: Optional[str] = None,
        venue: Optional[str] = None
    ) -> JurisdictionContext:
        """
        Determine jurisdiction context from input parameters.

        Args:
            jurisdiction: Primary jurisdiction (federal, state name, etc.)
            question_type: Type of legal question (procedural/substantive)
            event_location: Where events occurred (from intake form)
            venue: Court where case is filed

        Returns:
            JurisdictionContext with determined parameters
        """

        # Determine question type
        if question_type == "procedural":
            if jurisdiction.lower() == "federal":
                legal_q_type = LegalQuestionType.PROCEDURAL
            else:
                legal_q_type = LegalQuestionType.PROCEDURAL
        else:  # substantive
            if jurisdiction.lower() == "federal":
                if event_location:
                    legal_q_type = LegalQuestionType.SUBSTANTIVE_FEDERAL_DIVERSITY
                else:
                    legal_q_type = LegalQuestionType.SUBSTANTIVE_FEDERAL
            else:
                legal_q_type = LegalQuestionType.SUBSTANTIVE_STATE

        # Determine court type
        court_type = "district"  # default
        if venue:
            venue_lower = venue.lower()
            if "supreme" in venue_lower:
                court_type = "supreme"
            elif "appeal" in venue_lower or "appellate" in venue_lower:
                court_type = "appellate"
            elif "circuit" in venue_lower:
                court_type = "circuit"

        return JurisdictionContext(
            primary_jurisdiction=jurisdiction,
            court_type=court_type,
            event_location=event_location,
            venue=venue,
            question_type=legal_q_type
        )

    def get_search_hierarchy(self, context: JurisdictionContext) -> List[Dict[str, Any]]:
        """
        Get search hierarchy for jurisdiction - binding first, then persuasive.

        Returns list of search parameters in priority order.
        Each entry contains jurisdiction, court level, and authority weight.
        """

        hierarchy = []

        if context.question_type == LegalQuestionType.PROCEDURAL:
            if context.primary_jurisdiction.lower() == "federal":
                # Federal procedural hierarchy
                hierarchy = [
                    {"jurisdiction": "federal", "court": "supreme_court", "authority": "binding", "priority": 1},
                    {"jurisdiction": "federal", "court": "circuit_court", "authority": "binding", "priority": 2},
                    {"jurisdiction": "federal", "court": "district_court", "authority": "binding", "priority": 3},
                    {"jurisdiction": "federal", "court": "other_circuits", "authority": "persuasive", "priority": 4},
                    {"jurisdiction": "federal", "court": "other_districts", "authority": "persuasive", "priority": 5},
                ]
            else:
                # State procedural hierarchy
                hierarchy = [
                    {"jurisdiction": context.primary_jurisdiction, "court": "supreme_court", "authority": "binding", "priority": 1},
                    {"jurisdiction": context.primary_jurisdiction, "court": "appellate_court", "authority": "binding", "priority": 2},
                    {"jurisdiction": context.primary_jurisdiction, "court": "trial_court", "authority": "binding", "priority": 3},
                    {"jurisdiction": "other_states", "court": "any", "authority": "persuasive", "priority": 4},
                ]

        elif context.question_type == LegalQuestionType.SUBSTANTIVE_FEDERAL:
            # Federal substantive (federal question)
            hierarchy = [
                {"jurisdiction": "federal", "court": "supreme_court", "authority": "binding", "priority": 1},
                {"jurisdiction": "federal", "court": "circuit_court", "authority": "binding", "priority": 2},
                {"jurisdiction": "federal", "court": "other_circuits", "authority": "persuasive", "priority": 3},
                {"jurisdiction": "federal", "court": "district_courts", "authority": "persuasive", "priority": 4},
            ]

        elif context.question_type == LegalQuestionType.SUBSTANTIVE_FEDERAL_DIVERSITY:
            # Federal substantive (diversity jurisdiction) - need event location
            if context.event_location:
                state = self._extract_state_from_location(context.event_location)
                hierarchy = [
                    {"jurisdiction": state, "court": "supreme_court", "authority": "binding", "priority": 1},
                    {"jurisdiction": state, "court": "appellate_court", "authority": "binding", "priority": 2},
                    {"jurisdiction": state, "court": "trial_court", "authority": "persuasive", "priority": 3},
                    {"jurisdiction": "federal", "court": "supreme_court", "authority": "persuasive", "priority": 4},
                    {"jurisdiction": "federal", "court": "circuit_court", "authority": "persuasive", "priority": 5},
                ]
            else:
                # Fallback to general federal
                hierarchy = [
                    {"jurisdiction": "federal", "court": "supreme_court", "authority": "binding", "priority": 1},
                    {"jurisdiction": "federal", "court": "circuit_court", "authority": "binding", "priority": 2},
                ]

        else:  # SUBSTANTIVE_STATE
            # State substantive law
            hierarchy = [
                {"jurisdiction": context.primary_jurisdiction, "court": "supreme_court", "authority": "binding", "priority": 1},
                {"jurisdiction": context.primary_jurisdiction, "court": "appellate_court", "authority": "binding", "priority": 2},
                {"jurisdiction": context.primary_jurisdiction, "court": "trial_court", "authority": "persuasive", "priority": 3},
                {"jurisdiction": "other_states", "court": "supreme_court", "authority": "persuasive", "priority": 4},
                {"jurisdiction": "federal", "court": "supreme_court", "authority": "persuasive", "priority": 5},
            ]

        return hierarchy

    def assess_caselaw_authority(
        self,
        case_citation: str,
        case_court: str,
        case_jurisdiction: str,
        context: JurisdictionContext
    ) -> CaselawAuthority:
        """
        Assess the authority level of a specific case.

        Args:
            case_citation: Case citation
            case_court: Court that decided the case
            case_jurisdiction: Jurisdiction of the case
            context: Current jurisdiction context

        Returns:
            CaselawAuthority with rating and reasoning
        """

        # Determine authority level based on jurisdiction match and court level
        authority_level = self._calculate_authority_level(
            case_court, case_jurisdiction, context
        )

        star_rating = authority_level.value
        is_binding = authority_level.value >= 4  # 4-6 stars = binding

        reasoning = self._generate_authority_reasoning(
            case_court, case_jurisdiction, context, authority_level
        )

        # Calculate search priority (inverse of star rating for binding preference)
        search_priority = 7 - star_rating  # Higher stars = lower priority numbers

        return CaselawAuthority(
            case_name=f"Case from {case_court}",
            citation=case_citation,
            court=case_court,
            jurisdiction=case_jurisdiction,
            authority_level=authority_level,
            star_rating=star_rating,
            is_binding=is_binding,
            reasoning=reasoning,
            search_priority=search_priority
        )

    def _calculate_authority_level(
        self,
        case_court: str,
        case_jurisdiction: str,
        context: JurisdictionContext
    ) -> AuthorityLevel:
        """Calculate authority level based on court hierarchy"""

        case_court_lower = case_court.lower()
        case_jur_lower = case_jurisdiction.lower()
        context_jur_lower = context.primary_jurisdiction.lower()

        # U.S. Supreme Court - always highest authority
        if "supreme" in case_court_lower and "u.s." in case_court_lower:
            return AuthorityLevel.BINDING_SUPREME

        # State Supreme Court - highest in state
        if "supreme" in case_court_lower and case_jur_lower == context_jur_lower:
            return AuthorityLevel.BINDING_SUPREME

        # Circuit Courts of Appeals
        if "circuit" in case_court_lower and case_jur_lower == context_jur_lower:
            return AuthorityLevel.BINDING_HIGH

        # State Appellate Courts
        if ("appeal" in case_court_lower or "appellate" in case_court_lower) and case_jur_lower == context_jur_lower:
            return AuthorityLevel.BINDING_HIGH

        # Federal District Courts
        if "district" in case_court_lower and case_jur_lower == "federal":
            return AuthorityLevel.BINDING_DISTRICT

        # State Trial Courts
        if case_jur_lower == context_jur_lower and "district" in case_court_lower:
            return AuthorityLevel.BINDING_DISTRICT

        # Same circuit/other high courts - persuasive strong
        if case_jur_lower == context_jur_lower:
            return AuthorityLevel.PERSUASIVE_STRONG

        # Other circuits/same state - persuasive medium
        if case_jur_lower == "federal" or case_jur_lower == context_jur_lower:
            return AuthorityLevel.PERSUASIVE_MEDIUM

        # Other states/dissimilar - persuasive weak
        return AuthorityLevel.PERSUASIVE_WEAK

    def _generate_authority_reasoning(
        self,
        case_court: str,
        case_jurisdiction: str,
        context: JurisdictionContext,
        authority_level: AuthorityLevel
    ) -> str:
        """Generate reasoning for authority assessment"""

        if authority_level == AuthorityLevel.BINDING_SUPREME:
            return f"U.S. Supreme Court precedent is binding on all courts"
        elif authority_level == AuthorityLevel.BINDING_HIGH:
            return f"Circuit/Appellate court in {context.primary_jurisdiction} is binding on lower courts"
        elif authority_level == AuthorityLevel.BINDING_DISTRICT:
            return f"District/Trial court decisions are binding horizontally"
        elif authority_level == AuthorityLevel.PERSUASIVE_STRONG:
            return f"Same jurisdiction provides strong persuasive authority"
        elif authority_level == AuthorityLevel.PERSUASIVE_MEDIUM:
            return f"Similar jurisdiction provides moderate persuasive authority"
        elif authority_level == AuthorityLevel.PERSUASIVE_WEAK:
            return f"Different jurisdiction provides weak persuasive authority only"
        else:
            return f"No precedential authority in this context"

    def _extract_state_from_location(self, location: str) -> str:
        """Extract state from location string"""
        # Simple state extraction - could be enhanced with proper geolocation
        location_lower = location.lower()

        state_map = {
            'california': 'california',
            'ca': 'california',
            'new york': 'new_york',
            'ny': 'new_york',
            'texas': 'texas',
            'tx': 'texas',
            'florida': 'florida',
            'fl': 'florida',
            # Add more states as needed
        }

        for key, state in state_map.items():
            if key in location_lower:
                return state

        return location  # Fallback to original

    def optimize_search_parameters(
        self,
        context: JurisdictionContext,
        found_cases: int,
        min_cases_needed: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Optimize search parameters based on results.

        If fewer than min_cases_needed found, expand search to more persuasive authorities.
        """

        search_hierarchy = self.get_search_hierarchy(context)

        if found_cases >= min_cases_needed:
            # Return only binding authorities
            return [item for item in search_hierarchy if item["authority"] == "binding"]
        else:
            # Expand to persuasive authorities
            return search_hierarchy

    def add_authority_rating_to_evidence_table(
        self,
        evidence_table_path: str,
        intake_form_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add authority rating column to evidence table.

        Args:
            evidence_table_path: Path to evidence_table.json
            intake_form_data: Data from legal intake form for jurisdiction context

        Returns:
            bool: Success status
        """

        try:
            # Load evidence table
            with open(evidence_table_path, 'r', encoding='utf-8') as f:
                table_data = json.load(f)

            # Extract jurisdiction context from intake form
            jurisdiction = intake_form_data.get('jurisdiction', 'federal') if intake_form_data else 'federal'
            event_location = intake_form_data.get('event_location') if intake_form_data else None

            context = self.determine_jurisdiction_context(
                jurisdiction=jurisdiction,
                event_location=event_location
            )

            # Process each evidence entry
            for entry in table_data.get('evidence_entries', []):
                # Extract case information from content or citation
                content = entry.get('content', '')
                citation = entry.get('bluebook_citation', '')

                if citation:
                    # Parse citation to extract court and jurisdiction
                    court, case_jurisdiction = self._parse_citation(citation)
                else:
                    # Try to extract from content
                    court, case_jurisdiction = self._extract_court_from_content(content)

                if court and case_jurisdiction:
                    # Assess authority
                    authority = self.assess_caselaw_authority(
                        case_citation=citation,
                        case_court=court,
                        case_jurisdiction=case_jurisdiction,
                        context=context
                    )

                    # Add authority information to entry
                    entry['authority_rating'] = {
                        'stars': authority.star_rating,
                        'level': authority.authority_level.name,
                        'is_binding': authority.is_binding,
                        'reasoning': authority.reasoning,
                        'color_code': self._get_color_code(authority.star_rating)
                    }

            # Save updated table
            with open(evidence_table_path, 'w', encoding='utf-8') as f:
                json.dump(table_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Added authority ratings to {len(table_data.get('evidence_entries', []))} evidence entries")
            return True

        except Exception as e:
            logger.error(f"Failed to add authority ratings to evidence table: {e}")
            return False

    def _parse_citation(self, citation: str) -> Tuple[str, str]:
        """Parse citation to extract court and jurisdiction"""
        # Simple citation parsing - could be enhanced
        citation_lower = citation.lower()

        # Federal courts
        if 'u.s.' in citation_lower or 's. ct.' in citation_lower:
            return "U.S. Supreme Court", "federal"
        elif 'f.' in citation_lower and 'circ' in citation_lower:
            return "Federal Circuit Court", "federal"
        elif 'f. supp.' in citation_lower:
            return "Federal District Court", "federal"

        # State courts - simplified
        state_indicators = {
            'cal.': 'california',
            'n.y.': 'new_york',
            'tex.': 'texas',
            'fla.': 'florida'
        }

        for indicator, state in state_indicators.items():
            if indicator in citation_lower:
                if 'supreme' in citation_lower:
                    return f"{state.title()} Supreme Court", state
                elif 'app.' in citation_lower or 'appeal' in citation_lower:
                    return f"{state.title()} Appellate Court", state
                else:
                    return f"{state.title()} Trial Court", state

        return "Unknown Court", "unknown"

    def _extract_court_from_content(self, content: str) -> Tuple[str, str]:
        """Extract court information from content text"""
        content_lower = content.lower()

        # Look for court names in content
        if 'supreme court' in content_lower:
            if 'u.s.' in content_lower or 'united states' in content_lower:
                return "U.S. Supreme Court", "federal"
            else:
                return "State Supreme Court", "unknown"

        if 'circuit' in content_lower and 'court' in content_lower:
            return "Circuit Court", "federal"

        if 'district' in content_lower and 'court' in content_lower:
            return "District Court", "federal"

        return "Unknown Court", "unknown"

    def _get_color_code(self, star_rating: int) -> str:
        """Get color code for star rating"""
        if star_rating == 0:
            return "gray"  # No authority
        elif star_rating <= 3:
            return "copper"  # Persuasive (least to most)
        else:
            return "jade"  # Binding (least to most)

    def generate_authority_prompt_instructions(self) -> str:
        """
        Generate prompt instructions for caselaw researcher based on authority rules.
        This can be used to enhance the researcher's prompts.
        """

        return """
COURT AUTHORITY HIERARCHY INSTRUCTIONS:

When searching for caselaw, always prioritize by authority level:

1. BINDING AUTHORITY (Search First - Stars 4-6):
   - U.S. Supreme Court decisions (★6)
   - Controlling Circuit Court decisions (★5)
   - State Supreme Court decisions (★6)
   - State Appellate Court decisions (★5)
   - Federal District Court decisions (★4)
   - State Trial Court decisions (★4)

2. PERSUASIVE AUTHORITY (Search Only If <2 Binding Cases Found - Stars 1-3):
   - Same jurisdiction, different court level (★3)
   - Similar jurisdictions (★2)
   - Different jurisdictions (★1)

3. JURISDICTION-SPECIFIC RULES:

   FEDERAL PROCEDURAL:
   - U.S. Constitution, federal statutes, Federal Rules
   - Controlling Circuit (en banc > panel)
   - Local rules, judge standing orders

   FEDERAL SUBSTANTIVE (Federal Question):
   - U.S. Supreme Court on federal law
   - Controlling Circuit decisions
   - Agency rules/precedents

   FEDERAL SUBSTANTIVE (Diversity - State Law):
   - State Supreme Court on state law
   - State constitution & statutes
   - State intermediate appellate decisions

   STATE PROCEDURAL:
   - State supreme court interpretations
   - State intermediate appellate decisions
   - State trial court decisions (horizontal binding)

   STATE SUBSTANTIVE:
   - State supreme court decisions
   - State constitution & statutes
   - State intermediate appellate decisions

4. SEARCH STRATEGY:
   - Start with binding authorities only
   - If fewer than 2 cases found, expand to persuasive authorities
   - For federal substantive questions, identify event location from intake form
   - Prioritize same jurisdiction over different jurisdictions
   - Federal courts generally prefer other federal courts over state courts

5. RATING SYSTEM:
   - ★★★★★★ (6 stars): U.S. Supreme Court, State Supreme Court
   - ★★★★★ (5 stars): Circuit Courts of Appeals, State Appellate Courts
   - ★★★★ (4 stars): Federal District Courts, State Trial Courts
   - ★★★ (3 stars): Same jurisdiction, different court level
   - ★★ (2 stars): Similar jurisdictions
   - ★ (1 star): Different jurisdictions
   - ☆ (0 stars): No precedential authority

Color Coding: Copper (persuasive), Jade (binding), Gray (no authority)
"""


# Integration function for caselaw researcher
def integrate_with_caselaw_researcher():
    """
    Integration function to add court authority helper to caselaw researcher.
    This would be called from the caselaw researcher to enhance its functionality.
    """

    helper = CourtAuthorityHelper()

    # Example integration points:

    # 1. Before searching, get jurisdiction context
    # jurisdiction_context = helper.determine_jurisdiction_context(...)

    # 2. Get search hierarchy for optimization
    # search_hierarchy = helper.get_search_hierarchy(jurisdiction_context)

    # 3. After finding cases, assess their authority
    # for case in found_cases:
    #     authority = helper.assess_caselaw_authority(...)

    # 4. Add ratings to evidence table
    # helper.add_authority_rating_to_evidence_table(...)

    return helper


if __name__ == "__main__":
    # Example usage
    helper = CourtAuthorityHelper()

    # Example: Federal procedural question
    context = helper.determine_jurisdiction_context(
        jurisdiction="federal",
        question_type="procedural"
    )

    hierarchy = helper.get_search_hierarchy(context)
    print("Search Hierarchy for Federal Procedural:")
    for item in hierarchy:
        print(f"  Priority {item['priority']}: {item['jurisdiction']} {item['court']} ({item['authority']})")

    # Example authority assessment
    authority = helper.assess_caselaw_authority(
        case_citation="123 F.3d 456 (2023)",
        case_court="U.S. Court of Appeals",
        case_jurisdiction="federal",
        context=context
    )

    print(f"\nAuthority Assessment: {authority.star_rating} stars")
    print(f"Level: {authority.authority_level.name}")
    print(f"Binding: {authority.is_binding}")
    print(f"Reasoning: {authority.reasoning}")