"""
# Script Name: enhanced_evidence_assessor.py
# Description: Enhanced Evidence Assessor that integrates CourtAuthorityHelper to add 0-6 star ratings to evidence entries based on caselaw authority.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Intake
#   - Group Tags: evidence-processing, authority-rating
Enhanced Evidence Assessor for LawyerFactory Intake Phase.

This enhanced version integrates the CourtAuthorityHelper to provide:
- Authority level assessment for all caselaw evidence
- 0-6 star rating system with color coding
- Binding vs persuasive authority determination
- Integration with jurisdiction context from intake form
- Enhanced evidence table with authority metadata
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from ...agents.research.court_authority_helper import CourtAuthorityHelper, JurisdictionContext
from .enhanced_intake_processor import EnhancedIntakeProcessor, EnhancedIntakeContext

logger = logging.getLogger(__name__)


@dataclass
class AuthorityRatedEvidence:
    """Evidence entry with authority rating"""
    original_evidence: Dict[str, Any]
    authority_assessment: Optional[Dict[str, Any]] = None
    star_rating: int = 0
    is_binding: bool = False
    reasoning: str = ""
    color_code: str = "gray"
    enhanced_relevance: float = 0.0


class EnhancedEvidenceAssessor:
    """
    Enhanced evidence assessor with court authority integration.

    This assessor extends basic evidence processing with:
    1. Caselaw authority assessment for all evidence entries
    2. 0-6 star rating system with binding/persuasive determination
    3. Color-coded evidence ratings (jade for binding, copper for persuasive)
    4. Integration with jurisdiction context from intake processing
    5. Enhanced evidence table with authority metadata
    """

    def __init__(self):
        self.authority_helper = CourtAuthorityHelper()
        self.jurisdiction_context: Optional[JurisdictionContext] = None

    def set_jurisdiction_context(self, context: JurisdictionContext):
        """
        Set jurisdiction context for authority assessment.

        Args:
            context: Jurisdiction context from intake processing
        """
        self.jurisdiction_context = context
        logger.info(f"Set jurisdiction context for evidence assessment: {context.primary_jurisdiction}")

    def process_evidence_table_with_authority(
        self,
        evidence_table_path: str,
        intake_context: Optional[EnhancedIntakeContext] = None
    ) -> Dict[str, Any]:
        """
        Process evidence table and add authority ratings to all entries.

        Args:
            evidence_table_path: Path to evidence_table.json
            intake_context: Enhanced intake context with jurisdiction information

        Returns:
            Processing results with statistics
        """

        try:
            # Load evidence table
            with open(evidence_table_path, 'r', encoding='utf-8') as f:
                evidence_data = json.load(f)

            evidence_entries = evidence_data.get('evidence_entries', [])

            if not evidence_entries:
                return {
                    'success': True,
                    'entries_processed': 0,
                    'authority_ratings_added': 0,
                    'message': 'No evidence entries found'
                }

            # Set jurisdiction context if intake context provided
            if intake_context:
                self.set_jurisdiction_context(intake_context.jurisdiction_context)

            # Process each evidence entry
            processed_entries = []
            authority_ratings_added = 0

            for entry in evidence_entries:
                enhanced_entry = self._process_evidence_entry(entry)
                processed_entries.append(enhanced_entry)

                if enhanced_entry.authority_assessment:
                    authority_ratings_added += 1

            # Update evidence table with enhanced entries
            for i, enhanced_entry in enumerate(processed_entries):
                if enhanced_entry.authority_assessment:
                    evidence_entries[i]['authority_rating'] = enhanced_entry.authority_assessment

            # Save updated evidence table
            with open(evidence_table_path, 'w', encoding='utf-8') as f:
                json.dump(evidence_data, f, indent=2, ensure_ascii=False)

            # Calculate statistics
            binding_count = sum(1 for e in processed_entries if e.is_binding and e.authority_assessment)
            persuasive_count = sum(1 for e in processed_entries if not e.is_binding and e.authority_assessment and e.star_rating > 0)
            no_authority_count = sum(1 for e in processed_entries if e.star_rating == 0 and e.authority_assessment)

            # Generate authority summary
            authority_summary = self._generate_authority_summary(
                processed_entries, binding_count, persuasive_count, no_authority_count
            )

            results = {
                'success': True,
                'entries_processed': len(processed_entries),
                'authority_ratings_added': authority_ratings_added,
                'binding_authority_count': binding_count,
                'persuasive_authority_count': persuasive_count,
                'no_authority_count': no_authority_count,
                'authority_summary': authority_summary,
                'jurisdiction_context': {
                    'primary_jurisdiction': self.jurisdiction_context.primary_jurisdiction if self.jurisdiction_context else 'unknown',
                    'court_type': self.jurisdiction_context.court_type if self.jurisdiction_context else 'unknown',
                    'event_location': self.jurisdiction_context.event_location if self.jurisdiction_context else 'unknown'
                }
            }

            logger.info(f"Enhanced evidence assessment completed: {authority_ratings_added} ratings added")
            return results

        except Exception as e:
            logger.error(f"Failed to process evidence table with authority: {e}")
            return {
                'success': False,
                'error': str(e),
                'entries_processed': 0,
                'authority_ratings_added': 0
            }

    def _process_evidence_entry(self, entry: Dict[str, Any]) -> AuthorityRatedEvidence:
        """
        Process a single evidence entry and assess its authority level.

        Args:
            entry: Evidence entry from evidence table

        Returns:
            Enhanced evidence entry with authority assessment
        """

        # Extract caselaw information from entry
        citation, court, jurisdiction = self._extract_caselaw_info(entry)

        # Create base enhanced entry
        enhanced_entry = AuthorityRatedEvidence(
            original_evidence=entry,
            star_rating=0,
            is_binding=False,
            reasoning="No caselaw detected in evidence",
            color_code="gray"
        )

        # If caselaw information found, assess authority
        if citation and court and jurisdiction:
            if self.jurisdiction_context:
                try:
                    # Assess authority using court authority helper
                    authority = self.authority_helper.assess_caselaw_authority(
                        case_citation=citation,
                        case_court=court,
                        case_jurisdiction=jurisdiction,
                        context=self.jurisdiction_context
                    )

                    # Create authority assessment dict
                    authority_assessment = {
                        'stars': authority.star_rating,
                        'level': authority.authority_level.name,
                        'is_binding': authority.is_binding,
                        'reasoning': authority.reasoning,
                        'color_code': self._get_color_code(authority.star_rating)
                    }

                    # Update enhanced entry
                    enhanced_entry.authority_assessment = authority_assessment
                    enhanced_entry.star_rating = authority.star_rating
                    enhanced_entry.is_binding = authority.is_binding
                    enhanced_entry.reasoning = authority.reasoning
                    enhanced_entry.color_code = authority_assessment['color_code']
                    enhanced_entry.enhanced_relevance = self._calculate_enhanced_relevance(
                        entry.get('relevance_score', 0.0),
                        authority.star_rating
                    )

                except Exception as e:
                    logger.warning(f"Failed to assess authority for {citation}: {e}")
                    enhanced_entry.reasoning = f"Authority assessment failed: {str(e)}"
            else:
                enhanced_entry.reasoning = "No jurisdiction context available for authority assessment"
        else:
            enhanced_entry.reasoning = "No caselaw citation found in evidence entry"

        return enhanced_entry

    def _extract_caselaw_info(self, entry: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract caselaw information from evidence entry.

        Args:
            entry: Evidence entry

        Returns:
            Tuple of (citation, court, jurisdiction)
        """

        # Look for citation in bluebook_citation field first
        citation = entry.get('bluebook_citation', '').strip()
        if citation:
            court, jurisdiction = self._parse_citation(citation)
            return citation, court, jurisdiction

        # Look for citation patterns in content
        content = entry.get('content', '')
        citation_match = self._find_citation_in_text(content)
        if citation_match:
            court, jurisdiction = self._parse_citation(citation_match)
            return citation_match, court, jurisdiction

        # Look for court information in content
        court_match = self._find_court_in_text(content)
        if court_match:
            return None, court_match, self._guess_jurisdiction_from_court(court_match)

        return None, None, None

    def _parse_citation(self, citation: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse citation to extract court and jurisdiction.

        Args:
            citation: Legal citation string

        Returns:
            Tuple of (court, jurisdiction)
        """

        citation_lower = citation.lower()

        # Federal courts
        if 'u.s.' in citation_lower or 's. ct.' in citation_lower:
            return "U.S. Supreme Court", "federal"
        elif 'f.' in citation_lower and 'circ' in citation_lower:
            return "U.S. Court of Appeals", "federal"
        elif 'f. supp.' in citation_lower:
            return "U.S. District Court", "federal"
        elif 'f.' in citation_lower and 'd' in citation_lower:
            return "U.S. District Court", "federal"

        # State courts - simplified parsing
        state_indicators = {
            'cal.': 'california',
            'n.y.': 'new_york',
            'tex.': 'texas',
            'fla.': 'florida',
            'ill.': 'illinois',
            'pa.': 'pennsylvania',
            'ohio': 'ohio',
            'ga.': 'georgia',
            'n.c.': 'north_carolina',
            'mich.': 'michigan',
            'n.j.': 'new_jersey',
            'va.': 'virginia',
            'wash.': 'washington',
            'ariz.': 'arizona',
            'mass.': 'massachusetts'
        }

        for indicator, state in state_indicators.items():
            if indicator in citation_lower:
                if 'supreme' in citation_lower:
                    return f"{state.title()} Supreme Court", state
                elif 'app.' in citation_lower or 'appeal' in citation_lower:
                    return f"{state.title()} Appellate Court", state
                else:
                    return f"{state.title()} Trial Court", state

        return None, None

    def _find_citation_in_text(self, text: str) -> Optional[str]:
        """
        Find legal citation patterns in text.

        Args:
            text: Text to search for citations

        Returns:
            First citation found or None
        """

        # Common citation patterns
        patterns = [
            r'\d+\s+U\.S\.\s+\d+',  # U.S. Supreme Court
            r'\d+\s+F\.\s+\d+',     # Federal courts
            r'\d+\s+F\.?\s+Supp\.?\s+\d+',  # Federal district
            r'\d+\s+[A-Z]{2,}\s+\d+',  # State courts
            r'\d+\s+[A-Z][a-z]+\.\s+\d+'  # State abbreviations
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()

        return None

    def _find_court_in_text(self, text: str) -> Optional[str]:
        """
        Find court names in text.

        Args:
            text: Text to search for court names

        Returns:
            Court name found or None
        """

        text_lower = text.lower()

        # Court name patterns
        court_patterns = [
            'supreme court',
            'court of appeals',
            'appellate court',
            'district court',
            'circuit court',
            'superior court',
            'trial court'
        ]

        for pattern in court_patterns:
            if pattern in text_lower:
                return pattern.title()

        return None

    def _guess_jurisdiction_from_court(self, court: str) -> str:
        """
        Guess jurisdiction from court name.

        Args:
            court: Court name

        Returns:
            Guessed jurisdiction
        """

        court_lower = court.lower()

        if any(federal_term in court_lower for federal_term in ['u.s.', 'federal', 'circuit']):
            return 'federal'
        else:
            # Default to unknown - would need more sophisticated logic
            return 'unknown'

    def _calculate_enhanced_relevance(self, base_relevance: float, authority_stars: int) -> float:
        """
        Calculate enhanced relevance score combining base relevance with authority.

        Args:
            base_relevance: Original relevance score (0-1)
            authority_stars: Authority level (0-6)

        Returns:
            Enhanced relevance score (0-1)
        """

        # Authority weight: higher authority increases relevance
        authority_weight = min(authority_stars / 6.0, 1.0)  # 0-1 scale

        # Combine base relevance with authority weight
        # Authority gets 40% weight, base relevance gets 60%
        enhanced_score = (base_relevance * 0.6) + (authority_weight * 0.4)

        return min(enhanced_score, 1.0)  # Cap at 1.0

    def _get_color_code(self, star_rating: int) -> str:
        """
        Get color code for star rating display.

        Args:
            star_rating: Star rating (0-6)

        Returns:
            Color code string
        """
        if star_rating == 0:
            return "gray"      # No authority
        elif star_rating <= 3:
            return "copper"    # Persuasive (least to most)
        else:
            return "jade"      # Binding (least to most)

    def _generate_authority_summary(
        self,
        processed_entries: List[AuthorityRatedEvidence],
        binding_count: int,
        persuasive_count: int,
        no_authority_count: int
    ) -> str:
        """
        Generate a summary of authority assessment results.

        Args:
            processed_entries: List of processed evidence entries
            binding_count: Number of binding authority entries
            persuasive_count: Number of persuasive authority entries
            no_authority_count: Number of entries with no authority

        Returns:
            Formatted authority summary
        """

        total_entries = len(processed_entries)

        summary = "=== EVIDENCE AUTHORITY ASSESSMENT SUMMARY ===\n\n"
        summary += f"Total Evidence Entries: {total_entries}\n"
        summary += f"Binding Authority: {binding_count} ({binding_count/total_entries*100:.1f}%)\n"
        summary += f"Persuasive Authority: {persuasive_count} ({persuasive_count/total_entries*100:.1f}%)\n"
        summary += f"No Authority: {no_authority_count} ({no_authority_count/total_entries*100:.1f}%)\n\n"

        if binding_count > 0:
            summary += "🔴 BINDING AUTHORITY EVIDENCE:\n"
            binding_entries = [e for e in processed_entries if e.is_binding and e.authority_assessment]
            for entry in binding_entries[:3]:  # Show top 3
                original = entry.original_evidence
                summary += f"  • {original.get('source_document', 'Unknown')}\n"
                summary += f"    Stars: {'★' * entry.star_rating} - {entry.reasoning}\n"
            if binding_count > 3:
                summary += f"    ... and {binding_count - 3} more\n"
            summary += "\n"

        if persuasive_count > 0:
            summary += "🟠 PERSUASIVE AUTHORITY EVIDENCE:\n"
            persuasive_entries = [e for e in processed_entries if not e.is_binding and e.authority_assessment and e.star_rating > 0]
            for entry in persuasive_entries[:3]:  # Show top 3
                original = entry.original_evidence
                summary += f"  • {original.get('source_document', 'Unknown')}\n"
                summary += f"    Stars: {'★' * entry.star_rating} - {entry.reasoning}\n"
            if persuasive_count > 3:
                summary += f"    ... and {persuasive_count - 3} more\n"
            summary += "\n"

        return summary


# Integration function for the intake phase
def assess_evidence_with_authority_enhancement(
    evidence_table_path: str,
    intake_context_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Assess evidence table with court authority enhancement.

    Args:
        evidence_table_path: Path to evidence_table.json
        intake_context_path: Optional path to enhanced intake context

    Returns:
        Assessment results with authority ratings
    """

    assessor = EnhancedEvidenceAssessor()

    # Load intake context if provided
    intake_context = None
    if intake_context_path and Path(intake_context_path).exists():
        try:
            from ...phases.intake.enhanced_intake_processor import EnhancedIntakeProcessor
            processor = EnhancedIntakeProcessor()
            intake_context = processor.load_enhanced_context(intake_context_path)
        except Exception as e:
            logger.warning(f"Failed to load intake context: {e}")

    # Process evidence table with authority assessment
    results = assessor.process_evidence_table_with_authority(
        evidence_table_path=evidence_table_path,
        intake_context=intake_context
    )

    return results


# Example usage and testing
if __name__ == "__main__":
    # Example evidence table processing
    sample_evidence_table = {
        "evidence_entries": [
            {
                "evidence_id": "sample_1",
                "source_document": "Legal Brief",
                "content": "The court in Smith v. Jones, 123 U.S. 456 (2023) held that...",
                "bluebook_citation": "Smith v. Jones, 123 U.S. 456 (2023)",
                "relevance_score": 0.8
            },
            {
                "evidence_id": "sample_2",
                "source_document": "Case Summary",
                "content": "In California Supreme Court case Johnson v. State, 45 Cal.4th 123 (2022)...",
                "bluebook_citation": "Johnson v. State, 45 Cal.4th 123 (2022)",
                "relevance_score": 0.7
            },
            {
                "evidence_id": "sample_3",
                "source_document": "Research Notes",
                "content": "General information about contract law principles",
                "relevance_score": 0.3
            }
        ]
    }

    # Save sample evidence table
    sample_path = "sample_evidence_table.json"
    with open(sample_path, 'w') as f:
        json.dump(sample_evidence_table, f, indent=2)

    # Create sample jurisdiction context
    from ...agents.research.court_authority_helper import JurisdictionContext, LegalQuestionType

    sample_context = JurisdictionContext(
        primary_jurisdiction="federal",
        court_type="district",
        event_location="California",
        question_type=LegalQuestionType.SUBSTANTIVE_FEDERAL_DIVERSITY
    )

    # Process with authority enhancement
    results = assess_evidence_with_authority_enhancement(
        evidence_table_path=sample_path,
        intake_context_path=None  # Would use real context file
    )

    print("=== ENHANCED EVIDENCE ASSESSMENT RESULTS ===")
    print(f"Success: {results['success']}")
    print(f"Entries Processed: {results['entries_processed']}")
    print(f"Authority Ratings Added: {results['authority_ratings_added']}")
    print(f"Binding Authority: {results['binding_authority_count']}")
    print(f"Persuasive Authority: {results['persuasive_authority_count']}")
    print(f"No Authority: {results['no_authority_count']}")

    print("
=== AUTHORITY SUMMARY ===")
    print(results['authority_summary'])

    # Load and display updated evidence table
    with open(sample_path, 'r') as f:
        updated_table = json.load(f)

    print("\n=== UPDATED EVIDENCE TABLE ===")
    for entry in updated_table['evidence_entries']:
        print(f"Document: {entry['source_document']}")
        if 'authority_rating' in entry:
            rating = entry['authority_rating']
            print(f"  Authority: {'★' * rating['stars']} ({rating['level']})")
            print(f"  Color: {rating['color_code']}")
            print(f"  Reasoning: {rating['reasoning']}")
        else:
            print("  No authority rating")
        print()