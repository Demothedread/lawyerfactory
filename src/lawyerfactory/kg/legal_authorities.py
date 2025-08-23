"""
# Script Name: legal_authorities.py
# Description: Legal Authority Management System for LawyerFactory  Manages binding vs persuasive authority based on jurisdiction and court hierarchy. Implements authority precedence rules and citation validation.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Research
#   - Group Tags: knowledge-graph
Legal Authority Management System for LawyerFactory

Manages binding vs persuasive authority based on jurisdiction and court hierarchy.
Implements authority precedence rules and citation validation.
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AuthorityType(Enum):
    """Types of legal authority"""
    BINDING = "binding"
    PERSUASIVE = "persuasive"
    OBSOLETE = "obsolete"
    QUESTIONABLE = "questionable"


class CourtLevel(Enum):
    """Court hierarchy levels"""
    SUPREME_COURT = "supreme_court"
    APPELLATE = "appellate"
    DISTRICT = "district"
    STATE_SUPREME = "state_supreme"
    STATE_APPELLATE = "state_appellate"
    STATE_TRIAL = "state_trial"


@dataclass
class LegalAuthority:
    """Represents a legal authority with jurisdiction and precedence information"""
    title: str
    section: str
    court: str
    jurisdiction: str
    court_level: CourtLevel
    decision_date: str
    authority_type: AuthorityType
    tags: List[str] = field(default_factory=list)
    content: str = ""
    superseded_by: Optional[str] = None
    superseded_date: Optional[str] = None

    def is_binding_in_jurisdiction(self, target_jurisdiction: str) -> bool:
        """Check if this authority is binding in the target jurisdiction"""
        if self.authority_type == AuthorityType.OBSOLETE:
            return False

        if self.authority_type == AuthorityType.QUESTIONABLE:
            return False

        # Supreme Court decisions are binding nationwide
        if self.court_level == CourtLevel.SUPREME_COURT:
            return True

        # Federal appellate decisions are binding in their circuits
        if "federal" in self.jurisdiction.lower():
            if "federal" in target_jurisdiction.lower():
                return True

        # State supreme courts are binding statewide
        if self.court_level == CourtLevel.STATE_SUPREME:
            if self.jurisdiction.lower() in target_jurisdiction.lower():
                return True

        # State appellate decisions are binding in their districts
        if self.court_level == CourtLevel.STATE_APPELLATE:
            if self.jurisdiction.lower() in target_jurisdiction.lower():
                return True

        return False

    def get_precedence_score(self, target_jurisdiction: str) -> float:
        """Get precedence score for this authority in target jurisdiction"""
        if self.authority_type == AuthorityType.OBSOLETE:
            return 0.0

        if self.authority_type == AuthorityType.QUESTIONABLE:
            return 0.2

        if self.is_binding_in_jurisdiction(target_jurisdiction):
            # Binding authorities get high scores
            if self.court_level == CourtLevel.SUPREME_COURT:
                return 1.0
            elif self.court_level == CourtLevel.STATE_SUPREME:
                return 0.95
            elif self.court_level == CourtLevel.APPELLATE:
                return 0.9
            else:
                return 0.8
        else:
            # Persuasive authorities get lower scores
            if self.court_level == CourtLevel.SUPREME_COURT:
                return 0.7
            elif self.court_level == CourtLevel.STATE_SUPREME:
                return 0.6
            else:
                return 0.4


class LegalAuthorityManager:
    """Manages legal authorities and their precedence"""

    def __init__(self, data_path: str = "data/kg/legal_authorities.json"):
        self.data_path = data_path
        self.authorities: Dict[str, LegalAuthority] = {}
        self._load_authorities()

    def _load_authorities(self):
        """Load authorities from data file"""
        try:
            with open(self.data_path, 'r') as f:
                data = json.load(f)
                for item in data.get("authorities", []):
                    authority = LegalAuthority(**item)
                    self.authorities[authority.section] = authority
            logger.info(f"Loaded {len(self.authorities)} legal authorities")
        except FileNotFoundError:
            logger.warning(f"Legal authorities file not found: {self.data_path}")
            self._create_default_authorities()
        except Exception as e:
            logger.error(f"Error loading legal authorities: {e}")
            self.authorities = {}

    def _create_default_authorities(self):
        """Create default authorities for common legal issues"""
        default_authorities = [
            LegalAuthority(
                title="Smith v. Johnson",
                section="123 F. Supp. 456",
                court="U.S. District Court",
                jurisdiction="federal",
                court_level=CourtLevel.DISTRICT,
                decision_date="2023-01-15",
                authority_type=AuthorityType.PERSUASIVE,
                tags=["contract", "breach"],
                content="District court held that email communications can constitute binding contract"
            ),
            LegalAuthority(
                title="California Supreme Court Contract Case",
                section="45 Cal.4th 789",
                court="California Supreme Court",
                jurisdiction="california",
                court_level=CourtLevel.STATE_SUPREME,
                decision_date="2022-06-10",
                authority_type=AuthorityType.BINDING,
                tags=["contract", "consideration"],
                content="California Supreme Court established rules for digital contract formation"
            ),
            LegalAuthority(
                title="Federal Circuit Authority",
                section="789 F.3d 123",
                court="U.S. Court of Appeals",
                jurisdiction="federal_9th_circuit",
                court_level=CourtLevel.APPELLATE,
                decision_date="2021-03-20",
                authority_type=AuthorityType.BINDING,
                tags=["patent", "infringement"],
                content="Ninth Circuit clarified standards for patent infringement claims"
            )
        ]

        for authority in default_authorities:
            self.authorities[authority.section] = authority

        self._save_authorities()
        logger.info("Created default legal authorities")

    def _save_authorities(self):
        """Save authorities to data file"""
        try:
            data = {
                "authorities": [authority.__dict__ for authority in self.authorities.values()],
                "last_updated": datetime.now().isoformat()
            }
            with open(self.data_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving legal authorities: {e}")

    def search_authorities(self, query: str, limit: int = 10) -> List[LegalAuthority]:
        """Search for authorities matching the query"""
        results = []
        query_lower = query.lower()

        for authority in self.authorities.values():
            # Search in title, content, and tags
            searchable_text = f"{authority.title} {authority.content} {' '.join(authority.tags)}".lower()

            if query_lower in searchable_text:
                results.append(authority)

        # Sort by relevance (simple keyword matching for now)
        results.sort(key=lambda x: len([word for word in query_lower.split() if word in searchable_text]), reverse=True)

        return results[:limit]

    def get_authority_by_citation(self, citation: str) -> Optional[LegalAuthority]:
        """Get authority by citation"""
        return self.authorities.get(citation)

    def validate_citation_for_jurisdiction(self, citation: str, target_jurisdiction: str) -> Dict[str, Any]:
        """Validate if a citation is appropriate for the target jurisdiction"""
        authority = self.get_authority_by_citation(citation)

        if not authority:
            return {
                "valid": False,
                "reason": "Citation not found in authority database",
                "suggested_alternatives": []
            }

        is_binding = authority.is_binding_in_jurisdiction(target_jurisdiction)
        precedence_score = authority.get_precedence_score(target_jurisdiction)

        result = {
            "valid": is_binding,
            "authority_type": authority.authority_type.value,
            "precedence_score": precedence_score,
            "court_level": authority.court_level.value,
            "reason": ""
        }

        if authority.authority_type == AuthorityType.OBSOLETE:
            result["reason"] = f"This authority was superseded by {authority.superseded_by}"
            result["suggested_alternatives"] = self._find_superseding_authority(authority)
        elif not is_binding:
            result["reason"] = f"This {authority.court_level.value} decision is not binding in {target_jurisdiction}"
            result["suggested_alternatives"] = self._find_binding_authorities(target_jurisdiction, authority.tags)

        return result

    def _find_superseding_authority(self, obsolete_authority: LegalAuthority) -> List[str]:
        """Find authorities that superseded the given obsolete authority"""
        if obsolete_authority.superseded_by:
            superseding = self.get_authority_by_citation(obsolete_authority.superseded_by)
            if superseding:
                return [superseding.section]
        return []

    def _find_binding_authorities(self, jurisdiction: str, tags: List[str]) -> List[str]:
        """Find binding authorities in the jurisdiction with matching tags"""
        binding_authorities = []

        for authority in self.authorities.values():
            if (authority.is_binding_in_jurisdiction(jurisdiction) and
                any(tag in authority.tags for tag in tags)):
                binding_authorities.append(authority.section)

        return binding_authorities[:3]  # Return top 3

    def add_authority(self, authority: LegalAuthority):
        """Add a new legal authority"""
        self.authorities[authority.section] = authority
        self._save_authorities()
        logger.info(f"Added new authority: {authority.section}")

    def update_authority_status(self, citation: str, new_status: AuthorityType, superseded_by: Optional[str] = None):
        """Update the status of an existing authority"""
        if citation in self.authorities:
            self.authorities[citation].authority_type = new_status
            if superseded_by:
                self.authorities[citation].superseded_by = superseded_by
                self.authorities[citation].superseded_date = datetime.now().isoformat()
            self._save_authorities()
            logger.info(f"Updated authority status: {citation} -> {new_status.value}")


class AuthorityCitationManager:
    """Manages citation formatting and validation for different authority types"""

    def __init__(self, authority_manager: LegalAuthorityManager):
        self.authority_manager = authority_manager

    def format_citation(self, citation: str, jurisdiction: str) -> str:
        """Format citation with appropriate signals based on jurisdiction"""
        validation = self.authority_manager.validate_citation_for_jurisdiction(citation, jurisdiction)

        if validation["valid"]:
            return citation  # No signal needed for binding authority
        else:
            # Add persuasive authority signals
            if validation["authority_type"] == "persuasive":
                return f"{citation} (persuasive)"
            elif validation["authority_type"] == "obsolete":
                return f"{citation} (superseded)"
            else:
                return f"{citation} (not binding)"

    def generate_citation_table(self, citations: List[str], jurisdiction: str) -> str:
        """Generate a formatted citation table for a document"""
        table_lines = []
        table_lines.append("TABLE OF AUTHORITIES")
        table_lines.append("=" * 50)

        for citation in citations:
            authority = self.authority_manager.get_authority_by_citation(citation)
            if authority:
                formatted_citation = self.format_citation(citation, jurisdiction)
                table_lines.append(f"{formatted_citation:<40} {authority.title}")
            else:
                table_lines.append(f"{citation:<40} (Authority not found)")

        return "\n".join(table_lines)

    def validate_document_citations(self, document_text: str, jurisdiction: str) -> Dict[str, Any]:
        """Validate all citations in a document for the given jurisdiction"""
        # Simple regex to find citations (this would need to be more sophisticated)
        citation_pattern = r'\d+\s+[A-Za-z\.]+\s+\d+'
        citations = re.findall(citation_pattern, document_text)

        validation_results = {}
        issues = []

        for citation in citations:
            validation = self.authority_manager.validate_citation_for_jurisdiction(citation, jurisdiction)
            validation_results[citation] = validation

            if not validation["valid"]:
                issues.append({
                    "citation": citation,
                    "issue": validation["reason"],
                    "suggested_alternatives": validation.get("suggested_alternatives", [])
                })

        return {
            "total_citations": len(citations),
            "validation_results": validation_results,
            "issues": issues,
            "recommendations": self._generate_recommendations(issues)
        }

    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on citation issues"""
        recommendations = []

        if issues:
            recommendations.append(f"Found {len(issues)} citation issues that need attention")

            obsolete_count = sum(1 for issue in issues if "superseded" in issue["issue"].lower())
            if obsolete_count > 0:
                recommendations.append(f"Update {obsolete_count} obsolete citations with current authority")

            non_binding_count = sum(1 for issue in issues if "not binding" in issue["issue"].lower())
            if non_binding_count > 0:
                recommendations.append(f"Replace {non_binding_count} non-binding citations with jurisdiction-appropriate authority")

        return recommendations