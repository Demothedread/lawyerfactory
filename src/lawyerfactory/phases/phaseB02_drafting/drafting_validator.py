"""
Drafting Validation System for LawyerFactory
Validates draft complaints against defendant-specific clusters.
Provides similarity analysis and improvement recommendations.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import unified storage API
try:
    from lawyerfactory.storage.enhanced_unified_storage_api import (
        EnhancedUnifiedStorageAPI,
        get_enhanced_unified_storage_api,
        EvidenceMetadata
    )
    UNIFIED_STORAGE_AVAILABLE = True
except ImportError:
    logger.warning("Enhanced unified storage not available")
    UNIFIED_STORAGE_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Comprehensive validation result for a draft complaint"""

    draft_id: str
    case_id: str
    defendant_name: str
    validation_timestamp: datetime
    overall_score: float  # 0-1 scale
    similarity_score: float  # 0-1 scale
    similarity_threshold: float
    is_valid: bool
    issues_found: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    similar_documents: List[Dict[str, Any]] = field(default_factory=list)
    missing_elements: List[str] = field(default_factory=list)
    strength_assessment: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0


@dataclass
class ValidationMetrics:
    """Detailed validation metrics"""

    factual_similarity: float = 0.0
    legal_elements_similarity: float = 0.0
    structural_similarity: float = 0.0
    language_similarity: float = 0.0
    defendant_specificity: float = 0.0
    overall_confidence: float = 0.0


class DraftingValidator:
    """
    Advanced drafting validator that compares draft complaints
    against defendant-specific document clusters.
    """

    def __init__(self, intake_processor=None, cluster_manager=None):
        self.intake_processor = intake_processor
        self.cluster_manager = cluster_manager

        # Initialize unified storage
        self.unified_storage = None
        if UNIFIED_STORAGE_AVAILABLE:
            try:
                self.unified_storage = get_enhanced_unified_storage_api()
                logger.info("Unified storage initialized for drafting validator")
            except Exception as e:
                logger.warning(f"Failed to initialize unified storage: {e}")

        # Validation thresholds
        self.default_thresholds = {
            "similarity_threshold": 0.6,
            "factual_threshold": 0.5,
            "legal_threshold": 0.7,
            "structural_threshold": 0.4,
        }

        # Common legal elements to check for
        self.required_elements = [
            "jurisdiction_venue",
            "parties_identified",
            "factual_allegations",
            "legal_claims",
            "damages_requested",
            "prayer_for_relief",
        ]

        # Common issues to detect
        self.common_issues = {
            "missing_defendant_specifics": "Complaint lacks defendant-specific details",
            "insufficient_facts": "Insufficient factual allegations",
            "missing_legal_elements": "Missing required legal elements",
            "poor_structure": "Poor document structure or organization",
            "inconsistent_naming": "Inconsistent party names or references",
            "missing_jurisdiction": "Missing or incorrect jurisdiction/venue",
            "insufficient_damages": "Insufficient damages allegations",
        }

    async def validate_draft_complaint(
        self,
        draft_text: str,
        case_id: str,
        custom_thresholds: Optional[Dict[str, float]] = None,
    ) -> ValidationResult:
        """
        Validate a draft complaint against the defendant's cluster

        Args:
            draft_text: Text of the draft complaint
            case_id: Associated case ID
            custom_thresholds: Optional custom validation thresholds

        Returns:
            Comprehensive validation result
        """
        start_time = datetime.now()

        try:
            # Get case information
            if (
                not self.intake_processor
                or case_id not in self.intake_processor.active_cases
            ):
                return ValidationResult(
                    draft_id=self._generate_draft_id(),
                    case_id=case_id,
                    defendant_name="Unknown",
                    validation_timestamp=datetime.now(),
                    overall_score=0.0,
                    similarity_score=0.0,
                    similarity_threshold=0.6,
                    is_valid=False,
                    issues_found=["Case not found in system"],
                )

            case_info = self.intake_processor.active_cases[case_id]
            defendant_name = case_info["defendant_name"]

            # Use custom thresholds or defaults
            thresholds = custom_thresholds or self.default_thresholds

            # Perform cluster validation
            if self.cluster_manager:
                cluster_validation = (
                    await self.cluster_manager.validate_draft_against_cluster(
                        draft_text=draft_text,
                        defendant_name=defendant_name,
                        similarity_threshold=thresholds["similarity_threshold"],
                    )
                )
            else:
                cluster_validation = {
                    "valid": False,
                    "reason": "Cluster manager not available",
                    "max_similarity": 0.0,
                }

            if not cluster_validation["valid"]:
                return ValidationResult(
                    draft_id=self._generate_draft_id(),
                    case_id=case_id,
                    defendant_name=defendant_name,
                    validation_timestamp=datetime.now(),
                    overall_score=0.0,
                    similarity_score=cluster_validation.get("max_similarity", 0.0),
                    similarity_threshold=thresholds["similarity_threshold"],
                    is_valid=False,
                    issues_found=[
                        cluster_validation.get("reason", "Validation failed")
                    ],
                    processing_time=(datetime.now() - start_time).total_seconds(),
                )

            # Perform detailed content analysis
            content_analysis = await self._analyze_draft_content(draft_text, case_info)

            # Calculate overall score
            overall_score = self._calculate_overall_score(
                cluster_validation, content_analysis, thresholds
            )

            # Determine if valid
            is_valid = overall_score >= thresholds["similarity_threshold"]

            # Generate recommendations
            recommendations = self._generate_recommendations(
                cluster_validation, content_analysis, is_valid
            )

            # Get similar documents
            similar_docs = await self._get_similar_documents(draft_text, case_id)

            processing_time = (datetime.now() - start_time).total_seconds()

            # Create validation result
            validation_result = ValidationResult(
                draft_id=self._generate_draft_id(),
                case_id=case_id,
                defendant_name=defendant_name,
                validation_timestamp=datetime.now(),
                overall_score=overall_score,
                similarity_score=cluster_validation.get("max_similarity", 0.0),
                similarity_threshold=thresholds["similarity_threshold"],
                is_valid=is_valid,
                issues_found=content_analysis.get("issues", []),
                recommendations=recommendations,
                similar_documents=similar_docs,
                missing_elements=content_analysis.get("missing_elements", []),
                strength_assessment=content_analysis.get("strength_assessment", {}),
                processing_time=processing_time,
            )

            # Store validation result and draft through unified storage (don't block on this)
            if self.unified_storage:
                try:
                    # Store validation result
                    validation_object_id = await self.store_validation_result(
                        validation_result, draft_text, case_id
                    )
                    if validation_object_id:
                        logger.info(f"Validation result stored with ObjectID: {validation_object_id}")

                    # Store draft complaint
                    draft_object_id = await self.store_draft_complaint(
                        draft_text, case_id, defendant_name,
                        draft_metadata={
                            "validation_score": overall_score,
                            "is_valid": is_valid,
                            "validation_object_id": validation_object_id
                        }
                    )
                    if draft_object_id:
                        logger.info(f"Draft complaint stored with ObjectID: {draft_object_id}")

                except Exception as e:
                    logger.warning(f"Failed to store validation data through unified storage: {e}")

            return validation_result

        except Exception as e:
            logger.error(f"Draft validation failed: {e}")
            return ValidationResult(
                draft_id=self._generate_draft_id(),
                case_id=case_id,
                defendant_name="Unknown",
                validation_timestamp=datetime.now(),
                overall_score=0.0,
                similarity_score=0.0,
                similarity_threshold=0.6,
                is_valid=False,
                issues_found=[f"Validation error: {str(e)}"],
                processing_time=(datetime.now() - start_time).total_seconds(),
            )

    async def _analyze_draft_content(
        self, draft_text: str, case_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze draft content for legal and structural issues"""
        analysis = {
            "issues": [],
            "missing_elements": [],
            "strength_assessment": {},
            "metrics": ValidationMetrics(),
        }

        # Check for required elements
        analysis["missing_elements"] = self._check_required_elements(draft_text)

        # Analyze structure
        structure_issues = self._analyze_structure(draft_text)
        analysis["issues"].extend(structure_issues)

        # Check defendant specificity
        defendant_issues = self._check_defendant_specificity(
            draft_text, case_info["defendant_name"]
        )
        analysis["issues"].extend(defendant_issues)

        # Assess legal strength
        analysis["strength_assessment"] = self._assess_legal_strength(
            draft_text, case_info
        )

        # Calculate content metrics
        analysis["metrics"] = self._calculate_content_metrics(draft_text, case_info)

        return analysis

    def _check_required_elements(self, draft_text: str) -> List[str]:
        """Check for missing required legal elements"""
        missing = []
        text_lower = draft_text.lower()

        element_indicators = {
            "jurisdiction_venue": ["jurisdiction", "venue", "county", "district"],
            "parties_identified": [
                "plaintiff",
                "defendant",
                "petitioner",
                "respondent",
            ],
            "factual_allegations": [
                "alleg",
                "fact",
                "occurred",
                "happened",
                "incident",
            ],
            "legal_claims": ["negligence", "breach", "contract", "tort", "violation"],
            "damages_requested": [
                "damages",
                "compensation",
                "relief",
                "injury",
                "harm",
            ],
            "prayer_for_relief": ["prayer", "relief", "request", "award", "judgment"],
        }

        for element, indicators in element_indicators.items():
            if not any(indicator in text_lower for indicator in indicators):
                missing.append(element)

        return missing

    def _analyze_structure(self, draft_text: str) -> List[str]:
        """Analyze document structure and organization"""
        issues = []

        # Check for numbered paragraphs
        if not any(f"paragraph {i}" in draft_text.lower() for i in range(1, 10)):
            if not any(f"¶ {i}" in draft_text for i in range(1, 10)):
                issues.append("Document lacks numbered paragraphs")

        # Check for proper sections
        required_sections = [
            "introduction",
            "parties",
            "jurisdiction",
            "facts",
            "claims",
            "prayer",
        ]
        found_sections = [
            section for section in required_sections if section in draft_text.lower()
        ]

        if len(found_sections) < 3:
            issues.append("Document lacks proper section organization")

        # Check length
        word_count = len(draft_text.split())
        if word_count < 500:
            issues.append("Document is too short for a comprehensive complaint")
        elif word_count > 10000:
            issues.append("Document is excessively long")

        return issues

    def _check_defendant_specificity(
        self, draft_text: str, defendant_name: str
    ) -> List[str]:
        """Check if complaint is specific to the defendant"""
        issues = []
        text_lower = draft_text.lower()
        defendant_lower = defendant_name.lower()

        # Check for defendant name mentions
        defendant_mentions = text_lower.count(defendant_lower)
        if defendant_mentions < 3:
            issues.append(
                f"Defendant '{defendant_name}' mentioned only {defendant_mentions} times"
            )

        # Check for generic vs specific language
        generic_indicators = [
            "defendant",
            "the company",
            "said defendant",
            "defendant corporation",
        ]
        generic_count = sum(
            text_lower.count(indicator) for indicator in generic_indicators
        )

        if generic_count > defendant_mentions:
            issues.append(
                "Too much generic defendant language, needs more specific references"
            )

        return issues

    def _assess_legal_strength(
        self, draft_text: str, case_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess the legal strength of the complaint"""
        assessment = {
            "factual_detail": 0.0,
            "legal_precision": 0.0,
            "damages_specificity": 0.0,
            "jurisdictional_accuracy": 0.0,
            "overall_strength": 0.0,
        }

        text_lower = draft_text.lower()

        # Assess factual detail
        fact_indicators = [
            "specifically",
            "on or about",
            "at all times",
            "thereafter",
            "hereinafter",
        ]
        assessment["factual_detail"] = min(
            1.0,
            len([ind for ind in fact_indicators if ind in text_lower])
            / len(fact_indicators),
        )

        # Assess legal precision
        legal_indicators = [
            "hereby",
            "pursuant to",
            "in accordance with",
            "as required by",
            "under penalty of",
        ]
        assessment["legal_precision"] = min(
            1.0,
            len([ind for ind in legal_indicators if ind in text_lower])
            / len(legal_indicators),
        )

        # Assess damages specificity
        damage_indicators = [
            "compensatory damages",
            "punitive damages",
            "actual damages",
            "special damages",
            "general damages",
        ]
        assessment["damages_specificity"] = min(
            1.0,
            len([ind for ind in damage_indicators if ind in text_lower])
            / len(damage_indicators),
        )

        # Assess jurisdictional accuracy
        jurisdiction_indicators = [
            "proper venue",
            "jurisdiction",
            "subject matter jurisdiction",
            "personal jurisdiction",
        ]
        assessment["jurisdictional_accuracy"] = min(
            1.0,
            len([ind for ind in jurisdiction_indicators if ind in text_lower])
            / len(jurisdiction_indicators),
        )

        # Calculate overall strength
        assessment["overall_strength"] = sum(assessment.values()) / 4

        return assessment

    def _calculate_content_metrics(
        self, draft_text: str, case_info: Dict[str, Any]
    ) -> ValidationMetrics:
        """Calculate detailed content metrics"""
        metrics = ValidationMetrics()

        # Simple heuristic-based calculations
        # In a real implementation, these would use more sophisticated NLP analysis

        text_length = len(draft_text)
        word_count = len(draft_text.split())

        # Factual similarity (based on text length and detail indicators)
        detail_indicators = [
            "specifically",
            "on or about",
            "at that time",
            "thereafter",
        ]
        metrics.factual_similarity = min(
            1.0,
            len([ind for ind in detail_indicators if ind in draft_text.lower()]) / 5,
        )

        # Legal elements similarity
        legal_indicators = [
            "plaintiff alleges",
            "defendant",
            "negligence",
            "breach",
            "damages",
        ]
        metrics.legal_elements_similarity = min(
            1.0, len([ind for ind in legal_indicators if ind in draft_text.lower()]) / 5
        )

        # Structural similarity
        structure_indicators = [
            "paragraph",
            "wherefore",
            "prayer",
            "respectfully",
            "complaint",
        ]
        metrics.structural_similarity = min(
            1.0,
            len([ind for ind in structure_indicators if ind in draft_text.lower()]) / 5,
        )

        # Language similarity (formal legal language)
        formal_indicators = [
            "hereby",
            "pursuant",
            "hereinafter",
            "aforementioned",
            "forthwith",
        ]
        metrics.language_similarity = min(
            1.0,
            len([ind for ind in formal_indicators if ind in draft_text.lower()]) / 5,
        )

        # Defendant specificity
        defendant_name = case_info.get("defendant_name", "")
        if defendant_name:
            defendant_mentions = draft_text.lower().count(defendant_name.lower())
            metrics.defendant_specificity = min(
                1.0, defendant_mentions / 10
            )  # Expect at least 10 mentions

        # Overall confidence
        metrics.overall_confidence = (
            metrics.factual_similarity
            + metrics.legal_elements_similarity
            + metrics.structural_similarity
            + metrics.language_similarity
            + metrics.defendant_specificity
        ) / 5

        return metrics

    def _calculate_overall_score(
        self,
        cluster_validation: Dict[str, Any],
        content_analysis: Dict[str, Any],
        thresholds: Dict[str, float],
    ) -> float:
        """Calculate overall validation score"""
        try:
            # Get similarity score from cluster validation
            similarity_score = cluster_validation.get("max_similarity", 0.0)

            # Get content metrics
            metrics = content_analysis.get("metrics", ValidationMetrics())

            # Weight different factors
            weights = {
                "similarity": 0.4,
                "factual": 0.2,
                "legal": 0.2,
                "structural": 0.1,
                "language": 0.1,
            }

            overall_score = (
                weights["similarity"] * similarity_score
                + weights["factual"] * metrics.factual_similarity
                + weights["legal"] * metrics.legal_elements_similarity
                + weights["structural"] * metrics.structural_similarity
                + weights["language"] * metrics.language_similarity
            )

            return overall_score

        except Exception as e:
            logger.error(f"Score calculation failed: {e}")
            return 0.0

    def _generate_recommendations(
        self,
        cluster_validation: Dict[str, Any],
        content_analysis: Dict[str, Any],
        is_valid: bool,
    ) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        if not is_valid:
            # Add similarity-based recommendations
            similarity_score = cluster_validation.get("max_similarity", 0.0)
            if similarity_score < 0.4:
                recommendations.append(
                    "Review similar complaints in the database for factual patterns and legal language"
                )
                recommendations.append(
                    "Incorporate more specific details about the defendant's actions"
                )

            # Add content-based recommendations
            missing_elements = content_analysis.get("missing_elements", [])
            if missing_elements:
                recommendations.append(
                    f"Add missing elements: {', '.join(missing_elements)}"
                )

            # Add structural recommendations
            issues = content_analysis.get("issues", [])
            if any("structure" in issue.lower() for issue in issues):
                recommendations.append(
                    "Improve document organization with clear sections and numbered paragraphs"
                )

            # Add defendant-specific recommendations
            if any("defendant" in issue.lower() for issue in issues):
                recommendations.append(
                    "Replace generic defendant references with specific company details"
                )

        # Always provide some general recommendations
        recommendations.extend(
            [
                "Consider adding more specific factual allegations",
                "Review jurisdiction and venue requirements",
                "Ensure all damages are properly pleaded",
            ]
        )

        return recommendations[:5]  # Limit to top 5 recommendations

    async def _get_similar_documents(
        self, draft_text: str, case_id: str
    ) -> List[Dict[str, Any]]:
        """Get similar documents from the cluster"""
        try:
            if (
                not self.intake_processor
                or case_id not in self.intake_processor.active_cases
            ):
                return []

            case_info = self.intake_processor.active_cases[case_id]
            cluster_id = case_info["cluster_id"]

            # Try unified storage search first
            if self.unified_storage:
                try:
                    search_results = await self.unified_storage.search_evidence(
                        query=draft_text[:500],  # Use first 500 chars as search query
                        search_tier="vector"
                    )
                    if search_results:
                        return [
                            {
                                "document_id": result.get("object_id", ""),
                                "similarity_score": result.get("relevance_score", 0.5),
                                "document_type": "stored_evidence",
                                "key_similarities": ["vector_similarity"],
                                "metadata": result.get("metadata", {})
                            }
                            for result in search_results[:5]  # Limit to top 5
                        ]
                except Exception as e:
                    logger.warning(f"Unified storage search failed: {e}")

            # Fallback to placeholder structure
            return [
                {
                    "document_id": "similar_doc_1",
                    "similarity_score": 0.75,
                    "document_type": "plaintiff_complaint",
                    "key_similarities": ["factual_pattern", "legal_elements"],
                }
            ]

        except Exception as e:
            logger.error(f"Failed to get similar documents: {e}")
            return []

    async def store_validation_result(
        self, validation_result: ValidationResult, draft_text: str, case_id: str
    ) -> Optional[str]:
        """
        Store validation result and draft through unified storage

        Args:
            validation_result: The validation result to store
            draft_text: The original draft text
            case_id: Associated case ID

        Returns:
            ObjectID if stored successfully, None otherwise
        """
        if not self.unified_storage:
            logger.warning("Unified storage not available for storing validation results")
            return None

        try:
            # Prepare metadata for storage
            metadata = {
                "case_id": case_id,
                "draft_id": validation_result.draft_id,
                "defendant_name": validation_result.defendant_name,
                "validation_score": validation_result.overall_score,
                "is_valid": validation_result.is_valid,
                "validation_timestamp": validation_result.validation_timestamp.isoformat(),
                "source_phase": "drafting_validation",
                "content_type": "validation_result"
            }

            # Convert validation result to JSON
            validation_data = {
                "validation_result": validation_result.__dict__,
                "draft_text": draft_text,
                "case_id": case_id,
                "processing_time": validation_result.processing_time
            }

            import json
            file_content = json.dumps(validation_data, indent=2, default=str).encode('utf-8')
            filename = f"validation_{validation_result.draft_id}.json"

            # Store through unified storage
            storage_result = await self.unified_storage.store_evidence(
                file_content=file_content,
                filename=filename,
                metadata=metadata,
                source_phase="drafting_validation"
            )

            if storage_result.success:
                logger.info(f"Stored validation result with ObjectID: {storage_result.object_id}")
                return storage_result.object_id
            else:
                logger.error(f"Failed to store validation result: {storage_result.error}")
                return None

        except Exception as e:
            logger.error(f"Failed to store validation result: {e}")
            return None

    async def retrieve_validation_result(self, object_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve validation result from unified storage

        Args:
            object_id: The ObjectID of the stored validation result

        Returns:
            Validation result data if found, None otherwise
        """
        if not self.unified_storage:
            logger.warning("Unified storage not available for retrieving validation results")
            return None

        try:
            evidence_data = await self.unified_storage.get_evidence(object_id=object_id)

            if "error" in evidence_data:
                logger.error(f"Failed to retrieve validation result: {evidence_data['error']}")
                return None

            # Extract validation data from evidence
            if "evidence_data" in evidence_data:
                import json
                validation_json = evidence_data["evidence_data"]
                if isinstance(validation_json, str):
                    validation_data = json.loads(validation_json)
                else:
                    validation_data = validation_json

                return validation_data

            logger.warning("No evidence data found in retrieval result")
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve validation result {object_id}: {e}")
            return None

    async def store_draft_complaint(
        self, draft_text: str, case_id: str, defendant_name: str,
        draft_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Store draft complaint through unified storage

        Args:
            draft_text: The draft complaint text
            case_id: Associated case ID
            defendant_name: Name of the defendant
            draft_metadata: Additional metadata for the draft

        Returns:
            ObjectID if stored successfully, None otherwise
        """
        if not self.unified_storage:
            logger.warning("Unified storage not available for storing draft complaints")
            return None

        try:
            # Prepare metadata for storage
            metadata = {
                "case_id": case_id,
                "defendant_name": defendant_name,
                "source_phase": "drafting",
                "content_type": "draft_complaint",
                "draft_version": draft_metadata.get("version", "1.0") if draft_metadata else "1.0",
                "created_at": datetime.now().isoformat()
            }

            if draft_metadata:
                metadata.update(draft_metadata)

            # Convert draft to bytes
            file_content = draft_text.encode('utf-8')
            filename = f"draft_complaint_{case_id}_{defendant_name.replace(' ', '_')}.txt"

            # Store through unified storage
            storage_result = await self.unified_storage.store_evidence(
                file_content=file_content,
                filename=filename,
                metadata=metadata,
                source_phase="drafting"
            )

            if storage_result.success:
                logger.info(f"Stored draft complaint with ObjectID: {storage_result.object_id}")
                return storage_result.object_id
            else:
                logger.error(f"Failed to store draft complaint: {storage_result.error}")
                return None

        except Exception as e:
            logger.error(f"Failed to store draft complaint: {e}")
            return None

    def _generate_draft_id(self) -> str:
        """Generate unique draft ID"""
        import uuid

        return f"draft_{uuid.uuid4().hex[:8]}"

    async def iterative_improvement(
        self, draft_text: str, case_id: str, max_iterations: int = 3
    ) -> List[ValidationResult]:
        """
        Perform iterative improvement of a draft complaint

        Args:
            draft_text: Initial draft text
            case_id: Associated case ID
            max_iterations: Maximum improvement iterations

        Returns:
            List of validation results showing improvement over time
        """
        results = []
        current_draft = draft_text

        for iteration in range(max_iterations):
            # Validate current draft
            result = await self.validate_draft_complaint(current_draft, case_id)
            results.append(result)

            # If valid or no more iterations, break
            if result.is_valid or iteration == max_iterations - 1:
                break

            # Generate improved draft based on recommendations
            current_draft = await self._improve_draft(current_draft, result)

        return results

    async def _improve_draft(
        self, draft_text: str, validation_result: ValidationResult
    ) -> str:
        """Generate improved draft based on validation results"""
        # This would integrate with an LLM service to improve the draft
        # For now, return the original draft
        logger.info(
            f"Would improve draft based on {len(validation_result.recommendations)} recommendations"
        )
        return draft_text
