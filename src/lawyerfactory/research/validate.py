"""
# Script Name: validate.py
# Description: Legal Authority Validation System for Claims Matrix Phase 3.2 Validates legal authorities, enforces jurisdiction hierarchy, and resolves conflicts
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Research
#   - Group Tags: legal-research
Legal Authority Validation System for Claims Matrix Phase 3.2
Validates legal authorities, enforces jurisdiction hierarchy, and resolves conflicts
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import re
from typing import Any, Dict, List, Optional

from enhanced_knowledge_graph import EnhancedKnowledgeGraph
from legal_research_integration import AuthorityLevel, LegalCitation

from src.lawyerfactory.knowledge_graph.core.jurisdiction_manager import (
    JurisdictionManager,
)

logger = logging.getLogger(__name__)


class CitationCompliance(Enum):
    """Citation format compliance levels"""

    BLUEBOOK_COMPLIANT = "bluebook_compliant"
    ACCEPTABLE = "acceptable"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"


@dataclass
class AuthorityConflict:
    """Represents a conflict between legal authorities"""

    conflict_id: str
    primary_authority: LegalCitation
    conflicting_authority: LegalCitation
    conflict_type: str  # jurisdictional, temporal, substantive
    severity: str  # critical, high, medium, low
    resolution_strategy: str
    resolved_authority: Optional[LegalCitation] = None
    resolution_confidence: float = 0.0
    attorney_review_required: bool = True
    notes: str = ""


@dataclass
class FederalPreemptionAnalysis:
    """Analysis of federal preemption issues"""

    preemption_exists: bool
    preemption_type: str  # complete, partial, none
    federal_authority: Optional[LegalCitation] = None
    state_authority: Optional[LegalCitation] = None
    analysis_notes: str = ""
    confidence_score: float = 0.0


@dataclass
class BluebookValidation:
    """Validation result for Bluebook citation format"""

    is_compliant: bool
    compliance_level: CitationCompliance
    detected_format: str
    suggested_format: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class LegalAuthorityValidator:
    """Validates legal authorities and resolves jurisdiction conflicts"""

    def __init__(
        self,
        enhanced_kg: EnhancedKnowledgeGraph,
        jurisdiction_manager: JurisdictionManager,
    ):
        self.kg = enhanced_kg
        self.jurisdiction_manager = jurisdiction_manager

        # Authority hierarchy configuration
        self.authority_hierarchy = {
            AuthorityLevel.SUPREME_COURT: 1,
            AuthorityLevel.APPELLATE_COURT: 2,
            AuthorityLevel.TRIAL_COURT: 3,
            AuthorityLevel.ADMINISTRATIVE: 4,
            AuthorityLevel.SECONDARY_SOURCE: 5,
        }

        # Federal preemption areas
        self.federal_preemption_areas = {
            "complete": [
                "immigration",
                "bankruptcy",
                "patent",
                "copyright",
                "maritime",
                "foreign_commerce",
                "interstate_commerce",
            ],
            "partial": [
                "employment",
                "environmental",
                "consumer_protection",
                "securities",
                "antitrust",
                "civil_rights",
            ],
        }

        # Bluebook citation patterns
        self.bluebook_patterns = self._initialize_bluebook_patterns()

        logger.info("Legal Authority Validator initialized")

    def _initialize_bluebook_patterns(self) -> Dict[str, List[str]]:
        """Initialize Bluebook citation format patterns"""
        return {
            "case": [
                r"^\d+\s+[A-Z][a-z]+\.?\s+\d+d?\s+\(\d{4}\)$",  # Volume Reporter Page (Year)
                r"^[A-Z][a-zA-Z\s]+v\.\s+[A-Z][a-zA-Z\s]+,\s+\d+\s+[A-Z][a-z]+\.?\s+\d+d?\s+\([A-Z][a-z\.\s]+\d{4}\)$",
                r"^\d+\s+U\.S\.\s+\d+\s+\(\d{4}\)$",  # Supreme Court
                r"^\d+\s+F\.\d+d\s+\d+\s+\([A-Z\.\s]+\d{4}\)$",  # Federal courts
            ],
            "statute": [
                r"^\d+\s+U\.S\.C\.\s+§\s+\d+(\([a-z]\))?$",  # Federal statute
                r"^[A-Z][a-z]+\.?\s+Code\s+§\s+\d+(\.[a-z\d]+)?$",  # State code
                r"^[A-Z][a-z]+\.?\s+[A-Z][a-z]+\.?\s+Code\s+Ann\.\s+§\s+\d+(\.[a-z\d]+)?$",
            ],
            "regulation": [
                r"^\d+\s+C\.F\.R\.\s+§\s+\d+(\.\d+)?$",  # Federal regulation
                r"^[A-Z][a-z]+\.?\s+Regs?\.\s+tit\.\s+\d+,\s+§\s+\d+(\.\d+)?$",  # State regulation
            ],
        }

    async def validate_authority_hierarchy(
        self, citations: List[LegalCitation], jurisdiction: str
    ) -> Dict[str, Any]:
        """Validate authority hierarchy and identify conflicts"""
        validation_result = {
            "valid_authorities": [],
            "invalid_authorities": [],
            "conflicts": [],
            "preemption_issues": [],
            "recommendations": [],
        }

        try:
            # Group citations by jurisdiction and authority level
            jurisdiction_groups = self._group_by_jurisdiction(citations)

            # Validate each jurisdiction group
            for juris, juris_citations in jurisdiction_groups.items():
                juris_validation = await self._validate_jurisdiction_group(
                    juris_citations, juris, jurisdiction
                )

                validation_result["valid_authorities"].extend(juris_validation["valid"])
                validation_result["invalid_authorities"].extend(
                    juris_validation["invalid"]
                )
                validation_result["conflicts"].extend(juris_validation["conflicts"])

            # Check for federal preemption issues
            federal_citations = jurisdiction_groups.get("federal", [])
            state_citations = [
                c
                for j, cites in jurisdiction_groups.items()
                if j != "federal"
                for c in cites
            ]

            if federal_citations and state_citations:
                preemption_analysis = await self._analyze_federal_preemption(
                    federal_citations, state_citations, jurisdiction
                )
                validation_result["preemption_issues"].append(preemption_analysis)

            # Generate recommendations
            validation_result["recommendations"] = (
                self._generate_validation_recommendations(validation_result)
            )

            logger.info(
                f"Authority validation completed: {len(validation_result['valid_authorities'])} valid, "
                f"{len(validation_result['invalid_authorities'])} invalid, "
                f"{len(validation_result['conflicts'])} conflicts"
            )

            return validation_result

        except Exception as e:
            logger.exception(f"Authority hierarchy validation failed: {e}")
            raise

    def _group_by_jurisdiction(
        self, citations: List[LegalCitation]
    ) -> Dict[str, List[LegalCitation]]:
        """Group citations by jurisdiction"""
        groups = {}

        for citation in citations:
            jurisdiction = citation.jurisdiction or "unknown"
            if jurisdiction not in groups:
                groups[jurisdiction] = []
            groups[jurisdiction].append(citation)

        return groups

    async def _validate_jurisdiction_group(
        self,
        citations: List[LegalCitation],
        citation_jurisdiction: str,
        target_jurisdiction: str,
    ) -> Dict[str, List]:
        """Validate citations within a single jurisdiction"""
        result = {"valid": [], "invalid": [], "conflicts": []}

        # Check jurisdiction compatibility
        is_compatible = self.jurisdiction_manager.is_jurisdiction_compatible(
            citation_jurisdiction, target_jurisdiction
        )

        if not is_compatible and citation_jurisdiction != "federal":
            # Mark all as invalid due to jurisdiction mismatch
            result["invalid"].extend(citations)
            return result

        # Sort citations by authority level for hierarchy validation
        sorted_citations = sorted(
            citations,
            key=lambda c: self.authority_hierarchy.get(
                AuthorityLevel(c.authority_level), 10
            ),
        )

        # Validate authority hierarchy within jurisdiction
        for i, citation in enumerate(sorted_citations):
            # Check if citation conflicts with higher authority
            conflicts = []

            for higher_auth in sorted_citations[:i]:
                if self._citations_conflict(citation, higher_auth):
                    conflict = AuthorityConflict(
                        conflict_id=f"conflict_{len(result['conflicts']) + 1}",
                        primary_authority=higher_auth,
                        conflicting_authority=citation,
                        conflict_type="authority_hierarchy",
                        severity="medium",
                        resolution_strategy="defer_to_higher_authority",
                        resolved_authority=higher_auth,
                    )
                    conflicts.append(conflict)

            if conflicts:
                result["conflicts"].extend(conflicts)
                result["invalid"].append(citation)
            else:
                result["valid"].append(citation)

        return result

    def _citations_conflict(
        self, citation1: LegalCitation, citation2: LegalCitation
    ) -> bool:
        """Check if two citations conflict substantively"""
        # Simple conflict detection based on similar topics but different outcomes
        # This is a simplified implementation - real conflict detection would require
        # more sophisticated legal analysis

        if not citation1.title or not citation2.title:
            return False

        # Check for topic similarity
        title1_lower = citation1.title.lower()
        title2_lower = citation2.title.lower()

        # Extract key legal concepts
        concepts1 = self._extract_legal_concepts(title1_lower)
        concepts2 = self._extract_legal_concepts(title2_lower)

        # If significant concept overlap but different authority levels, potential conflict
        overlap = len(concepts1.intersection(concepts2))
        if overlap >= 2 and citation1.authority_level != citation2.authority_level:
            return True

        return False

    def _extract_legal_concepts(self, text: str) -> set:
        """Extract legal concepts from text"""
        legal_terms = {
            "negligence",
            "breach",
            "contract",
            "duty",
            "care",
            "damages",
            "fraud",
            "misrepresentation",
            "defamation",
            "liability",
            "causation",
            "proximate",
            "intentional",
            "reckless",
        }

        found_terms = set()
        for term in legal_terms:
            if term in text:
                found_terms.add(term)

        return found_terms

    async def _analyze_federal_preemption(
        self,
        federal_citations: List[LegalCitation],
        state_citations: List[LegalCitation],
        jurisdiction: str,
    ) -> FederalPreemptionAnalysis:
        """Analyze federal preemption issues"""
        try:
            # Determine if federal preemption applies
            preemption_type = "none"
            preemption_exists = False

            # Check for complete preemption areas
            for citation in federal_citations:
                title_lower = (citation.title or "").lower()

                for area in self.federal_preemption_areas["complete"]:
                    if area.replace("_", " ") in title_lower:
                        preemption_type = "complete"
                        preemption_exists = True
                        break

                if preemption_exists:
                    break

            # Check for partial preemption if complete not found
            if not preemption_exists:
                for citation in federal_citations:
                    title_lower = (citation.title or "").lower()

                    for area in self.federal_preemption_areas["partial"]:
                        if area.replace("_", " ") in title_lower:
                            preemption_type = "partial"
                            preemption_exists = True
                            break

                    if preemption_exists:
                        break

            # Select best federal and state authorities
            best_federal = (
                max(
                    federal_citations,
                    key=lambda c: (
                        self.authority_hierarchy.get(
                            AuthorityLevel(c.authority_level), 10
                        ),
                        c.relevance_score,
                    ),
                )
                if federal_citations
                else None
            )

            best_state = (
                max(
                    state_citations,
                    key=lambda c: (
                        self.authority_hierarchy.get(
                            AuthorityLevel(c.authority_level), 10
                        ),
                        c.relevance_score,
                    ),
                )
                if state_citations
                else None
            )

            # Generate analysis notes
            if preemption_type == "complete":
                notes = "Complete federal preemption likely applies. Federal authority should control."
            elif preemption_type == "partial":
                notes = "Partial federal preemption may apply. Both federal and state authorities relevant."
            else:
                notes = f"No clear federal preemption. State law likely controls in {jurisdiction}."

            return FederalPreemptionAnalysis(
                preemption_exists=preemption_exists,
                preemption_type=preemption_type,
                federal_authority=best_federal,
                state_authority=best_state,
                analysis_notes=notes,
                confidence_score=0.7 if preemption_exists else 0.3,
            )

        except Exception as e:
            logger.error(f"Federal preemption analysis failed: {e}")
            return FederalPreemptionAnalysis(
                preemption_exists=False,
                preemption_type="none",
                analysis_notes=f"Analysis failed: {e}",
                confidence_score=0.0,
            )

    def _generate_validation_recommendations(
        self, validation_result: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        # Authority recommendations
        if len(validation_result["invalid_authorities"]) > 0:
            recommendations.append(
                f"Remove {len(validation_result['invalid_authorities'])} invalid authorities "
                "due to jurisdiction or hierarchy conflicts"
            )

        # Conflict recommendations
        if len(validation_result["conflicts"]) > 0:
            high_priority_conflicts = [
                c
                for c in validation_result["conflicts"]
                if c.severity in ["critical", "high"]
            ]
            if high_priority_conflicts:
                recommendations.append(
                    f"Resolve {len(high_priority_conflicts)} high-priority authority conflicts"
                )

        # Preemption recommendations
        if validation_result["preemption_issues"]:
            for issue in validation_result["preemption_issues"]:
                if issue.preemption_exists:
                    recommendations.append(
                        f"Review federal preemption analysis: {issue.preemption_type} preemption identified"
                    )

        # General recommendations
        valid_authorities = validation_result["valid_authorities"]
        if len(valid_authorities) < 5:
            recommendations.append(
                "Consider expanding research to find additional supporting authority"
            )

        high_authority_count = len(
            [a for a in valid_authorities if a.authority_level <= 2]
        )
        if high_authority_count < 2:
            recommendations.append(
                "Seek additional high-level authority (Supreme/Appellate courts)"
            )

        return recommendations

    async def validate_bluebook_citations(
        self, citations: List[LegalCitation]
    ) -> List[BluebookValidation]:
        """Validate citations for Bluebook compliance"""
        validations = []

        for citation in citations:
            validation = await self._validate_single_bluebook_citation(citation)
            validations.append(validation)

        return validations

    async def _validate_single_bluebook_citation(
        self, citation: LegalCitation
    ) -> BluebookValidation:
        """Validate a single citation for Bluebook compliance"""
        try:
            citation_text = citation.citation or ""
            citation_type = citation.citation_type or "case"

            if not citation_text:
                return BluebookValidation(
                    is_compliant=False,
                    compliance_level=CitationCompliance.NON_COMPLIANT,
                    detected_format="empty",
                    errors=["Citation text is empty"],
                )

            # Get relevant patterns for citation type
            patterns = self.bluebook_patterns.get(citation_type, [])

            # Check against patterns
            is_compliant = False
            detected_format = "unknown"
            errors = []
            warnings = []

            for i, pattern in enumerate(patterns):
                if re.match(pattern, citation_text.strip()):
                    is_compliant = True
                    detected_format = f"{citation_type}_pattern_{i+1}"
                    break

            if not is_compliant:
                errors.append(
                    f"Citation does not match standard {citation_type} format"
                )

                # Provide specific format guidance
                if citation_type == "case":
                    errors.append(
                        "Case citations should follow: Volume Reporter Page (Year) format"
                    )
                elif citation_type == "statute":
                    errors.append(
                        "Statute citations should follow: Title Code § Section format"
                    )
                elif citation_type == "regulation":
                    errors.append(
                        "Regulation citations should follow: Title C.F.R. § Section format"
                    )

            # Additional validation checks
            validation_checks = self._perform_additional_bluebook_checks(
                citation_text, citation_type
            )
            errors.extend(validation_checks["errors"])
            warnings.extend(validation_checks["warnings"])

            # Determine compliance level
            if is_compliant and not errors:
                compliance_level = CitationCompliance.BLUEBOOK_COMPLIANT
            elif not errors or (len(errors) == 1 and warnings):
                compliance_level = CitationCompliance.ACCEPTABLE
            else:
                compliance_level = CitationCompliance.NON_COMPLIANT

            return BluebookValidation(
                is_compliant=compliance_level == CitationCompliance.BLUEBOOK_COMPLIANT,
                compliance_level=compliance_level,
                detected_format=detected_format,
                suggested_format=(
                    self._suggest_bluebook_format(citation_text, citation_type)
                    if not is_compliant
                    else None
                ),
                errors=errors,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"Bluebook validation failed for citation: {e}")
            return BluebookValidation(
                is_compliant=False,
                compliance_level=CitationCompliance.UNKNOWN,
                detected_format="error",
                errors=[f"Validation error: {e}"],
            )

    def _perform_additional_bluebook_checks(
        self, citation_text: str, citation_type: str
    ) -> Dict[str, List[str]]:
        """Perform additional Bluebook compliance checks"""
        errors = []
        warnings = []

        # Check for common formatting issues
        if citation_text != citation_text.strip():
            warnings.append("Citation has leading/trailing whitespace")

        # Check for proper abbreviations
        if citation_type == "case":
            # Check for proper "v." vs "vs"
            if " vs " in citation_text or " vs. " in citation_text:
                errors.append("Use 'v.' instead of 'vs' or 'vs.' in case citations")

            # Check for proper year format
            year_match = re.search(r"\((\d{4})\)", citation_text)
            if year_match:
                year = int(year_match.group(1))
                current_year = datetime.now().year
                if year > current_year or year < 1800:
                    warnings.append(f"Unusual year in citation: {year}")

        # Check for proper section symbol
        if citation_type in ["statute", "regulation"]:
            if (
                " sec. " in citation_text.lower()
                or " section " in citation_text.lower()
            ):
                errors.append("Use '§' symbol instead of 'sec.' or 'section'")

        return {"errors": errors, "warnings": warnings}

    def _suggest_bluebook_format(self, citation_text: str, citation_type: str) -> str:
        """Suggest proper Bluebook format for citation"""
        # This is a simplified suggestion system
        # In practice, this would require more sophisticated parsing

        suggestions = {
            "case": "Volume Reporter Page (Year) - e.g., 123 F.3d 456 (9th Cir. 2001)",
            "statute": "Title Code § Section - e.g., 42 U.S.C. § 1983",
            "regulation": "Title C.F.R. § Section - e.g., 29 C.F.R. § 1630.2",
        }

        return suggestions.get(
            citation_type, "Follow standard Bluebook format for citation type"
        )

    async def resolve_authority_conflicts(
        self, conflicts: List[AuthorityConflict]
    ) -> List[AuthorityConflict]:
        """Resolve authority conflicts using hierarchy and jurisdiction rules"""
        resolved_conflicts = []

        for conflict in conflicts:
            try:
                resolved_conflict = await self._resolve_single_conflict(conflict)
                resolved_conflicts.append(resolved_conflict)

                # Store conflict resolution in knowledge graph
                await self._store_conflict_resolution(resolved_conflict)

            except Exception as e:
                logger.error(f"Failed to resolve conflict {conflict.conflict_id}: {e}")
                conflict.notes = f"Resolution failed: {e}"
                resolved_conflicts.append(conflict)

        return resolved_conflicts

    async def _resolve_single_conflict(
        self, conflict: AuthorityConflict
    ) -> AuthorityConflict:
        """Resolve a single authority conflict"""
        primary = conflict.primary_authority
        conflicting = conflict.conflicting_authority

        # Resolution based on authority hierarchy
        primary_level = self.authority_hierarchy.get(
            AuthorityLevel(primary.authority_level), 10
        )
        conflicting_level = self.authority_hierarchy.get(
            AuthorityLevel(conflicting.authority_level), 10
        )

        if primary_level < conflicting_level:
            # Primary authority is higher - use it
            conflict.resolved_authority = primary
            conflict.resolution_confidence = 0.9
            conflict.resolution_strategy = "higher_authority_controls"
            conflict.notes = f"Resolved in favor of higher authority ({AuthorityLevel(primary.authority_level).name})"

        elif conflicting_level < primary_level:
            # Conflicting authority is higher - use it
            conflict.resolved_authority = conflicting
            conflict.resolution_confidence = 0.9
            conflict.resolution_strategy = "higher_authority_controls"
            conflict.notes = f"Resolved in favor of higher authority ({AuthorityLevel(conflicting.authority_level).name})"

        else:
            # Same authority level - use other factors
            if primary.year and conflicting.year:
                if primary.year > conflicting.year:
                    conflict.resolved_authority = primary
                    conflict.resolution_confidence = 0.7
                    conflict.resolution_strategy = "more_recent_authority"
                    conflict.notes = f"Resolved in favor of more recent authority ({primary.year} vs {conflicting.year})"
                else:
                    conflict.resolved_authority = conflicting
                    conflict.resolution_confidence = 0.7
                    conflict.resolution_strategy = "more_recent_authority"
                    conflict.notes = f"Resolved in favor of more recent authority ({conflicting.year} vs {primary.year})"
            else:
                # Use relevance score
                if primary.relevance_score > conflicting.relevance_score:
                    conflict.resolved_authority = primary
                    conflict.resolution_confidence = 0.6
                    conflict.resolution_strategy = "higher_relevance"
                    conflict.notes = "Resolved in favor of more relevant authority"
                else:
                    conflict.resolved_authority = conflicting
                    conflict.resolution_confidence = 0.6
                    conflict.resolution_strategy = "higher_relevance"
                    conflict.notes = "Resolved in favor of more relevant authority"

        # Mark for attorney review if confidence is low
        conflict.attorney_review_required = conflict.resolution_confidence < 0.8

        return conflict

    async def _store_conflict_resolution(self, conflict: AuthorityConflict):
        """Store conflict resolution in knowledge graph"""
        try:
            # Store in fact_conflicts table
            self.kg._execute(
                """
                INSERT INTO fact_conflicts
                (entity_a_id, entity_b_id, conflict_type, severity,
                 resolution_strategy, resolved_entity_id, resolution_confidence,
                 attorney_reviewed, resolution_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    conflict.primary_authority.citation,
                    conflict.conflicting_authority.citation,
                    conflict.conflict_type,
                    conflict.severity,
                    conflict.resolution_strategy,
                    (
                        conflict.resolved_authority.citation
                        if conflict.resolved_authority
                        else None
                    ),
                    conflict.resolution_confidence,
                    not conflict.attorney_review_required,
                    conflict.notes,
                ),
            )

            self.kg.conn.commit()
            logger.debug(f"Stored conflict resolution: {conflict.conflict_id}")

        except Exception as e:
            logger.error(f"Failed to store conflict resolution: {e}")

    async def get_jurisdiction_authority_summary(
        self, jurisdiction: str
    ) -> Dict[str, Any]:
        """Get summary of legal authorities for a jurisdiction"""
        try:
            # Get jurisdiction configuration
            juris_config = self.jurisdiction_manager.jurisdictions.get(jurisdiction)
            if not juris_config:
                return {"error": f"Unknown jurisdiction: {jurisdiction}"}

            # Get cached authorities from database
            authorities = self.kg._execute(
                """
                SELECT authority_type, authority_name, authority_citation, 
                       precedence_level, federal_preemption_scope
                FROM jurisdiction_authorities 
                WHERE jurisdiction = ?
                ORDER BY precedence_level ASC
            """,
                (jurisdiction,),
            ).fetchall()

            # Organize by authority type
            authority_summary = {
                "jurisdiction": jurisdiction,
                "jurisdiction_name": juris_config.jurisdiction_name,
                "authority_types": {},
                "total_authorities": len(authorities),
                "preemption_areas": [],
            }

            for auth_type, name, citation, precedence, preemption in authorities:
                if auth_type not in authority_summary["authority_types"]:
                    authority_summary["authority_types"][auth_type] = []

                authority_summary["authority_types"][auth_type].append(
                    {
                        "name": name,
                        "citation": citation,
                        "precedence_level": precedence,
                        "preemption_scope": preemption,
                    }
                )

                if preemption and preemption != "none":
                    authority_summary["preemption_areas"].append(
                        {"authority": name, "scope": preemption}
                    )

            return authority_summary

        except Exception as e:
            logger.exception(f"Failed to get jurisdiction authority summary: {e}")
            return {"error": str(e)}

    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation performance statistics"""
        try:
            # Get conflict statistics
            conflict_stats = self.kg._execute(
                """
                SELECT conflict_type, COUNT(*) as count
                FROM fact_conflicts
                GROUP BY conflict_type
            """
            ).fetchall()

            # Get resolution statistics
            resolution_stats = self.kg._execute(
                """
                SELECT resolution_strategy, AVG(resolution_confidence) as avg_confidence
                FROM fact_conflicts
                WHERE resolved_entity_id IS NOT NULL
                GROUP BY resolution_strategy
            """
            ).fetchall()

            return {
                "total_conflicts": sum(count for _, count in conflict_stats),
                "conflict_types": dict(conflict_stats),
                "resolution_strategies": dict(resolution_stats),
                "average_resolution_confidence": (
                    sum(conf for _, conf in resolution_stats) / len(resolution_stats)
                    if resolution_stats
                    else 0.0
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get validation statistics: {e}")
            return {"error": str(e)}
