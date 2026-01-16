"""
# Script Name: jurisdiction.py
# Description: Jurisdiction Management System for Claims Matrix Manages jurisdiction selection, legal authority hierarchy, and federal preemption resolution
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Research
#   - Group Tags: knowledge-graph
Jurisdiction Management System for Claims Matrix
Manages jurisdiction selection, legal authority hierarchy, and federal preemption resolution
"""

from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional

from lawyerfactory.kg.graph_api import EnhancedKnowledgeGraph, JurisdictionAuthority

logger = logging.getLogger(__name__)


@dataclass
class JurisdictionConfig:
    """Configuration for a specific jurisdiction"""

    jurisdiction_code: str
    jurisdiction_name: str
    jurisdiction_type: str  # federal, state, local
    court_levels: List[str] = field(default_factory=list)
    federal_preemption_areas: List[str] = field(default_factory=list)
    citation_format: str = "default"
    active: bool = True


class JurisdictionManager:
    """Manages jurisdiction selection and legal authority hierarchy for Claims Matrix"""

    def __init__(self, enhanced_kg: EnhancedKnowledgeGraph):
        self.kg = enhanced_kg
        self.jurisdictions = self._initialize_jurisdictions()
        self.current_jurisdiction = None
        self.authority_hierarchy = self._initialize_authority_hierarchy()

    def _initialize_jurisdictions(self) -> Dict[str, JurisdictionConfig]:
        """Initialize supported jurisdictions"""
        jurisdictions = {
            "ca_state": JurisdictionConfig(
                jurisdiction_code="ca_state",
                jurisdiction_name="California State Court",
                jurisdiction_type="state",
                court_levels=["superior", "appellate", "supreme"],
                citation_format="california",
            ),
            "federal_district": JurisdictionConfig(
                jurisdiction_code="federal_district",
                jurisdiction_name="Federal District Court",
                jurisdiction_type="federal",
                court_levels=["district", "circuit", "supreme"],
                federal_preemption_areas=[
                    "interstate_commerce",
                    "patent",
                    "copyright",
                    "securities",
                ],
                citation_format="federal",
            ),
            "ny_state": JurisdictionConfig(
                jurisdiction_code="ny_state",
                jurisdiction_name="New York State Court",
                jurisdiction_type="state",
                court_levels=["supreme", "appellate", "appeals"],
                citation_format="new_york",
            ),
            "federal_bankruptcy": JurisdictionConfig(
                jurisdiction_code="federal_bankruptcy",
                jurisdiction_name="Federal Bankruptcy Court",
                jurisdiction_type="federal",
                court_levels=["bankruptcy", "district", "circuit"],
                federal_preemption_areas=["bankruptcy"],
                citation_format="federal",
            ),
        }

        logger.info(f"Initialized {len(jurisdictions)} jurisdictions")
        return jurisdictions

    def _initialize_authority_hierarchy(self) -> Dict[str, Dict[str, int]]:
        """Initialize legal authority precedence hierarchy by jurisdiction"""
        return {
            "ca_state": {
                "us_constitution": 1,
                "federal_statute": 2,
                "federal_regulation": 3,
                "ca_constitution": 4,
                "ca_statute": 5,
                "ca_regulation": 6,
                "us_supreme_court": 7,
                "ninth_circuit": 8,
                "ca_supreme_court": 9,
                "ca_appellate": 10,
                "federal_district": 11,
                "ca_superior": 12,
            },
            "federal_district": {
                "us_constitution": 1,
                "federal_statute": 2,
                "federal_regulation": 3,
                "us_supreme_court": 4,
                "circuit_court": 5,
                "federal_district": 6,
                "state_authority": 7,  # Only when no federal preemption
            },
            "ny_state": {
                "us_constitution": 1,
                "federal_statute": 2,
                "federal_regulation": 3,
                "ny_constitution": 4,
                "ny_statute": 5,
                "ny_regulation": 6,
                "us_supreme_court": 7,
                "second_circuit": 8,
                "ny_appeals": 9,
                "ny_appellate": 10,
                "federal_district": 11,
                "ny_supreme": 12,
            },
        }

    def get_available_jurisdictions(self) -> List[Dict[str, Any]]:
        """Get list of available jurisdictions for dropdown selection"""
        return [
            {
                "code": config.jurisdiction_code,
                "name": config.jurisdiction_name,
                "type": config.jurisdiction_type,
                "active": config.active,
                "court_levels": config.court_levels,
            }
            for config in self.jurisdictions.values()
            if config.active
        ]

    def select_jurisdiction(self, jurisdiction_code: str) -> bool:
        """Select current jurisdiction for claims matrix analysis"""
        if jurisdiction_code not in self.jurisdictions:
            logger.error(f"Invalid jurisdiction code: {jurisdiction_code}")
            return False

        if not self.jurisdictions[jurisdiction_code].active:
            logger.error(f"Jurisdiction not active: {jurisdiction_code}")
            return False

        self.current_jurisdiction = jurisdiction_code
        logger.info(
            f"Selected jurisdiction: {self.jurisdictions[jurisdiction_code].jurisdiction_name}"
        )
        return True

    def get_current_jurisdiction(self) -> Optional[JurisdictionConfig]:
        """Get currently selected jurisdiction configuration"""
        if not self.current_jurisdiction:
            return None
        return self.jurisdictions.get(self.current_jurisdiction)

    def add_jurisdiction_authority(self, authority: JurisdictionAuthority) -> int:
        """Add a legal authority to the jurisdiction"""
        if not self._validate_jurisdiction(authority.jurisdiction):
            raise ValueError(f"Invalid jurisdiction: {authority.jurisdiction}")

        try:
            cursor = self.kg.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO jurisdiction_authorities
                (jurisdiction, authority_type, authority_name, authority_citation,
                 precedence_level, federal_preemption_scope, effective_date, superseded_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    authority.jurisdiction,
                    authority.authority_type,
                    authority.authority_name,
                    authority.authority_citation,
                    authority.precedence_level,
                    authority.federal_preemption_scope,
                    authority.effective_date,
                    authority.superseded_date,
                ),
            )

            authority_id = cursor.lastrowid
            cursor.close()
            self.kg.conn.commit()

            logger.info(
                f"Added jurisdiction authority: {authority.authority_name} for {authority.jurisdiction}"
            )
            return authority_id

        except Exception as e:
            logger.exception(f"Failed to add jurisdiction authority: {e}")
            raise

    def get_jurisdiction_authorities(
        self, jurisdiction: str, authority_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get legal authorities for a specific jurisdiction"""
        if not self._validate_jurisdiction(jurisdiction):
            return []

        try:
            query = """
                SELECT id, jurisdiction, authority_type, authority_name, authority_citation,
                       precedence_level, federal_preemption_scope, effective_date,
                       superseded_date, created_at
                FROM jurisdiction_authorities
                WHERE jurisdiction = ? 
                AND (superseded_date IS NULL OR superseded_date > date('now'))
            """
            params = [jurisdiction]

            if authority_type:
                query += " AND authority_type = ?"
                params.append(authority_type)

            query += " ORDER BY precedence_level ASC"

            rows = self.kg._fetchall(query, tuple(params))

            authorities = []
            for row in rows:
                authorities.append(
                    {
                        "id": row[0],
                        "jurisdiction": row[1],
                        "authority_type": row[2],
                        "authority_name": row[3],
                        "authority_citation": row[4],
                        "precedence_level": row[5],
                        "federal_preemption_scope": row[6],
                        "effective_date": row[7],
                        "superseded_date": row[8],
                        "created_at": row[9],
                    }
                )

            return authorities

        except Exception as e:
            logger.exception(
                f"Failed to get jurisdiction authorities for {jurisdiction}: {e}"
            )
            return []

    def resolve_authority_conflict(
        self, authorities: List[Dict[str, Any]], legal_area: str
    ) -> Dict[str, Any]:
        """Resolve conflicts between multiple legal authorities"""
        if not authorities:
            return {"error": "No authorities provided"}

        try:
            # Check for federal preemption
            federal_authorities = [
                a for a in authorities if a["jurisdiction"].startswith("federal")
            ]
            state_authorities = [
                a for a in authorities if not a["jurisdiction"].startswith("federal")
            ]

            # Determine if federal law preempts
            preempted = False
            controlling_authority = None

            for fed_auth in federal_authorities:
                preemption_scope = fed_auth.get("federal_preemption_scope", "none")
                if preemption_scope == "complete":
                    preempted = True
                    controlling_authority = fed_auth
                    break
                elif preemption_scope == "partial" and legal_area in fed_auth.get(
                    "preemption_areas", []
                ):
                    preempted = True
                    controlling_authority = fed_auth
                    break

            # If not preempted, use precedence level
            if not preempted:
                # Sort by precedence level (lower number = higher precedence)
                sorted_authorities = sorted(
                    authorities, key=lambda x: x["precedence_level"]
                )
                controlling_authority = sorted_authorities[0]

            return {
                "controlling_authority": controlling_authority,
                "federal_preemption": preempted,
                "preemption_reason": (
                    f"Federal law preempts in area: {legal_area}" if preempted else None
                ),
                "alternative_authorities": [
                    a for a in authorities if a != controlling_authority
                ],
                "resolution_method": (
                    "federal_preemption" if preempted else "precedence_hierarchy"
                ),
            }

        except Exception as e:
            logger.exception(f"Failed to resolve authority conflict: {e}")
            return {"error": str(e)}

    def get_jurisdiction_causes_of_action(
        self, jurisdiction: str
    ) -> List[Dict[str, Any]]:
        """Get all causes of action available for a jurisdiction"""
        if not self._validate_jurisdiction(jurisdiction):
            return []

        return self.kg.get_causes_of_action_by_jurisdiction(jurisdiction)

    def validate_cause_for_jurisdiction(
        self, cause_name: str, jurisdiction: str
    ) -> Dict[str, Any]:
        """Validate if a cause of action is available in the specified jurisdiction"""
        try:
            causes = self.get_jurisdiction_causes_of_action(jurisdiction)
            matching_cause = next(
                (c for c in causes if c["cause_name"] == cause_name), None
            )

            if not matching_cause:
                return {
                    "valid": False,
                    "reason": f"Cause of action '{cause_name}' not available in {jurisdiction}",
                    "suggested_alternatives": self._suggest_alternative_causes(
                        cause_name, jurisdiction
                    ),
                }

            # Check for federal preemption
            if matching_cause.get("federal_preempted"):
                fed_jurisdiction = "federal_district"
                if fed_jurisdiction in self.jurisdictions:
                    return {
                        "valid": False,
                        "reason": f"Federal law preempts '{cause_name}' - must use federal jurisdiction",
                        "required_jurisdiction": fed_jurisdiction,
                        "federal_preemption": True,
                    }

            return {
                "valid": True,
                "cause": matching_cause,
                "jurisdiction": jurisdiction,
            }

        except Exception as e:
            logger.exception(f"Failed to validate cause for jurisdiction: {e}")
            return {"valid": False, "error": str(e)}

    def get_jurisdiction_citation_format(self, jurisdiction: str) -> str:
        """Get citation format for the jurisdiction"""
        if jurisdiction not in self.jurisdictions:
            return "default"
        return self.jurisdictions[jurisdiction].citation_format

    def _validate_jurisdiction(self, jurisdiction: str) -> bool:
        """Validate jurisdiction code"""
        return (
            jurisdiction in self.jurisdictions
            and self.jurisdictions[jurisdiction].active
        )

    def _suggest_alternative_causes(
        self, cause_name: str, jurisdiction: str
    ) -> List[str]:
        """Suggest alternative causes of action for the jurisdiction"""
        try:
            causes = self.get_jurisdiction_causes_of_action(jurisdiction)
            # Simple text similarity matching (could be enhanced with NLP)
            alternatives = []
            cause_lower = cause_name.lower()

            for cause in causes:
                if any(
                    word in cause["cause_name"].lower() for word in cause_lower.split()
                ):
                    alternatives.append(cause["cause_name"])

            return alternatives[:3]  # Return top 3 matches

        except Exception:
            return []

    def is_jurisdiction_compatible(
        self, result_jurisdiction: str, request_jurisdiction: str
    ) -> bool:
        """Check if result jurisdiction is compatible with request jurisdiction"""
        if result_jurisdiction == request_jurisdiction:
            return True

        # Federal law applies to all jurisdictions
        if result_jurisdiction == "federal":
            return True

        # Check if both are state courts (may have persuasive authority)
        result_config = self.jurisdictions.get(result_jurisdiction)
        request_config = self.jurisdictions.get(request_jurisdiction)

        if result_config and request_config:
            if (
                result_config.jurisdiction_type == "state"
                and request_config.jurisdiction_type == "state"
            ):
                return True  # State courts can cite other state courts as persuasive

        return False

    def check_federal_preemption(self, jurisdiction: str, cause_of_action: str) -> bool:
        """Check if federal law preempts state law for the given cause of action"""
        try:
            # Federal preemption areas
            complete_preemption_areas = [
                "patent",
                "copyright",
                "trademark",
                "immigration",
                "bankruptcy",
                "maritime",
                "foreign_commerce",
                "interstate_commerce",
            ]

            partial_preemption_areas = [
                "employment",
                "environmental",
                "securities",
                "antitrust",
                "consumer_protection",
                "civil_rights",
                "labor",
            ]

            cause_lower = cause_of_action.lower()

            # Check for complete preemption
            for area in complete_preemption_areas:
                if area in cause_lower:
                    return True

            # Check for partial preemption (context-dependent)
            for area in partial_preemption_areas:
                if area in cause_lower:
                    # Would need more sophisticated analysis in practice
                    return jurisdiction == "federal"

            return False

        except Exception as e:
            logger.error(f"Failed to check federal preemption: {e}")
            return False

    def get_jurisdiction_statistics(self) -> Dict[str, Any]:
        """Get statistics for all jurisdictions"""
        try:
            stats = {}
            for jurisdiction_code, config in self.jurisdictions.items():
                causes = self.get_jurisdiction_causes_of_action(jurisdiction_code)
                authorities = self.get_jurisdiction_authorities(jurisdiction_code)

                stats[jurisdiction_code] = {
                    "name": config.jurisdiction_name,
                    "type": config.jurisdiction_type,
                    "active": config.active,
                    "causes_of_action_count": len(causes),
                    "authorities_count": len(authorities),
                    "court_levels": len(config.court_levels),
                    "federal_preemption_areas": len(config.federal_preemption_areas),
                }

            return stats

        except Exception as e:
            logger.exception(f"Failed to get jurisdiction statistics: {e}")
            return {}


if __name__ == "__main__":
    # Test jurisdiction manager
    import sys

    logging.basicConfig(level=logging.INFO)

    from lawyerfactory.kg.graph_api import EnhancedKnowledgeGraph

    kg = EnhancedKnowledgeGraph("test_jurisdiction.db")
    manager = JurisdictionManager(kg)

    try:
        # Test jurisdiction selection
        jurisdictions = manager.get_available_jurisdictions()
        print(f"Available jurisdictions: {len(jurisdictions)}")

        # Select California state jurisdiction
        if manager.select_jurisdiction("ca_state"):
            current = manager.get_current_jurisdiction()
            print(f"Selected: {current.jurisdiction_name}")

            # Add test authority
            authority = JurisdictionAuthority(
                jurisdiction="ca_state",
                authority_type="statute",
                authority_name="California Civil Code Section 1714",
                authority_citation="Cal. Civ. Code § 1714",
                precedence_level=5,
            )

            auth_id = manager.add_jurisdiction_authority(authority)
            print(f"Added authority: {auth_id}")

            # Get authorities
            authorities = manager.get_jurisdiction_authorities("ca_state")
            print(f"Found {len(authorities)} authorities")

            # Test statistics
            stats = manager.get_jurisdiction_statistics()
            print(f"Jurisdiction statistics: {stats}")

    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    finally:
        kg.close()
