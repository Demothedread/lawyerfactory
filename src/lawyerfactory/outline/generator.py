"""
# Script Name: generator.py
# Description: Skeletal Outline Generator - Phase 4 Preproduction Deliverable Generates FRCP-compliant skeletal outlines for legal complaints with section-specific prompts for chained LLM generation, preventing repetition and ensuring comprehensive coverage.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
Skeletal Outline Generator - Phase 4 Preproduction Deliverable
Generates FRCP-compliant skeletal outlines for legal complaints with section-specific prompts
for chained LLM generation, preventing repetition and ensuring comprehensive coverage.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
from typing import Any, Dict, List, Optional

try:
    from ..claims.matrix import ComprehensiveClaimsMatrixIntegration
    from ..kg.enhanced_graph import EnhancedKnowledgeGraph
    from ..phases.phaseA01_intake.evidence_routes import EvidenceAPI
    from ..storage.enhanced_unified_storage_api import get_enhanced_unified_storage_api
except ImportError:
    # Fallback to absolute imports if relative fails
    from lawyerfactory.claims.matrix import ComprehensiveClaimsMatrixIntegration
    from lawyerfactory.kg.graph_api import EnhancedKnowledgeGraph
    from lawyerfactory.phases.phaseA01_intake.evidence_routes import EvidenceAPI
    from lawyerfactory.storage.core.unified_storage_api import get_enhanced_unified_storage_api

logger = logging.getLogger(__name__)


class SectionType(Enum):
    """Types of sections in legal complaints"""

    CAPTION = "caption"
    INTRODUCTION = "introduction"
    JURISDICTION_VENUE = "jurisdiction_venue"
    PARTIES = "parties"
    STATEMENT_OF_FACTS = "statement_of_facts"
    CAUSE_OF_ACTION = "cause_of_action"
    PRAYER_FOR_RELIEF = "prayer_for_relief"
    JURY_DEMAND = "jury_demand"


class PromptType(Enum):
    """Types of prompts for LLM generation"""

    GENERAL_CONTEXT = "general_context"
    SECTION_SPECIFIC = "section_specific"
    ELEMENT_SPECIFIC = "element_specific"
    FACT_INTEGRATION = "fact_integration"
    CITATION_INTEGRATION = "citation_integration"


@dataclass
class SkeletalSection:
    """Individual section of the skeletal outline"""

    section_id: str
    section_type: SectionType
    title: str
    roman_numeral: Optional[str] = None
    subsections: List["SkeletalSection"] = field(default_factory=list)
    prompt_template: str = ""
    context_references: List[str] = field(
        default_factory=list
    )  # IDs of evidence/facts to reference
    legal_authorities: List[str] = field(default_factory=list)
    word_count_target: int = 500
    priority_level: int = 1  # 1=highest, 5=lowest
    dependencies: List[str] = field(default_factory=list)  # Section IDs this depends on
    evidence_mapping: Dict[str, List[str]] = field(default_factory=dict)  # element -> evidence_ids
    fact_mapping: Dict[str, List[str]] = field(default_factory=dict)  # element -> fact_ids

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SkeletalOutline:
    """Complete skeletal outline for legal document generation"""

    outline_id: str
    case_id: str
    document_type: str = "complaint"
    jurisdiction: str = "California"
    sections: List[SkeletalSection] = field(default_factory=list)
    general_prompts: Dict[str, str] = field(default_factory=dict)
    global_context: Dict[str, Any] = field(default_factory=dict)
    evidence_summary: Dict[str, Any] = field(default_factory=dict)
    claims_summary: Dict[str, Any] = field(default_factory=dict)
    estimated_page_count: int = 10
    created_at: datetime = field(default_factory=datetime.now)

    # Unified storage integration
    object_ids: List[str] = field(default_factory=list)
    storage_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SkeletalOutlineGenerator:
    """Generates comprehensive skeletal outlines for legal document production"""

    def __init__(
        self,
        enhanced_kg: EnhancedKnowledgeGraph,
        claims_matrix: ComprehensiveClaimsMatrixIntegration,
        evidence_api: EvidenceAPI,
    ):
        self.kg = enhanced_kg
        self.claims_matrix = claims_matrix
        self.evidence_api = evidence_api

        # Initialize unified storage API
        self.unified_storage = get_unified_storage_api()

        # Roman numeral mapping for sections
        self.roman_numerals = [
            "I",
            "II",
            "III",
            "IV",
            "V",
            "VI",
            "VII",
            "VIII",
            "IX",
            "X",
            "XI",
            "XII",
            "XIII",
            "XIV",
            "XV",
            "XVI",
            "XVII",
            "XVIII",
            "XIX",
            "XX",
        ]

        # Initialize prompt templates
        self.prompt_templates = self._initialize_prompt_templates()

        logger.info("Skeletal Outline Generator initialized")

    def store_outline_results(
        self,
        outline: SkeletalOutline,
        case_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Store skeletal outline results through unified storage pipeline.

        Args:
            outline: Complete skeletal outline
            case_id: Associated case identifier
            metadata: Additional metadata for storage

        Returns:
            Storage results with ObjectIDs
        """
        try:
            stored_results = []
            object_ids = []

            # Convert outline to storable format
            outline_content = self._format_outline_for_storage(outline)

            # Store through unified storage
            storage_result = self.unified_storage.store_evidence(
                file_content=outline_content.encode("utf-8"),
                filename=f"skeletal_outline_{outline.outline_id}.txt",
                metadata={
                    "outline_id": outline.outline_id,
                    "case_id": case_id,
                    "document_type": outline.document_type,
                    "jurisdiction": outline.jurisdiction,
                    "section_count": len(outline.sections),
                    "estimated_page_count": outline.estimated_page_count,
                    "created_at": outline.created_at.isoformat(),
                    **(metadata or {}),
                },
                source_phase="outline_generation",
            )

            if storage_result.success:
                object_ids.append(storage_result.object_id)
                stored_results.append(
                    {
                        "object_id": storage_result.object_id,
                        "outline_id": outline.outline_id,
                        "case_id": case_id,
                        "storage_urls": {
                            "s3": storage_result.s3_url,
                            "evidence": storage_result.evidence_id,
                            "vector": storage_result.vector_ids,
                        },
                    }
                )

                # Store individual sections as separate objects
                for section in outline.sections:
                    section_content = self._format_section_for_storage(section, outline)

                    section_storage = self.unified_storage.store_evidence(
                        file_content=section_content.encode("utf-8"),
                        filename=f"section_{section.section_id}_{outline.outline_id}.txt",
                        metadata={
                            "parent_outline_id": outline.outline_id,
                            "section_id": section.section_id,
                            "section_type": section.section_type.value,
                            "case_id": case_id,
                            "jurisdiction": outline.jurisdiction,
                            "created_at": outline.created_at.isoformat(),
                        },
                        source_phase="outline_generation",
                    )

                    if section_storage.success:
                        object_ids.append(section_storage.object_id)
                        stored_results.append(
                            {
                                "object_id": section_storage.object_id,
                                "section_id": section.section_id,
                                "parent_outline_id": outline.outline_id,
                            }
                        )

            return {
                "success": True,
                "stored_count": len(stored_results),
                "object_ids": object_ids,
                "results": stored_results,
            }

        except Exception as e:
            logger.error(f"Failed to store outline results: {e}")
            return {
                "success": False,
                "error": str(e),
                "stored_count": 0,
                "object_ids": [],
                "results": [],
            }

    def generate_skeletal_outline(self, case_id: str, session_id: str) -> SkeletalOutline:
        """Generate comprehensive skeletal outline from claims matrix and evidence"""
        try:
            # Get case data from various sources
            case_data = self._gather_case_data(case_id, session_id)

            # Create base outline structure
            outline = SkeletalOutline(
                outline_id=f"outline_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                case_id=case_id,
                global_context=case_data["global_context"],
                evidence_summary=case_data["evidence_summary"],
                claims_summary=case_data["claims_summary"],
            )

            # Generate general context prompts
            outline.general_prompts = self._generate_general_prompts(case_data)

            # Build skeletal sections
            outline.sections = self._build_skeletal_sections(case_data)

            # Calculate estimated page count
            outline.estimated_page_count = self._estimate_page_count(outline.sections)

            # Store outline results through unified storage pipeline
            case_id = f"outline_case_{case_id}"
            storage_metadata = {
                "session_id": session_id,
                "generation_timestamp": datetime.now().isoformat(),
                "outline_phase": "skeletal_generation",
                "global_context": case_data.get("global_context", {}),
                "evidence_summary": case_data.get("evidence_summary", {}),
                "claims_summary": case_data.get("claims_summary", {}),
            }

            storage_result = self.store_outline_results(outline, case_id, storage_metadata)

            # Add storage information to the outline object
            if storage_result.get("success"):
                # Add ObjectIDs to the outline for future reference
                outline.object_ids = storage_result.get("object_ids", [])
                outline.storage_metadata = storage_result

                logger.info(
                    f"Outline {outline.outline_id} stored with {storage_result.get('stored_count', 0)} objects"
                )

            logger.info(
                f"Generated skeletal outline {outline.outline_id} with {len(outline.sections)} sections"
            )
            return outline

        except Exception as e:
            logger.exception(f"Failed to generate skeletal outline for case {case_id}: {e}")
            raise

    def _gather_case_data(self, case_id: str, session_id: str) -> Dict[str, Any]:
        """Gather all relevant case data from claims matrix and evidence table"""
        case_data = {
            "global_context": {},
            "evidence_summary": {},
            "claims_summary": {},
            "causes_of_action": [],
            "facts": [],
            "evidence_entries": [],
            "parties": [],
            "jurisdiction": "California",
        }

        try:
            # Get comprehensive analysis from claims matrix
            analysis = self.claims_matrix.generate_attorney_ready_analysis(session_id)
            if analysis:
                case_data["claims_summary"] = {
                    "cause_of_action": analysis.cause_of_action,
                    "jurisdiction": analysis.jurisdiction,
                    "element_breakdowns": {
                        k: asdict(v) for k, v in analysis.element_breakdowns.items()
                    },
                    "case_strength_assessment": analysis.case_strength_assessment,
                    "discovery_recommendations": analysis.discovery_recommendations,
                    "california_authorities": analysis.california_authorities,
                }
                case_data["jurisdiction"] = analysis.jurisdiction
                case_data["causes_of_action"] = [analysis.cause_of_action]

            # Get evidence data
            evidence_data = self.evidence_api.evidence_table.export_to_dict()
            case_data["evidence_summary"] = evidence_data.get("statistics", {})
            case_data["evidence_entries"] = evidence_data.get("evidence_entries", [])
            case_data["facts"] = evidence_data.get("fact_assertions", [])

            # Extract parties from evidence/facts
            case_data["parties"] = self._extract_parties_from_data(case_data)

            # Set global context
            case_data["global_context"] = {
                "case_id": case_id,
                "session_id": session_id,
                "total_evidence_count": len(case_data["evidence_entries"]),
                "total_fact_count": len(case_data["facts"]),
                "primary_cause_of_action": (
                    case_data["causes_of_action"][0] if case_data["causes_of_action"] else "Unknown"
                ),
                "jurisdiction": case_data["jurisdiction"],
            }

        except Exception as e:
            logger.warning(f"Error gathering case data: {e}")

        return case_data

    def _extract_parties_from_data(self, case_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract party information from facts and evidence"""
        parties = []
        party_names = set()

        # Extract from facts
        for fact in case_data.get("facts", []):
            for party in fact.get("parties_involved", []):
                if party not in party_names:
                    parties.append({"name": party, "role": "Unknown"})
                    party_names.add(party)

        # Extract from evidence - look for common legal entity patterns
        for evidence in case_data.get("evidence_entries", []):
            content = evidence.get("content", "").lower()
            # Simple regex patterns for party identification
            plaintiff_patterns = ["plaintiff", "claimant", "petitioner"]
            defendant_patterns = ["defendant", "respondent"]

            for pattern in plaintiff_patterns:
                if pattern in content and "plaintiff" not in [
                    p.get("role", "").lower() for p in parties
                ]:
                    parties.append({"name": "Plaintiff", "role": "Plaintiff"})
                    break

            for pattern in defendant_patterns:
                if pattern in content and "defendant" not in [
                    p.get("role", "").lower() for p in parties
                ]:
                    parties.append({"name": "Defendant", "role": "Defendant"})
                    break

        return parties[:10]  # Limit to 10 parties for complexity management

    def _generate_general_prompts(self, case_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate general context prompts that apply across all sections"""
        return {
            "global_context": f"""
            You are drafting a legal complaint for {case_data['global_context']['primary_cause_of_action']} 
            in {case_data['jurisdiction']}. This case involves {case_data['global_context']['total_fact_count']} 
            key facts supported by {case_data['global_context']['total_evidence_count']} pieces of evidence.
            
            CRITICAL INSTRUCTIONS:
            1. Maintain strict adherence to Federal Rules of Civil Procedure
            2. Use formal legal writing with precise terminology
            3. Reference only facts and evidence specifically provided in context
            4. Avoid repetition across sections - each section should build upon previous ones
            5. Use proper Bluebook citation format for all authorities
            6. Ensure each element of the cause of action is adequately pled to survive Rule 12(b)(6) motion
            """,
            "anti_repetition": """
            ANTI-REPETITION PROTOCOL:
            - Before writing, review what has been established in prior sections
            - Do not re-state facts already presented in Statement of Facts
            - Reference prior sections using appropriate citations (e.g., "As alleged in paragraph X")
            - Each cause of action section should focus only on new legal theories and elements
            - Build upon rather than repeat previously established factual allegations
            """,
            "legal_standard": f"""
            LEGAL STANDARDS FOR {case_data['jurisdiction']}:
            - Apply California state law unless federal law is specified
            - Use California jury instructions where applicable
            - Cite controlling California appellate and Supreme Court cases
            - Follow California Code of Civil Procedure for procedural requirements
            - Ensure compliance with California statutes of limitations
            """,
        }

    def _build_skeletal_sections(self, case_data: Dict[str, Any]) -> List[SkeletalSection]:
        """Build all skeletal sections with appropriate prompts and mappings"""
        sections = []

        # 1. Case Caption
        sections.append(self._build_caption_section(case_data))

        # 2. Introduction
        sections.append(self._build_introduction_section(case_data))

        # 3. Jurisdiction and Venue
        sections.append(self._build_jurisdiction_venue_section(case_data))

        # 4. Parties
        sections.append(self._build_parties_section(case_data))

        # 5. Statement of Facts
        sections.append(self._build_statement_of_facts_section(case_data))

        # 6. Causes of Action (can be multiple)
        cause_sections = self._build_causes_of_action_sections(case_data)
        sections.extend(cause_sections)

        # 7. Prayer for Relief
        sections.append(self._build_prayer_for_relief_section(case_data))

        # 8. Jury Demand
        sections.append(self._build_jury_demand_section(case_data))

        return sections

    def _build_caption_section(self, case_data: Dict[str, Any]) -> SkeletalSection:
        """Build case caption section"""
        return SkeletalSection(
            section_id="caption",
            section_type=SectionType.CAPTION,
            title="CASE CAPTION",
            prompt_template=self.prompt_templates["caption"].format(
                parties=json.dumps(case_data.get("parties", []), indent=2),
                jurisdiction=case_data["jurisdiction"],
            ),
            word_count_target=100,
            priority_level=1,
        )

    def _build_introduction_section(self, case_data: Dict[str, Any]) -> SkeletalSection:
        """Build introduction section"""
        return SkeletalSection(
            section_id="introduction",
            section_type=SectionType.INTRODUCTION,
            title="INTRODUCTION",
            roman_numeral="I",
            prompt_template=self.prompt_templates["introduction"].format(
                cause_of_action=case_data["global_context"]["primary_cause_of_action"],
                jurisdiction=case_data["jurisdiction"],
                party_count=len(case_data.get("parties", [])),
            ),
            word_count_target=200,
            priority_level=1,
            dependencies=["caption"],
        )

    def _build_jurisdiction_venue_section(self, case_data: Dict[str, Any]) -> SkeletalSection:
        """Build jurisdiction and venue section"""
        return SkeletalSection(
            section_id="jurisdiction_venue",
            section_type=SectionType.JURISDICTION_VENUE,
            title="JURISDICTION AND VENUE",
            roman_numeral="II",
            prompt_template=self.prompt_templates["jurisdiction_venue"].format(
                jurisdiction=case_data["jurisdiction"],
                cause_of_action=case_data["global_context"]["primary_cause_of_action"],
            ),
            legal_authorities=[
                "28 U.S.C. § 1331 (federal question jurisdiction)",
                "28 U.S.C. § 1332 (diversity jurisdiction)",
                "28 U.S.C. § 1391 (venue)",
            ],
            word_count_target=300,
            priority_level=1,
            dependencies=["introduction"],
        )

    def _build_parties_section(self, case_data: Dict[str, Any]) -> SkeletalSection:
        """Build parties section"""
        return SkeletalSection(
            section_id="parties",
            section_type=SectionType.PARTIES,
            title="PARTIES",
            roman_numeral="III",
            prompt_template=self.prompt_templates["parties"].format(
                parties=json.dumps(case_data.get("parties", []), indent=2),
                jurisdiction=case_data["jurisdiction"],
            ),
            word_count_target=400,
            priority_level=1,
            dependencies=["jurisdiction_venue"],
        )

    def _build_statement_of_facts_section(self, case_data: Dict[str, Any]) -> SkeletalSection:
        """Build statement of facts section with evidence mapping"""
        # Map facts to evidence
        fact_mapping = {}
        evidence_mapping = {}

        for i, fact in enumerate(case_data.get("facts", [])):
            fact_key = f"fact_{i+1}"
            fact_mapping[fact_key] = [fact.get("fact_id", fact_key)]
            # Link related evidence
            evidence_mapping[fact_key] = [
                ev.get("evidence_id", "")
                for ev in case_data.get("evidence_entries", [])
                if any(
                    term in ev.get("content", "").lower()
                    for term in fact.get("fact_text", "").lower().split()[:3]
                )
            ][
                :3
            ]  # Limit to 3 most relevant evidence pieces per fact

        return SkeletalSection(
            section_id="statement_of_facts",
            section_type=SectionType.STATEMENT_OF_FACTS,
            title="STATEMENT OF FACTS",
            roman_numeral="IV",
            prompt_template=self.prompt_templates["statement_of_facts"].format(
                facts=json.dumps(case_data.get("facts", []), indent=2),
                evidence_count=len(case_data.get("evidence_entries", [])),
            ),
            fact_mapping=fact_mapping,
            evidence_mapping=evidence_mapping,
            word_count_target=1500,
            priority_level=1,
            dependencies=["parties"],
        )

    def _build_causes_of_action_sections(self, case_data: Dict[str, Any]) -> List[SkeletalSection]:
        """Build cause of action sections with element-specific prompts"""
        sections = []
        roman_start = 5  # Start at V after Statement of Facts

        # Get element breakdowns from claims matrix
        claims_summary = case_data.get("claims_summary", {})
        element_breakdowns = claims_summary.get("element_breakdowns", {})

        primary_coa = case_data["global_context"]["primary_cause_of_action"]

        # Create main cause of action section
        coa_section = SkeletalSection(
            section_id=f"coa_{primary_coa.lower().replace(' ', '_')}",
            section_type=SectionType.CAUSE_OF_ACTION,
            title=f"FIRST CAUSE OF ACTION: {primary_coa.upper()}",
            roman_numeral=self.roman_numerals[roman_start - 1],
            word_count_target=2000,
            priority_level=1,
            dependencies=["statement_of_facts"],
        )

        # Build element-specific subsections
        for element_name, breakdown in element_breakdowns.items():
            element_section = self._build_element_subsection(
                element_name, breakdown, case_data, coa_section.section_id
            )
            coa_section.subsections.append(element_section)

        # Set main COA prompt
        coa_section.prompt_template = self.prompt_templates["cause_of_action"].format(
            cause_of_action=primary_coa,
            elements=list(element_breakdowns.keys()),
            jurisdiction=case_data["jurisdiction"],
            element_count=len(element_breakdowns),
        )

        sections.append(coa_section)
        return sections

    def _build_element_subsection(
        self,
        element_name: str,
        breakdown: Dict[str, Any],
        case_data: Dict[str, Any],
        parent_id: str,
    ) -> SkeletalSection:
        """Build subsection for specific legal element"""
        # Map relevant facts and evidence to this element
        relevant_facts = self._find_relevant_facts_for_element(element_name, case_data)
        relevant_evidence = self._find_relevant_evidence_for_element(element_name, case_data)

        return SkeletalSection(
            section_id=f"{parent_id}_{element_name.lower().replace(' ', '_')}",
            section_type=SectionType.CAUSE_OF_ACTION,
            title=f"Element: {element_name}",
            prompt_template=self.prompt_templates["element_specific"].format(
                element_name=element_name,
                element_definition=breakdown.get("primary_definition", ""),
                authority_citations=breakdown.get("authority_citations", []),
                relevant_facts=relevant_facts,
                relevant_evidence=relevant_evidence,
                burden_of_proof=breakdown.get("burden_of_proof", "preponderance of evidence"),
            ),
            fact_mapping={element_name: [f["fact_id"] for f in relevant_facts]},
            evidence_mapping={element_name: [e["evidence_id"] for e in relevant_evidence]},
            legal_authorities=breakdown.get("authority_citations", []),
            word_count_target=500,
            priority_level=2,
            dependencies=[parent_id],
        )

    def _find_relevant_facts_for_element(
        self, element_name: str, case_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find facts most relevant to specific legal element"""
        facts = case_data.get("facts", [])
        element_keywords = self._get_element_keywords(element_name)

        relevant_facts = []
        for fact in facts:
            fact_text = fact.get("fact_text", "").lower()
            relevance_score = sum(1 for keyword in element_keywords if keyword in fact_text)
            if relevance_score > 0:
                fact_copy = fact.copy()
                fact_copy["relevance_score"] = relevance_score
                relevant_facts.append(fact_copy)

        # Sort by relevance and return top 5
        relevant_facts.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return relevant_facts[:5]

    def _find_relevant_evidence_for_element(
        self, element_name: str, case_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find evidence most relevant to specific legal element"""
        evidence_entries = case_data.get("evidence_entries", [])
        element_keywords = self._get_element_keywords(element_name)

        relevant_evidence = []
        for evidence in evidence_entries:
            content = evidence.get("content", "").lower()
            relevance_score = sum(1 for keyword in element_keywords if keyword in content)
            if relevance_score > 0:
                evidence_copy = evidence.copy()
                evidence_copy["relevance_score"] = relevance_score
                relevant_evidence.append(evidence_copy)

        # Sort by relevance and return top 3
        relevant_evidence.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return relevant_evidence[:3]

    def _get_element_keywords(self, element_name: str) -> List[str]:
        """Get keywords associated with legal elements"""
        keyword_map = {
            "duty": ["duty", "obligation", "standard", "care", "responsible"],
            "breach": ["breach", "violation", "failed", "negligent", "breach"],
            "causation": ["caused", "result", "because", "due to", "led to"],
            "damages": ["damages", "harm", "injury", "loss", "suffered"],
            "intent": ["intent", "intended", "purposeful", "deliberate", "knowing"],
            "contract": ["contract", "agreement", "promise", "terms", "performance"],
            "reliance": ["relied", "reliance", "depended", "trusted", "based on"],
        }

        element_key = element_name.lower()
        for key, keywords in keyword_map.items():
            if key in element_key:
                return keywords

        # Default keywords
        return element_name.lower().split()

    def _build_prayer_for_relief_section(self, case_data: Dict[str, Any]) -> SkeletalSection:
        """Build prayer for relief section"""
        return SkeletalSection(
            section_id="prayer_for_relief",
            section_type=SectionType.PRAYER_FOR_RELIEF,
            title="PRAYER FOR RELIEF",
            roman_numeral="VI",  # Adjust based on number of COAs
            prompt_template=self.prompt_templates["prayer_for_relief"].format(
                cause_of_action=case_data["global_context"]["primary_cause_of_action"],
                jurisdiction=case_data["jurisdiction"],
            ),
            word_count_target=500,
            priority_level=1,
            dependencies=[
                "coa_"
                + case_data["global_context"]["primary_cause_of_action"].lower().replace(" ", "_")
            ],
        )

    def _build_jury_demand_section(self, case_data: Dict[str, Any]) -> SkeletalSection:
        """Build jury demand section"""
        return SkeletalSection(
            section_id="jury_demand",
            section_type=SectionType.JURY_DEMAND,
            title="DEMAND FOR JURY TRIAL",
            prompt_template=self.prompt_templates["jury_demand"],
            word_count_target=100,
            priority_level=3,
            dependencies=["prayer_for_relief"],
        )

    def _estimate_page_count(self, sections: List[SkeletalSection]) -> int:
        """Estimate total page count based on word count targets"""
        total_words = sum(section.word_count_target for section in sections)
        # Add subsection word counts
        for section in sections:
            total_words += sum(sub.word_count_target for sub in section.subsections)

        # Estimate 250 words per page for legal documents
        return max(10, int(total_words / 250))

    def _initialize_prompt_templates(self) -> Dict[str, str]:
        """Initialize all prompt templates for section generation"""
        return {
            "caption": """
            Generate a proper case caption for a {jurisdiction} legal complaint with the following parties:
            {parties}
            
            Include:
            - Proper court designation
            - Plaintiff(s) and Defendant(s) names
            - Case number placeholder
            - Document title "COMPLAINT"
            """,
            "introduction": """
            Draft an introduction paragraph that:
            1. Identifies this as a {cause_of_action} action
            2. States the jurisdiction ({jurisdiction})
            3. Briefly identifies the {party_count} parties
            4. Provides a one-sentence summary of the claim
            5. States the relief sought in general terms
            
            Keep to exactly one paragraph. Do not detail facts here.
            """,
            "jurisdiction_venue": """
            Draft jurisdiction and venue allegations for {jurisdiction} regarding {cause_of_action}:
            
            Include separate numbered paragraphs for:
            1. Subject matter jurisdiction (federal question/diversity)
            2. Personal jurisdiction over defendants
            3. Proper venue
            4. Amount in controversy if required
            
            Cite relevant statutes and be specific about jurisdictional basis.
            """,
            "parties": """
            Draft party allegations for the following parties in {jurisdiction}:
            {parties}
            
            For each party include:
            - Full legal name and entity type
            - State of incorporation/residence
            - Principal place of business
            - Basis for personal jurisdiction
            
            Use separate numbered paragraphs for each party.
            """,
            "statement_of_facts": """
            Draft a comprehensive Statement of Facts using these {evidence_count} pieces of evidence and facts:
            {facts}
            
            Requirements:
            1. Use numbered paragraphs
            2. Present facts chronologically
            3. Include specific dates, locations, and amounts where available
            4. Reference supporting evidence in each paragraph
            5. Avoid legal conclusions - state facts only
            6. Ensure each fact supports elements of the claims
            
            Target 30-40 numbered paragraphs for comprehensive coverage.
            """,
            "cause_of_action": """
            Draft the {cause_of_action} cause of action with {element_count} elements for {jurisdiction}:
            Elements to address: {elements}
            
            Structure:
            1. Incorporate all prior allegations by reference
            2. State the cause of action clearly
            3. Address each element in separate subsections
            4. Conclude with damages paragraph
            
            Each element subsection will be generated separately - focus on overall structure here.
            """,
            "element_specific": """
            Draft allegations for the {element_name} element:
            
            Element Definition: {element_definition}
            Authorities: {authority_citations}
            Burden of Proof: {burden_of_proof}
            
            Relevant Facts: {relevant_facts}
            Supporting Evidence: {relevant_evidence}
            
            Requirements:
            1. State the element clearly
            2. Allege specific facts satisfying this element
            3. Reference supporting evidence
            4. Use numbered paragraphs
            5. Ensure allegations are sufficient to survive 12(b)(6) motion
            """,
            "prayer_for_relief": """
            Draft Prayer for Relief for {cause_of_action} action in {jurisdiction}:
            
            Include:
            1. Compensatory damages
            2. Punitive damages (if applicable)
            3. Injunctive relief (if applicable)
            4. Attorney's fees and costs
            5. Pre and post-judgment interest
            6. Such other relief as the Court deems just and proper
            
            Use "WHEREFORE" introduction and lettered subsections.
            """,
            "jury_demand": """
            Draft a standard jury demand:
            "Plaintiff demands trial by jury on all issues so triable as a matter of right."
            
            Include proper signature block with attorney information.
            """,
        }

    def _format_outline_for_storage(self, outline: SkeletalOutline) -> str:
        """
        Format skeletal outline for storage as text content.

        Args:
            outline: Complete skeletal outline

        Returns:
            Formatted text content
        """
        content = f"""
SKELETAL OUTLINE FOR LEGAL COMPLAINT
====================================

Outline ID: {outline.outline_id}
Case ID: {outline.case_id}
Document Type: {outline.document_type}
Jurisdiction: {outline.jurisdiction}
Estimated Page Count: {outline.estimated_page_count}
Created: {outline.created_at.strftime('%Y-%m-%d %H:%M:%S')}

GLOBAL CONTEXT
==============
{json.dumps(outline.global_context, indent=2)}

GENERAL PROMPTS
===============
"""
        for prompt_name, prompt_text in outline.general_prompts.items():
            content += f"\n{prompt_name.upper()}:\n{prompt_text}\n"

        content += f"""

SECTION OUTLINE
===============
"""
        for section in outline.sections:
            content += f"\n{section.roman_numeral or ''} {section.title}\n"
            content += f"Section ID: {section.section_id}\n"
            content += f"Type: {section.section_type.value}\n"
            content += f"Word Count Target: {section.word_count_target}\n"
            content += f"Priority: {section.priority_level}\n"
            if section.dependencies:
                content += f"Dependencies: {', '.join(section.dependencies)}\n"
            content += f"Prompt Template:\n{section.prompt_template}\n"

            if section.subsections:
                content += "Subsections:\n"
                for subsection in section.subsections:
                    content += f"  - {subsection.title} ({subsection.word_count_target} words)\n"

        return content.strip()

    def _format_section_for_storage(
        self, section: SkeletalSection, outline: SkeletalOutline
    ) -> str:
        """
        Format individual section for storage.

        Args:
            section: Section to format
            outline: Parent outline for context

        Returns:
            Formatted text content for section
        """
        content = f"""
SECTION: {section.title.upper()}
{'=' * (len(section.title) + 9)}

Section ID: {section.section_id}
Type: {section.section_type.value}
Roman Numeral: {section.roman_numeral or 'N/A'}
Word Count Target: {section.word_count_target}
Priority Level: {section.priority_level}

Parent Outline: {outline.outline_id}
Case ID: {outline.case_id}
Jurisdiction: {outline.jurisdiction}

DEPENDENCIES
============
{', '.join(section.dependencies) if section.dependencies else 'None'}

CONTEXT REFERENCES
==================
{', '.join(section.context_references) if section.context_references else 'None'}

LEGAL AUTHORITIES
=================
{chr(10).join(f"• {authority}" for authority in section.legal_authorities)}

EVIDENCE MAPPING
================
"""
        for element, evidence_ids in section.evidence_mapping.items():
            content += f"{element}: {', '.join(evidence_ids)}\n"

        content += f"""

FACT MAPPING
============
"""
        for element, fact_ids in section.fact_mapping.items():
            content += f"{element}: {', '.join(fact_ids)}\n"

        content += f"""

PROMPT TEMPLATE
===============
{section.prompt_template}
"""

        if section.subsections:
            content += f"""

SUBSECTIONS
===========
"""
            for subsection in section.subsections:
                content += f"• {subsection.title} ({subsection.word_count_target} words)\n"
                content += f"  ID: {subsection.section_id}\n"
                content += f"  Dependencies: {', '.join(subsection.dependencies) if subsection.dependencies else 'None'}\n\n"

        return content.strip()


def test_skeletal_outline_generator():
    """Test function for skeletal outline generator"""
    try:
        # Mock data for testing
        from lawyerfactory.claims.matrix import ComprehensiveClaimsMatrixIntegration
        from lawyerfactory.kg.graph_api import EnhancedKnowledgeGraph
        from lawyerfactory.phases.phaseA01_intake.evidence_routes import EvidenceAPI
        from lawyerfactory.storage.core.unified_storage_api import (
            get_enhanced_unified_storage_api,
        )

        # Initialize components
        kg = EnhancedKnowledgeGraph()
        claims_matrix = ComprehensiveClaimsMatrixIntegration(kg)
        evidence_api = EvidenceAPI()

        # Create generator
        generator = SkeletalOutlineGenerator(kg, claims_matrix, evidence_api)

        # Test generation
        outline = generator.generate_skeletal_outline("test_case_001", "test_session_001")

        print(f"Generated outline with {len(outline.sections)} sections")
        print(f"Estimated page count: {outline.estimated_page_count}")

        for section in outline.sections:
            print(f"- {section.title} ({section.word_count_target} words)")
            for subsection in section.subsections:
                print(f"  - {subsection.title} ({subsection.word_count_target} words)")

        return outline

    except Exception as e:
        print(f"Test failed: {e}")
        return None


if __name__ == "__main__":
    test_skeletal_outline_generator()
