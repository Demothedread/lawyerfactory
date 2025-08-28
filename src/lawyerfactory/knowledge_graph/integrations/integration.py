"""
# Script Name: integration.py
# Description: Knowledge Graph Integration Module Integrates enhanced knowledge graph, legal relationship detection, and draft processing with the existing lawyerfactory workflow system.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Research
#   - Group Tags: knowledge-graph
Knowledge Graph Integration Module
Integrates enhanced knowledge graph, legal relationship detection, and draft processing
with the existing lawyerfactory workflow system.
"""

from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from enhanced_draft_processor import EnhancedDraftProcessor
from enhanced_knowledge_graph import EnhancedKnowledgeGraph
from legal_relationship_detector import LegalRelationshipDetector

logger = logging.getLogger(__name__)


class KnowledgeGraphIntegration:
    """Centralized integration point for enhanced knowledge graph capabilities"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()
        self.kg = None
        self.relationship_detector = None
        self.draft_processor = None
        self._initialize_components()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for knowledge graph integration"""
        return {
            "knowledge_graph_path": "knowledge_graphs/main.db",
            "enable_enhanced_processing": True,
            "confidence_thresholds": {
                "entity_extraction": 0.6,
                "relationship_mapping": 0.5,
                "fact_validation": 0.7,
                "cross_validation": 0.8,
            },
            "processing_modes": {
                "fact_statements": {
                    "source_credibility": 0.9,
                    "aggregate_across_drafts": True,
                    "detect_conflicts": True,
                },
                "case_complaints": {
                    "source_credibility": 0.85,
                    "extract_legal_issues": True,
                    "build_claims_hierarchy": True,
                },
            },
            "output_settings": {
                "generate_facts_matrix": True,
                "build_temporal_timeline": True,
                "assess_case_strength": True,
                "provide_recommendations": True,
            },
        }

    def _initialize_components(self):
        """Initialize all knowledge graph components"""
        try:
            # Initialize enhanced knowledge graph
            kg_path = self.config["knowledge_graph_path"]
            Path(kg_path).parent.mkdir(parents=True, exist_ok=True)

            self.kg = EnhancedKnowledgeGraph(kg_path)
            logger.info(f"Enhanced knowledge graph initialized: {kg_path}")

            # Initialize relationship detector
            self.relationship_detector = LegalRelationshipDetector(self.kg)
            logger.info("Legal relationship detector initialized")

            # Initialize draft processor
            self.draft_processor = EnhancedDraftProcessor(kg_path)
            logger.info("Enhanced draft processor initialized")

        except Exception as e:
            logger.exception(f"Failed to initialize knowledge graph components: {e}")
            raise

    def process_draft_documents_comprehensive(
        self, draft_documents: List[Dict[str, Any]], session_id: str
    ) -> Dict[str, Any]:
        """Comprehensive processing of draft documents with full relationship mapping"""
        logger.info(
            f"Starting comprehensive processing of {len(draft_documents)} draft documents"
        )

        try:
            # Separate drafts by type
            fact_drafts = [
                doc
                for doc in draft_documents
                if doc.get("draft_type") == "fact_statement"
            ]
            case_drafts = [
                doc
                for doc in draft_documents
                if doc.get("draft_type") == "case_complaint"
            ]

            results = {
                "session_id": session_id,
                "processing_timestamp": datetime.now().isoformat(),
                "input_summary": {
                    "total_drafts": len(draft_documents),
                    "fact_drafts": len(fact_drafts),
                    "case_drafts": len(case_drafts),
                },
                "processing_results": {},
                "aggregated_analysis": {},
                "knowledge_graph_impact": {},
                "recommendations": [],
            }

            # Process fact statement drafts
            if fact_drafts:
                logger.info(f"Processing {len(fact_drafts)} fact statement drafts")
                fact_results = self.draft_processor.process_fact_statement_drafts(
                    fact_drafts, session_id
                )
                results["processing_results"]["fact_statements"] = fact_results

            # Process case/complaint drafts
            if case_drafts:
                logger.info(f"Processing {len(case_drafts)} case/complaint drafts")
                case_results = self.draft_processor.process_case_complaint_drafts(
                    case_drafts, session_id
                )
                results["processing_results"]["case_complaints"] = case_results

            # Aggregate and cross-validate if both types present
            if fact_drafts and case_drafts:
                logger.info("Performing cross-validation and aggregation")
                aggregated = self.draft_processor.aggregate_draft_results(
                    results["processing_results"].get("fact_statements"),
                    results["processing_results"].get("case_complaints"),
                )
                results["aggregated_analysis"] = aggregated

            # Analyze knowledge graph impact
            results["knowledge_graph_impact"] = self._analyze_knowledge_graph_impact()

            # Generate recommendations
            results["recommendations"] = self._generate_comprehensive_recommendations(
                results
            )

            # Update final statistics
            results["final_statistics"] = self._calculate_final_statistics(results)

            logger.info(
                f"Comprehensive processing complete: {results['final_statistics']['total_entities']} entities, {results['final_statistics']['total_relationships']} relationships"
            )
            return results

        except Exception as e:
            logger.exception(
                f"Comprehensive processing failed for session {session_id}: {e}"
            )
            return {
                "session_id": session_id,
                "error": str(e),
                "processing_timestamp": datetime.now().isoformat(),
                "success": False,
            }

    def generate_facts_matrix_and_statement(
        self, session_id: str, processing_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate facts matrix and statement of facts from processed drafts"""
        logger.info(f"Generating facts matrix and statement for session {session_id}")

        try:
            # Get comprehensive case foundation
            if processing_results and "aggregated_analysis" in processing_results:
                case_foundation = processing_results["aggregated_analysis"][
                    "case_foundation"
                ]
            else:
                # Retrieve from knowledge graph if not provided
                case_foundation = self._rebuild_case_foundation_from_kg(session_id)

            # Generate facts matrix
            facts_matrix = self._generate_enhanced_facts_matrix(case_foundation)

            # Generate statement of facts outline
            statement_outline = self._generate_statement_of_facts_outline(
                facts_matrix, case_foundation
            )

            # Generate legal issue summary
            legal_issues_summary = self._generate_legal_issues_summary(case_foundation)

            # Generate procedural checklist
            procedural_checklist = self._generate_procedural_checklist(case_foundation)

            return {
                "session_id": session_id,
                "generation_timestamp": datetime.now().isoformat(),
                "facts_matrix": facts_matrix,
                "statement_of_facts_outline": statement_outline,
                "legal_issues_summary": legal_issues_summary,
                "procedural_checklist": procedural_checklist,
                "case_strength_assessment": case_foundation.get(
                    "strength_assessment", {}
                ),
                "attorney_review_points": self._identify_attorney_review_points(
                    case_foundation
                ),
                "research_recommendations": self._generate_research_recommendations(
                    case_foundation
                ),
            }

        except Exception as e:
            logger.exception(
                f"Failed to generate facts matrix for session {session_id}: {e}"
            )
            return {
                "session_id": session_id,
                "error": str(e),
                "generation_timestamp": datetime.now().isoformat(),
                "success": False,
            }

    def _analyze_knowledge_graph_impact(self) -> Dict[str, Any]:
        """Analyze the impact of processing on the knowledge graph"""
        try:
            stats = self.kg.get_enhanced_statistics()

            # Detect recent conflicts
            recent_conflicts = self.kg.detect_fact_conflicts()

            return {
                "current_statistics": stats,
                "recent_conflicts_detected": len(recent_conflicts),
                "conflict_details": recent_conflicts[:5],  # Limit to top 5 for summary
                "knowledge_graph_health": self._assess_kg_health(stats),
                "recommendations": self._generate_kg_recommendations(
                    stats, recent_conflicts
                ),
            }

        except Exception as e:
            logger.error(f"Failed to analyze knowledge graph impact: {e}")
            return {"error": str(e)}

    def _assess_kg_health(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the health and quality of the knowledge graph"""
        confidence_metrics = stats.get("confidence_metrics", {})
        avg_confidence = confidence_metrics.get("average", 0.5)

        health_score = 0
        issues = []

        # Confidence assessment
        if avg_confidence > 0.8:
            health_score += 40
        elif avg_confidence > 0.6:
            health_score += 25
        else:
            issues.append("Low average confidence in extracted entities")

        # Relationship density assessment
        total_entities = stats.get("total_entities", 0)
        total_relationships = len(stats.get("legal_relationships", []))

        if total_entities > 0:
            relationship_ratio = total_relationships / total_entities
            if relationship_ratio > 0.5:
                health_score += 30
            elif relationship_ratio > 0.2:
                health_score += 15
            else:
                issues.append(
                    "Low relationship density - entities may be insufficiently connected"
                )

        # Conflict assessment
        conflicts = stats.get("conflicts", {})
        total_conflicts = conflicts.get("total", 0)
        reviewed_conflicts = conflicts.get("reviewed", 0)

        if total_conflicts == 0:
            health_score += 20
        elif reviewed_conflicts >= total_conflicts * 0.8:
            health_score += 15
        else:
            issues.append(
                f"Unresolved conflicts: {total_conflicts - reviewed_conflicts}"
            )

        # Data completeness
        if total_entities > 10 and total_relationships > 5:
            health_score += 10

        return {
            "health_score": min(100, health_score),
            "health_rating": (
                "excellent"
                if health_score >= 90
                else (
                    "good"
                    if health_score >= 70
                    else "fair" if health_score >= 50 else "poor"
                )
            ),
            "identified_issues": issues,
            "improvement_suggestions": self._generate_health_improvements(
                health_score, issues
            ),
        }

    def _generate_kg_recommendations(
        self, stats: Dict[str, Any], conflicts: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on knowledge graph analysis"""
        recommendations = []

        confidence_metrics = stats.get("confidence_metrics", {})
        avg_confidence = confidence_metrics.get("average", 0.5)

        if avg_confidence < 0.7:
            recommendations.append(
                "Consider manual review of low-confidence entities to improve data quality"
            )

        if len(conflicts) > 5:
            recommendations.append(
                "Multiple fact conflicts detected - attorney review recommended"
            )

        total_relationships = len(stats.get("legal_relationships", []))
        if total_relationships < 10:
            recommendations.append(
                "Limited relationship mapping - consider processing additional documents"
            )

        return recommendations

    def _generate_comprehensive_recommendations(
        self, results: Dict[str, Any]
    ) -> List[str]:
        """Generate comprehensive recommendations based on processing results"""
        recommendations = []

        # Processing-based recommendations
        if "aggregated_analysis" in results:
            aggregated = results["aggregated_analysis"]
            case_foundation = aggregated.get("case_foundation", {})
            strength_assessment = case_foundation.get("strength_assessment", {})

            # Case strength recommendations
            strength_rating = strength_assessment.get("strength_rating", "developing")
            if strength_rating == "developing":
                recommendations.append(
                    "Case foundation is developing - gather additional evidence and documentation"
                )
            elif strength_rating == "moderate":
                recommendations.append(
                    "Case shows moderate strength - focus on strengthening key claims"
                )
            elif strength_rating == "strong":
                recommendations.append(
                    "Case foundation is strong - consider aggressive litigation strategy"
                )

            # Cross-validation recommendations
            cross_validation = aggregated.get("cross_validation", {})
            inconsistent_entities = cross_validation.get("inconsistent_entities", [])
            if len(inconsistent_entities) > 0:
                recommendations.append(
                    f"Review {len(inconsistent_entities)} inconsistent entities between fact statements and case documents"
                )

        # Knowledge graph recommendations
        kg_impact = results.get("knowledge_graph_impact", {})
        kg_recommendations = kg_impact.get("recommendations", [])
        recommendations.extend(kg_recommendations)

        return recommendations

    def _calculate_final_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate final processing statistics"""
        stats = {
            "total_entities": 0,
            "total_relationships": 0,
            "fact_drafts_processed": 0,
            "case_drafts_processed": 0,
            "conflicts_detected": 0,
            "cross_validated_entities": 0,
        }

        # Aggregate from processing results
        processing_results = results.get("processing_results", {})

        if "fact_statements" in processing_results:
            fact_results = processing_results["fact_statements"]
            stats["total_entities"] += fact_results.get("total_entities", 0)
            stats["total_relationships"] += fact_results.get("total_relationships", 0)
            stats["fact_drafts_processed"] = fact_results.get("drafts_processed", 0)
            stats["conflicts_detected"] += fact_results.get("conflicts_detected", 0)

        if "case_complaints" in processing_results:
            case_results = processing_results["case_complaints"]
            stats["total_entities"] += case_results.get("total_entities", 0)
            stats["total_relationships"] += case_results.get("total_relationships", 0)
            stats["case_drafts_processed"] = case_results.get("drafts_processed", 0)

        # Add aggregated analysis stats if available
        if "aggregated_analysis" in results:
            aggregated = results["aggregated_analysis"]
            cross_validation = aggregated.get("cross_validation", {})
            stats["cross_validated_entities"] = len(
                cross_validation.get("consistent_entities", [])
            )

        return stats

    def _generate_enhanced_facts_matrix(
        self, case_foundation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate enhanced facts matrix with categorization and analysis"""
        facts_matrix = {
            "chronological_facts": [],
            "party_facts": {},
            "claim_supporting_facts": {},
            "disputed_facts": [],
            "undisputed_facts": [],
            "material_facts": [],
            "procedural_facts": [],
            "evidence_facts": [],
        }

        foundational_facts = case_foundation.get("foundational_facts", [])

        for fact in foundational_facts:
            confidence = fact.get("confidence", 0.5)
            fact_type = fact.get("type", "unknown")

            # Categorize by confidence and dispute status
            if confidence > 0.8:
                facts_matrix["undisputed_facts"].append(fact)
                if confidence > 0.9:
                    facts_matrix["material_facts"].append(fact)
            elif confidence < 0.6:
                facts_matrix["disputed_facts"].append(fact)

            # Categorize by type
            if fact_type in ["plaintiff", "defendant", "attorney"]:
                party_name = fact.get("name", "Unknown")
                if party_name not in facts_matrix["party_facts"]:
                    facts_matrix["party_facts"][party_name] = []
                facts_matrix["party_facts"][party_name].append(fact)
            elif fact_type in ["evidence", "document"]:
                facts_matrix["evidence_facts"].append(fact)
            elif fact_type in ["court", "jurisdiction", "filing"]:
                facts_matrix["procedural_facts"].append(fact)

        # Sort chronologically where possible
        facts_matrix["chronological_facts"] = sorted(
            foundational_facts, key=lambda x: x.get("confidence", 0), reverse=True
        )

        return facts_matrix

    def _generate_statement_of_facts_outline(
        self, facts_matrix: Dict[str, Any], case_foundation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured outline for statement of facts"""
        outline = {
            "introduction": {
                "parties": self._extract_party_introductions(facts_matrix),
                "jurisdiction_and_venue": self._extract_jurisdictional_facts(
                    facts_matrix
                ),
                "case_overview": self._generate_case_overview(case_foundation),
            },
            "background_facts": {
                "chronological_narrative": self._build_chronological_narrative(
                    facts_matrix
                ),
                "key_relationships": self._identify_key_relationships(case_foundation),
                "relevant_context": self._extract_background_context(facts_matrix),
            },
            "material_facts": {
                "undisputed_facts": facts_matrix.get("undisputed_facts", []),
                "key_events": self._identify_key_events(facts_matrix),
                "causation_chain": self._build_causation_chain(case_foundation),
            },
            "disputed_facts": {
                "factual_disputes": facts_matrix.get("disputed_facts", []),
                "areas_requiring_discovery": self._identify_discovery_needs(
                    facts_matrix
                ),
                "witness_requirements": self._identify_witness_needs(case_foundation),
            },
            "damages_and_relief": {
                "claimed_damages": self._extract_damages_claims(facts_matrix),
                "supporting_evidence": self._identify_damages_support(facts_matrix),
            },
        }

        return outline

    def _generate_legal_issues_summary(
        self, case_foundation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate summary of legal issues and claims"""
        legal_framework = case_foundation.get("legal_framework", {})
        claims_hierarchy = case_foundation.get("claims_hierarchy", {})

        return {
            "primary_legal_issues": legal_framework.get("structure", {}).get(
                "primary_claims", []
            ),
            "causes_of_action": legal_framework.get("structure", {}).get(
                "causes_of_action", []
            ),
            "claims_analysis": self._analyze_claims_strength(claims_hierarchy),
            "legal_standards": self._identify_applicable_legal_standards(
                case_foundation
            ),
            "burden_of_proof": self._analyze_burden_of_proof(legal_framework),
            "potential_defenses": self._identify_potential_defenses(case_foundation),
        }

    def _generate_procedural_checklist(
        self, case_foundation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate procedural requirements checklist"""
        procedural_reqs = case_foundation.get("procedural_checklist", [])

        checklist = []
        for req in procedural_reqs:
            checklist.append(
                {
                    "requirement": req.get("requirement", ""),
                    "type": req.get("type", ""),
                    "urgency": req.get("urgency", "medium"),
                    "status": "pending",
                    "notes": f"Identified from draft analysis - confidence: {req.get('confidence', 'unknown')}",
                }
            )

        # Add standard procedural items
        standard_items = [
            {
                "requirement": "File complaint within statute of limitations",
                "type": "filing",
                "urgency": "high",
            },
            {
                "requirement": "Serve all defendants properly",
                "type": "service",
                "urgency": "high",
            },
            {
                "requirement": "Complete initial discovery planning",
                "type": "discovery",
                "urgency": "medium",
            },
            {
                "requirement": "Preserve relevant documents and evidence",
                "type": "evidence",
                "urgency": "high",
            },
        ]

        for item in standard_items:
            if not any(
                existing["requirement"] == item["requirement"] for existing in checklist
            ):
                checklist.append(
                    {
                        **item,
                        "status": "pending",
                        "notes": "Standard procedural requirement",
                    }
                )

        return sorted(
            checklist,
            key=lambda x: {"high": 0, "medium": 1, "low": 2}[
                x.get("urgency", "medium")
            ],
        )

    def _identify_attorney_review_points(
        self, case_foundation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify points requiring attorney review and decision"""
        review_points = []

        # Conflicts requiring review
        conflicts = case_foundation.get("conflicts", [])
        for conflict in conflicts:
            if conflict.get("severity") == "high":
                review_points.append(
                    {
                        "type": "conflict_resolution",
                        "priority": "high",
                        "description": f"Resolve factual conflict: {conflict.get('type', 'unknown')}",
                        "details": conflict,
                    }
                )

        # Low confidence entities requiring review
        foundational_facts = case_foundation.get("foundational_facts", [])
        low_confidence_facts = [
            fact for fact in foundational_facts if fact.get("confidence", 0) < 0.6
        ]

        if len(low_confidence_facts) > 5:
            review_points.append(
                {
                    "type": "fact_verification",
                    "priority": "medium",
                    "description": f"Review {len(low_confidence_facts)} low-confidence facts",
                    "details": {
                        "count": len(low_confidence_facts),
                        "facts": low_confidence_facts[:3],
                    },
                }
            )

        # Case strength assessment review
        strength_assessment = case_foundation.get("strength_assessment", {})
        if strength_assessment.get("strength_rating") == "developing":
            review_points.append(
                {
                    "type": "case_strategy",
                    "priority": "high",
                    "description": "Case foundation needs strengthening - strategic review required",
                    "details": strength_assessment,
                }
            )

        return review_points

    def _generate_research_recommendations(
        self, case_foundation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate legal research recommendations"""
        recommendations = []

        # Legal issue research
        legal_framework = case_foundation.get("legal_framework", {})
        primary_claims = legal_framework.get("structure", {}).get("primary_claims", [])

        for claim in primary_claims:
            recommendations.append(
                {
                    "type": "case_law_research",
                    "priority": "high",
                    "topic": f"Recent precedents for {claim.get('name', 'unknown claim')}",
                    "jurisdiction": "applicable",
                    "confidence": claim.get("confidence", 0.5),
                }
            )

        # Procedural research
        procedural_checklist = case_foundation.get("procedural_checklist", [])
        complex_procedures = [
            req for req in procedural_checklist if req.get("confidence", 1.0) < 0.7
        ]

        if complex_procedures:
            recommendations.append(
                {
                    "type": "procedural_research",
                    "priority": "medium",
                    "topic": "Local rules and procedures verification",
                    "details": f"{len(complex_procedures)} procedures need clarification",
                }
            )

        return recommendations

    # Helper methods for outline generation
    def _extract_party_introductions(self, facts_matrix: Dict[str, Any]) -> List[str]:
        """Extract party introduction statements"""
        party_facts = facts_matrix.get("party_facts", {})
        introductions = []

        for party_name, facts in party_facts.items():
            if facts:
                party_type = facts[0].get("type", "party")
                introductions.append(f"{party_name} ({party_type})")

        return introductions

    def _extract_jurisdictional_facts(self, facts_matrix: Dict[str, Any]) -> List[str]:
        """Extract jurisdictional and venue facts"""
        procedural_facts = facts_matrix.get("procedural_facts", [])
        jurisdictional = [
            fact.get("name", "")
            for fact in procedural_facts
            if fact.get("type") in ["court", "jurisdiction", "venue"]
        ]
        return jurisdictional

    def _generate_case_overview(self, case_foundation: Dict[str, Any]) -> str:
        """Generate brief case overview"""
        legal_framework = case_foundation.get("legal_framework", {})
        total_issues = legal_framework.get("total_issues", 0)
        strength_rating = case_foundation.get("strength_assessment", {}).get(
            "strength_rating", "unknown"
        )

        return f"Case involves {total_issues} legal issues with {strength_rating} foundation strength"

    def _build_chronological_narrative(self, facts_matrix: Dict[str, Any]) -> List[str]:
        """Build chronological narrative from facts"""
        chronological_facts = facts_matrix.get("chronological_facts", [])
        narrative = []

        for fact in chronological_facts[:10]:  # Limit to top 10 most confident facts
            if fact.get("confidence", 0) > 0.7:
                narrative.append(fact.get("name", "Unknown fact"))

        return narrative

    def _identify_key_relationships(self, case_foundation: Dict[str, Any]) -> List[str]:
        """Identify key relationships from foundation"""
        # This would analyze the relationship data in the case foundation
        # Simplified implementation for now
        return ["Party relationships identified from draft analysis"]

    def _extract_background_context(self, facts_matrix: Dict[str, Any]) -> List[str]:
        """Extract background context facts"""
        # Extract lower-confidence facts that provide context
        all_facts = facts_matrix.get("chronological_facts", [])
        background = [
            fact.get("name", "")
            for fact in all_facts
            if 0.4 < fact.get("confidence", 0) < 0.7
        ]
        return background[:5]  # Limit to 5 background facts

    def _identify_key_events(self, facts_matrix: Dict[str, Any]) -> List[str]:
        """Identify key events from material facts"""
        material_facts = facts_matrix.get("material_facts", [])
        events = [
            fact.get("name", "")
            for fact in material_facts
            if fact.get("type") in ["event", "fact"]
        ]
        return events

    def _build_causation_chain(self, case_foundation: Dict[str, Any]) -> List[str]:
        """Build causation chain from relationships"""
        # This would analyze causal relationships in the knowledge graph
        # Simplified implementation
        return ["Causation chain to be developed from relationship analysis"]

    def _identify_discovery_needs(self, facts_matrix: Dict[str, Any]) -> List[str]:
        """Identify areas needing discovery"""
        disputed_facts = facts_matrix.get("disputed_facts", [])
        needs = [
            f"Discovery needed for: {fact.get('name', 'unknown')}"
            for fact in disputed_facts[:3]
        ]
        return needs

    def _identify_witness_needs(self, case_foundation: Dict[str, Any]) -> List[str]:
        """Identify witness requirements"""
        # Analyze entities for potential witnesses
        return ["Witness identification from entity analysis"]

    def _extract_damages_claims(self, facts_matrix: Dict[str, Any]) -> List[str]:
        """Extract damages claims"""
        all_facts = facts_matrix.get("chronological_facts", [])
        damages = [
            fact.get("name", "")
            for fact in all_facts
            if fact.get("type") in ["damages", "amount"]
        ]
        return damages

    def _identify_damages_support(self, facts_matrix: Dict[str, Any]) -> List[str]:
        """Identify evidence supporting damages"""
        evidence_facts = facts_matrix.get("evidence_facts", [])
        support = [fact.get("name", "") for fact in evidence_facts]
        return support

    def _analyze_claims_strength(
        self, claims_hierarchy: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze strength of each claim"""
        analysis = []
        for claim_name, claim_data in claims_hierarchy.items():
            strength_score = claim_data.get("strength_score", 0.5)
            analysis.append(
                {
                    "claim": claim_name,
                    "strength_score": strength_score,
                    "strength_rating": (
                        "strong"
                        if strength_score > 0.8
                        else "moderate" if strength_score > 0.6 else "weak"
                    ),
                    "supporting_relationships": len(
                        claim_data.get("supporting_relationships", [])
                    ),
                }
            )
        return analysis

    def _identify_applicable_legal_standards(
        self, case_foundation: Dict[str, Any]
    ) -> List[str]:
        """Identify applicable legal standards"""
        # Extract legal standards from the knowledge graph
        return ["Legal standards to be identified from knowledge graph analysis"]

    def _analyze_burden_of_proof(
        self, legal_framework: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze burden of proof for claims"""
        return {
            "standard": "preponderance_of_evidence",  # Default for civil cases
            "analysis": "Burden analysis based on claim types",
            "challenges": "To be determined from claim analysis",
        }

    def _identify_potential_defenses(
        self, case_foundation: Dict[str, Any]
    ) -> List[str]:
        """Identify potential defenses"""
        # This would analyze the case structure for potential defenses
        return ["Potential defenses to be analyzed"]

    def _generate_health_improvements(
        self, health_score: int, issues: List[str]
    ) -> List[str]:
        """Generate health improvement suggestions"""
        improvements = []

        if health_score < 50:
            improvements.append(
                "Consider reprocessing documents with higher confidence thresholds"
            )

        if "Low relationship density" in str(issues):
            improvements.append("Add more documents to improve entity interconnections")

        if "Unresolved conflicts" in str(issues):
            improvements.append(
                "Schedule attorney review session to resolve fact conflicts"
            )

        return improvements

    def _rebuild_case_foundation_from_kg(self, session_id: str) -> Dict[str, Any]:
        """Rebuild case foundation from knowledge graph data"""
        # This would query the knowledge graph to rebuild the case foundation
        # Simplified implementation for now
        return {
            "foundational_facts": [],
            "legal_framework": {},
            "strength_assessment": {"strength_rating": "unknown"},
        }

    def get_integration_statistics(self) -> Dict[str, Any]:
        """Get comprehensive integration statistics"""
        try:
            kg_stats = self.kg.get_enhanced_statistics() if self.kg else {}
            processor_stats = (
                self.draft_processor.get_processing_statistics()
                if self.draft_processor
                else {}
            )

            return {
                "knowledge_graph_stats": kg_stats,
                "processor_stats": processor_stats,
                "integration_health": self._assess_integration_health(),
                "component_status": {
                    "knowledge_graph": bool(self.kg),
                    "relationship_detector": bool(self.relationship_detector),
                    "draft_processor": bool(self.draft_processor),
                },
            }
        except Exception as e:
            logger.error(f"Failed to get integration statistics: {e}")
            return {"error": str(e)}

    def _assess_integration_health(self) -> Dict[str, str]:
        """Assess health of the integration"""
        health = {"status": "healthy", "issues": []}

        if not self.kg:
            health["issues"].append("Knowledge graph not initialized")
            health["status"] = "degraded"

        if not self.relationship_detector:
            health["issues"].append("Relationship detector not available")
            health["status"] = "degraded"

        if not self.draft_processor:
            health["issues"].append("Draft processor not available")
            health["status"] = "degraded"

        if len(health["issues"]) > 1:
            health["status"] = "critical"

        return health

    def close(self):
        """Close all components and cleanup resources"""
        try:
            if self.draft_processor:
                self.draft_processor.close()
            if self.kg:
                self.kg.close()
            logger.info("Knowledge graph integration closed successfully")
        except Exception as e:
            logger.error(f"Error closing knowledge graph integration: {e}")


if __name__ == "__main__":
    # Test the knowledge graph integration
    import os
    import tempfile

    logging.basicConfig(level=logging.INFO)

    # Create test integration
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        config = {"knowledge_graph_path": tmp.name, "enable_enhanced_processing": True}
        integration = KnowledgeGraphIntegration(config)

    try:
        # Test comprehensive processing
        test_drafts = [
            {
                "draft_type": "fact_statement",
                "content": """
                On January 15, 2024, plaintiff John Doe was injured when defendant MegaCorp's 
                delivery truck collided with his vehicle at the intersection of Main and First Streets.
                The defendant's driver was speeding and ran a red light, causing the collision.
                Plaintiff suffered a broken leg and concussion, requiring extensive medical treatment.
                """,
                "timestamp": "2024-01-20T10:00:00Z",
            },
            {
                "draft_type": "case_complaint",
                "content": """
                Plaintiff John Doe brings this negligence action against MegaCorp Inc.
                seeking $150,000 in damages for medical expenses, lost wages, and pain and suffering.
                
                First Cause of Action: Negligence
                Defendant owed plaintiff a duty of care and breached that duty by speeding
                and running a red light, proximately causing plaintiff's injuries.
                """,
                "timestamp": "2024-01-21T14:00:00Z",
            },
        ]

        # Process drafts comprehensively
        results = integration.process_draft_documents_comprehensive(
            test_drafts, "test_session_001"
        )
        print(
            f"Processing Results: {json.dumps(results['final_statistics'], indent=2)}"
        )

        # Generate facts matrix and statement
        facts_output = integration.generate_facts_matrix_and_statement(
            "test_session_001", results
        )
        print(
            f"Facts Matrix Generated: {len(facts_output.get('facts_matrix', {}).get('chronological_facts', []))} facts"
        )

        # Get integration statistics
        stats = integration.get_integration_statistics()
        print(f"Integration Health: {stats['integration_health']['status']}")

    except Exception as e:
        print(f"Integration test failed: {e}")
    finally:
        integration.close()
        os.unlink(tmp.name)
