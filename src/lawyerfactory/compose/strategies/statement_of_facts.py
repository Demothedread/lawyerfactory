"""
# Script Name: statement_of_facts.py
# Description: Professional Statement of Facts Generation Engine Produces litigation-ready Statement of Facts documents from knowledge graph data with proper legal formatting, Bluebook citations, and FRCP compliance.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: null
Professional Statement of Facts Generation Engine
Produces litigation-ready Statement of Facts documents from knowledge graph data
with proper legal formatting, Bluebook citations, and FRCP compliance.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from knowledge_graph_integration import KnowledgeGraphIntegration

logger = logging.getLogger(__name__)


class FactCategory(Enum):
    """Categories for organizing facts in Statement of Facts"""
    BACKGROUND = "background"
    MATERIAL = "material"
    DISPUTED = "disputed"
    PROCEDURAL = "procedural"
    DAMAGES = "damages"


class CitationFormat(Enum):
    """Supported citation formats"""
    BLUEBOOK = "bluebook"
    RECORD = "record"
    EXHIBIT = "exhibit"


@dataclass
class LegalFact:
    """Structured representation of a legal fact"""
    id: str
    text: str
    category: FactCategory
    confidence: float
    source_documents: List[str] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)
    date: Optional[str] = None
    is_disputed: bool = False
    legal_significance: str = ""
    citation: Optional[str] = None
    verification_status: str = "pending"  # pending, verified, disputed
    

@dataclass
class StatementSection:
    """Section of Statement of Facts"""
    title: str
    facts: List[LegalFact]
    introduction: str = ""
    conclusion: str = ""
    subsections: List['StatementSection'] = field(default_factory=list)


class StatementOfFactsGenerator:
    """Professional Statement of Facts generation engine"""
    
    def __init__(self, kg_integration: Optional[KnowledgeGraphIntegration] = None):
        self.kg_integration = kg_integration or KnowledgeGraphIntegration()
        self.citation_format = CitationFormat.BLUEBOOK
        self.templates = self._load_templates()
    
    def generate(self, case_data: Dict[str, Any], facts_matrix: Dict[str, Any]) -> str:
        """
        Generate Statement of Facts from case data and facts matrix.
        
        This is the primary API method matching the documented interface.
        
        Args:
            case_data: Dictionary containing case information
            facts_matrix: Canonical facts matrix from FactsMatrixAdapter
            
        Returns:
            Generated Statement of Facts as a string
        """
        logger.info("Generating Statement of Facts from provided facts matrix")
        
        try:
            # Normalize the facts matrix to ensure consistent structure
            normalized_facts_matrix = self._normalize_facts_matrix(facts_matrix)
            
            # Structure legal facts
            structured_facts = self._structure_legal_facts(normalized_facts_matrix)
            
            # Organize facts into Statement of Facts sections
            statement_sections = self._organize_statement_sections(structured_facts, case_data)
            
            # Generate professional document
            document = self._generate_professional_document(statement_sections, case_data)
            
            logger.info(f"Statement of Facts generated: {len(document.split())} words")
            return document
            
        except Exception as e:
            logger.exception(f"Failed to generate Statement of Facts: {e}")
    def generate_from_intake_data(self, intake_data: Dict[str, Any]) -> str:
        """
        Generate Statement of Facts directly from intake data.

        This method integrates with the intake processor to generate
        professional Statement of Facts documents.

        Args:
            intake_data: Processed intake data from IntakeProcessor

        Returns:
            Generated Statement of Facts as a string
        """
        logger.info("Generating Statement of Facts from intake data")

        try:
            # Create facts matrix from intake data
            facts_matrix = self._create_facts_matrix_from_intake(intake_data)

            # Create case data from intake
            case_data = self._create_case_data_from_intake(intake_data)

            # Use existing generate method
            return self.generate(case_data, facts_matrix)

        except Exception as e:
            logger.exception(f"Failed to generate Statement of Facts from intake data: {e}")
            return f"Error generating Statement of Facts: {str(e)}"

    def _create_facts_matrix_from_intake(self, intake_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create facts matrix from intake data"""
        return {
            "undisputed_facts": [
                f"Plaintiff {intake_data.get('client_name', 'Unknown')} is an individual residing in {intake_data.get('client_address', 'Unknown Location')}.",
                f"Defendant {intake_data.get('opposing_party_names', 'Unknown')} is the party against whom this action is brought.",
                f"The events giving rise to this action occurred in {intake_data.get('events_location', 'Unknown Location')} during {intake_data.get('events_date', 'Unknown Time')}.",
                f"The nature of the agreement between the parties was {intake_data.get('agreement_type', 'unknown').lower()}.",
                f"Plaintiff seeks damages in the amount of ${intake_data.get('claim_amount', 0):,}.",
                f"The specific claim is: {intake_data.get('claim_description', 'As described in the complaint')}."
            ],
            "disputed_facts": [
                # These would be filled in during litigation
                "Defendant disputes the material allegations contained herein and will provide its affirmative defenses in its Answer."
            ],
            "procedural_facts": [
                f"This case is properly filed in {intake_data.get('jurisdiction', 'the appropriate jurisdiction')}.",
                f"Venue is proper in {intake_data.get('venue', 'the designated venue')} because the events occurred here.",
                f"This Court has both subject matter and personal jurisdiction over the parties and claims."
            ],
            "case_metadata": {
                "case_name": intake_data.get("case_name", "Plaintiff v. Defendant"),
                "case_description": intake_data.get("case_description", ""),
                "jurisdiction": intake_data.get("jurisdiction", ""),
                "venue": intake_data.get("venue", ""),
                "court_type": intake_data.get("court_type", ""),
                "client_name": intake_data.get("client_name", ""),
                "client_address": intake_data.get("client_address", ""),
                "opposing_party_names": intake_data.get("opposing_party_names", ""),
                "claim_amount": intake_data.get("claim_amount", 0),
                "causes_of_action": intake_data.get("causes_of_action", []),
                "session_id": intake_data.get("session_id", "")
            },
            "evidence_references": {
                "has_evidence": intake_data.get("has_evidence", "no"),
                "has_witnesses": intake_data.get("has_witnesses", "no"),
                "has_draft": intake_data.get("has_draft", "no")
            },
            "key_events": [
                {
                    "date": intake_data.get("events_date", "Unknown"),
                    "description": f"Primary events occurred in {intake_data.get('events_location', 'Unknown Location')}",
                    "location": intake_data.get("events_location", "Unknown Location")
                }
            ],
            "background_context": [
                f"Client contact information: {intake_data.get('client_phone', 'Not provided')} / {intake_data.get('client_email', 'Not provided')}",
                f"Opposing party address: {intake_data.get('opposing_party_address', 'Not provided')}"
            ],
            "damages_claims": [
                {
                    "amount": intake_data.get("claim_amount", 0),
                    "description": intake_data.get("claim_description", "General damages"),
                    "type": "general_damages"
                }
            ] if intake_data.get("claim_amount", 0) > 0 else []
        }

    def _create_case_data_from_intake(self, intake_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create case data structure from intake data"""
        return {
            "case_name": intake_data.get("case_name", "Plaintiff v. Defendant"),
            "plaintiff": intake_data.get("client_name", "Plaintiff"),
            "defendant": intake_data.get("opposing_party_names", "Defendant"),
            "court_name": f"{intake_data.get('venue', 'Superior Court')}",
            "case_number": "To Be Assigned",
            "attorney_name": "Attorney Name",
            "attorney_title": "Counsel for Plaintiff",
            "bar_number": "State Bar No. XXXXXX",
            "document_purpose": "Plaintiff's Complaint",
            "jurisdiction": intake_data.get("jurisdiction", ""),
            "filing_date": datetime.now().strftime("%B %d, %Y")
        }
            return f"Error generating Statement of Facts: {str(e)}"
    
    def normalize_facts_matrix(self, facts_matrix: Dict[str, Any]) -> Dict[str, Any]:
        """
        Public method to normalize facts matrix structure.
        
        This method is exposed to allow external validation of facts matrix format.
        
        Args:
            facts_matrix: Input facts matrix to normalize
            
        Returns:
            Normalized facts matrix with safe defaults
        """
        return self._normalize_facts_matrix(facts_matrix)
        
    def _load_templates(self) -> Dict[str, str]:
        """Load professional legal document templates"""
        return {
            'document_header': """STATEMENT OF FACTS

{case_caption}

TO THE HONORABLE COURT:

{party_plaintiff}, by and through undersigned counsel, respectfully submits this Statement of Facts in support of {document_purpose}.

""",
            
            'section_introduction': """
{section_number}. {section_title}

{introduction_text}
""",
            
            'fact_paragraph': """{paragraph_number}. {fact_text}{citation}""",
            
            'disputed_fact': """{paragraph_number}. {fact_text}{citation} {party_defendant} disputes {dispute_description}.""",
            
            'conclusion': """
CONCLUSION

Based on the foregoing facts, {conclusion_statement}

Respectfully submitted,

_________________________
{attorney_name}
{attorney_title}
{bar_number}
Attorney for {client_name}

"""
        }
    
    def _normalize_facts_matrix(self, facts_matrix: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize facts_matrix to ensure consistent structure and handle missing fields gracefully.
        This function provides safe defaults and validates the input structure.
        """
        logger.debug("Normalizing facts_matrix structure")
        
        # Default structure for facts_matrix
        normalized = {
            "undisputed_facts": [],
            "disputed_facts": [],
            "procedural_facts": [],
            "case_metadata": {},
            "evidence_references": {},
            # Additional fields that might be present
            "key_events": [],
            "background_context": [],
            "damages_claims": []
        }
        
        if not isinstance(facts_matrix, dict):
            logger.warning(f"facts_matrix is not a dictionary, got {type(facts_matrix)}. Using defaults.")
            return normalized
        
        # Safely extract each field with defaults
        for key in normalized.keys():
            if key in facts_matrix:
                value = facts_matrix[key]
                if key in ["undisputed_facts", "disputed_facts", "procedural_facts", "key_events", "background_context", "damages_claims"]:
                    # Ensure lists
                    if isinstance(value, list):
                        normalized[key] = value
                    elif isinstance(value, str) and value.strip():
                        normalized[key] = [value]
                    elif value is not None:
                        logger.warning(f"Expected list for {key}, got {type(value)}. Converting to list.")
                        normalized[key] = [str(value)] if value else []
                elif key in ["case_metadata", "evidence_references"]:
                    # Ensure dictionaries
                    if isinstance(value, dict):
                        normalized[key] = value
                    else:
                        logger.warning(f"Expected dict for {key}, got {type(value)}. Using empty dict.")
                        normalized[key] = {}
                else:
                    normalized[key] = value
            else:
                logger.debug(f"Missing field '{key}' in facts_matrix, using default")
        
        # Log normalization results
        total_facts = (len(normalized["undisputed_facts"]) +
                      len(normalized["disputed_facts"]) +
                      len(normalized["procedural_facts"]) +
                      len(normalized.get("key_events", [])) +
                      len(normalized.get("background_context", [])) +
                      len(normalized.get("damages_claims", [])))
        
        logger.info(f"Facts matrix normalized: {total_facts} total facts across all categories")
        return normalized

    def generate_statement_of_facts(self, session_id: str,
                                  case_data: Dict[str, Any],
                                  options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate complete Statement of Facts document"""
        logger.info(f"Generating Statement of Facts for session {session_id}")
        logger.debug(f"Case data keys: {list(case_data.keys()) if case_data else 'None'}")
        logger.debug(f"Options: {options}")
        
        try:
            # Get processed facts from knowledge graph
            logger.debug("Fetching facts from knowledge graph integration")
            facts_data = self.kg_integration.generate_facts_matrix_and_statement(session_id)
            
            if not facts_data:
                logger.error("No facts data returned from knowledge graph integration")
                raise ValueError("No facts data available for statement generation")
            
            if 'facts_matrix' not in facts_data:
                logger.error(f"No facts_matrix in facts_data. Available keys: {list(facts_data.keys())}")
                raise ValueError("No facts matrix available for statement generation")
            
            logger.debug(f"Raw facts_matrix keys: {list(facts_data['facts_matrix'].keys()) if isinstance(facts_data['facts_matrix'], dict) else 'Not a dict'}")
            
            # Normalize facts matrix to handle data shape variations
            normalized_facts_matrix = self._normalize_facts_matrix(facts_data['facts_matrix'])
            
            # Structure legal facts
            logger.debug("Structuring legal facts from normalized matrix")
            structured_facts = self._structure_legal_facts(normalized_facts_matrix)
            
            # Organize facts into Statement of Facts sections
            statement_sections = self._organize_statement_sections(structured_facts, case_data)
            
            # Generate professional document
            document = self._generate_professional_document(statement_sections, case_data)
            
            # Create verification report
            verification_report = self._create_verification_report(structured_facts)
            
            # Generate attorney review points
            review_points = self._identify_review_requirements(structured_facts, facts_data)
            
            result = {
                'session_id': session_id,
                'generation_timestamp': datetime.now().isoformat(),
                'document': {
                    'content': document,
                    'sections': [self._section_to_dict(s) for s in statement_sections],
                    'word_count': len(document.split()),
                    'paragraph_count': len([p for p in document.split('\n') if p.strip() and p.strip()[0].isdigit()])
                },
                'verification_report': verification_report,
                'attorney_review_points': review_points,
                'export_formats': self._generate_export_formats(document, case_data),
                'quality_metrics': self._assess_document_quality(document, structured_facts)
            }
            
            logger.info(f"Statement of Facts generated: {result['document']['word_count']} words, {result['document']['paragraph_count']} paragraphs")
            return result
            
        except Exception as e:
            logger.exception(f"Failed to generate Statement of Facts for session {session_id}: {e}")
            return {
                'session_id': session_id,
                'error': str(e),
                'generation_timestamp': datetime.now().isoformat(),
                'success': False
            }
    
    def _structure_legal_facts(self, facts_matrix: Dict[str, Any]) -> List[LegalFact]:
        """Structure raw facts into legal fact objects with robust error handling"""
        logger.debug("Starting to structure legal facts")
        structured_facts = []
        fact_id_counter = 1
        
        # Track processing statistics
        processing_stats = {
            'undisputed_facts': 0,
            'disputed_facts': 0,
            'procedural_facts': 0,
            'key_events': 0,
            'background_context': 0,
            'damages_claims': 0,
            'errors': 0
        }
        
        # Process undisputed facts
        logger.debug(f"Processing {len(facts_matrix.get('undisputed_facts', []))} undisputed facts")
        for i, fact_data in enumerate(facts_matrix.get('undisputed_facts', [])):
            try:
                structured_fact = self._create_legal_fact(
                    fact_data, fact_id_counter, FactCategory.MATERIAL,
                    is_disputed=False, default_confidence=0.8
                )
                if structured_fact:
                    structured_facts.append(structured_fact)
                    fact_id_counter += 1
                    processing_stats['undisputed_facts'] += 1
            except Exception as e:
                logger.error(f"Error processing undisputed fact {i}: {e}")
                processing_stats['errors'] += 1
        
        # Process disputed facts
        logger.debug(f"Processing {len(facts_matrix.get('disputed_facts', []))} disputed facts")
        for i, fact_data in enumerate(facts_matrix.get('disputed_facts', [])):
            try:
                structured_fact = self._create_legal_fact(
                    fact_data, fact_id_counter, FactCategory.DISPUTED,
                    is_disputed=True, default_confidence=0.5
                )
                if structured_fact:
                    structured_facts.append(structured_fact)
                    fact_id_counter += 1
                    processing_stats['disputed_facts'] += 1
            except Exception as e:
                logger.error(f"Error processing disputed fact {i}: {e}")
                processing_stats['errors'] += 1
        
        # Process procedural facts
        logger.debug(f"Processing {len(facts_matrix.get('procedural_facts', []))} procedural facts")
        for i, fact_data in enumerate(facts_matrix.get('procedural_facts', [])):
            try:
                structured_fact = self._create_legal_fact(
                    fact_data, fact_id_counter, FactCategory.PROCEDURAL,
                    is_disputed=False, default_confidence=0.9
                )
                if structured_fact:
                    structured_facts.append(structured_fact)
                    fact_id_counter += 1
                    processing_stats['procedural_facts'] += 1
            except Exception as e:
                logger.error(f"Error processing procedural fact {i}: {e}")
                processing_stats['errors'] += 1
        
        # Process key events as material facts
        logger.debug(f"Processing {len(facts_matrix.get('key_events', []))} key events")
        for i, event_data in enumerate(facts_matrix.get('key_events', [])):
            try:
                structured_fact = self._create_legal_fact(
                    event_data, fact_id_counter, FactCategory.MATERIAL,
                    is_disputed=False, default_confidence=0.9,
                    default_significance='key_event'
                )
                if structured_fact:
                    structured_facts.append(structured_fact)
                    fact_id_counter += 1
                    processing_stats['key_events'] += 1
            except Exception as e:
                logger.error(f"Error processing key event {i}: {e}")
                processing_stats['errors'] += 1
        
        # Process background context
        logger.debug(f"Processing {len(facts_matrix.get('background_context', []))} background context items")
        for i, context_data in enumerate(facts_matrix.get('background_context', [])):
            try:
                structured_fact = self._create_legal_fact(
                    context_data, fact_id_counter, FactCategory.BACKGROUND,
                    is_disputed=False, default_confidence=0.7,
                    default_significance='background'
                )
                if structured_fact:
                    structured_facts.append(structured_fact)
                    fact_id_counter += 1
                    processing_stats['background_context'] += 1
            except Exception as e:
                logger.error(f"Error processing background context {i}: {e}")
                processing_stats['errors'] += 1
        
        # Process damages claims
        logger.debug(f"Processing {len(facts_matrix.get('damages_claims', []))} damages claims")
        for i, damages_data in enumerate(facts_matrix.get('damages_claims', [])):
            try:
                is_disputed = damages_data.get('is_disputed', False) if isinstance(damages_data, dict) else False
                structured_fact = self._create_legal_fact(
                    damages_data, fact_id_counter, FactCategory.DAMAGES,
                    is_disputed=is_disputed, default_confidence=0.8,
                    default_significance='damages'
                )
                if structured_fact:
                    structured_facts.append(structured_fact)
                    fact_id_counter += 1
                    processing_stats['damages_claims'] += 1
            except Exception as e:
                logger.error(f"Error processing damages claim {i}: {e}")
                processing_stats['errors'] += 1
        
        # Log processing results
        total_processed = sum(v for k, v in processing_stats.items() if k != 'errors')
        logger.info(f"Structured {total_processed} legal facts with {processing_stats['errors']} errors")
        logger.debug(f"Processing breakdown: {processing_stats}")
        
        # Sort facts chronologically within categories
        logger.debug("Sorting facts chronologically")
        sorted_facts = self._sort_facts_chronologically(structured_facts)
        logger.info(f"Final structured facts count: {len(sorted_facts)}")
        
        return sorted_facts
    
    def _create_legal_fact(self, fact_data: Any, fact_id: int, category: FactCategory,
                          is_disputed: bool = False, default_confidence: float = 0.8,
                          default_significance: str = '') -> Optional[LegalFact]:
        """Create a LegalFact object with robust error handling and safe defaults"""
        try:
            # Handle different input types
            if fact_data is None:
                logger.warning(f"Skipping None fact_data for fact_{fact_id:03d}")
                return None
            
            # Extract text content
            text = self._format_fact_text(fact_data)
            if not text or text.strip() == '':
                logger.warning(f"Skipping empty fact text for fact_{fact_id:03d}")
                return None
            
            # Extract metadata with safe defaults
            if isinstance(fact_data, dict):
                confidence = fact_data.get('confidence', default_confidence)
                source_documents = fact_data.get('source_documents', [])
                supporting_evidence = fact_data.get('supporting_evidence', [])
                date = fact_data.get('date')
                legal_significance = fact_data.get('legal_significance', default_significance)
                citation = self._format_citation(fact_data)
                
                # Ensure lists are actually lists
                if not isinstance(source_documents, list):
                    source_documents = [source_documents] if source_documents else []
                if not isinstance(supporting_evidence, list):
                    supporting_evidence = [supporting_evidence] if supporting_evidence else []
            else:
                # Simple string or other type
                confidence = default_confidence
                source_documents = []
                supporting_evidence = []
                date = None
                legal_significance = default_significance
                citation = ""
            
            # Validate confidence value
            if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
                logger.warning(f"Invalid confidence {confidence} for fact_{fact_id:03d}, using default")
                confidence = default_confidence
            
            return LegalFact(
                id=f"fact_{fact_id:03d}",
                text=text,
                category=category,
                confidence=confidence,
                source_documents=source_documents,
                supporting_evidence=supporting_evidence,
                date=date,
                is_disputed=is_disputed,
                legal_significance=legal_significance,
                citation=citation,
                verification_status="pending"
            )
            
        except Exception as e:
            logger.error(f"Error creating legal fact {fact_id}: {e}")
            return None
    
    def _organize_statement_sections(self, facts: List[LegalFact], 
                                   case_data: Dict[str, Any]) -> List[StatementSection]:
        """Organize facts into proper Statement of Facts sections"""
        sections = []
        
        # I. INTRODUCTION AND PARTIES
        party_facts = [f for f in facts if 'parties' in f.legal_significance.lower() or 'party' in f.text.lower()]
        introduction_section = StatementSection(
            title="INTRODUCTION AND PARTIES",
            facts=party_facts,
            introduction=self._generate_parties_introduction(case_data)
        )
        sections.append(introduction_section)
        
        # II. JURISDICTION AND VENUE
        jurisdiction_facts = [f for f in facts if any(term in f.text.lower() 
                            for term in ['jurisdiction', 'venue', 'court', 'filed'])]
        jurisdiction_section = StatementSection(
            title="JURISDICTION AND VENUE",
            facts=jurisdiction_facts,
            introduction="This Court has jurisdiction over this matter pursuant to the following facts:"
        )
        sections.append(jurisdiction_section)
        
        # III. BACKGROUND FACTS
        background_facts = [f for f in facts if f.category == FactCategory.BACKGROUND]
        background_section = StatementSection(
            title="BACKGROUND FACTS",
            facts=background_facts,
            introduction="The following background facts provide necessary context for this matter:"
        )
        sections.append(background_section)
        
        # IV. MATERIAL FACTS
        material_facts = [f for f in facts if f.category == FactCategory.MATERIAL and not f.is_disputed]
        material_section = StatementSection(
            title="MATERIAL FACTS",
            facts=material_facts,
            introduction="The following material facts are central to the claims and defenses in this case:"
        )
        sections.append(material_section)
        
        # V. DISPUTED FACTS
        disputed_facts = [f for f in facts if f.category == FactCategory.DISPUTED or f.is_disputed]
        if disputed_facts:
            disputed_section = StatementSection(
                title="DISPUTED FACTS",
                facts=disputed_facts,
                introduction="The parties dispute the following facts, which require resolution through discovery or trial:"
            )
            sections.append(disputed_section)
        
        # VI. DAMAGES AND RELIEF SOUGHT
        damages_facts = [f for f in facts if f.category == FactCategory.DAMAGES]
        if damages_facts:
            damages_section = StatementSection(
                title="DAMAGES AND RELIEF SOUGHT",
                facts=damages_facts,
                introduction="Plaintiff has suffered the following damages as a result of Defendant's conduct:"
            )
            sections.append(damages_section)
        
        return sections
    
    def _generate_professional_document(self, sections: List[StatementSection], 
                                      case_data: Dict[str, Any]) -> str:
        """Generate professional Statement of Facts document"""
        document_parts = []
        
        # Document header
        case_caption = self._format_case_caption(case_data)
        document_purpose = case_data.get('document_purpose', 'the pending motion')
        
        header = self.templates['document_header'].format(
            case_caption=case_caption,
            party_plaintiff=case_data.get('plaintiff_name', 'Plaintiff'),
            document_purpose=document_purpose
        )
        document_parts.append(header)
        
        # Generate sections
        paragraph_counter = 1
        for section_num, section in enumerate(sections, 1):
            # Section header
            section_intro = self.templates['section_introduction'].format(
                section_number=self._format_roman_numeral(section_num),
                section_title=section.title,
                introduction_text=section.introduction
            )
            document_parts.append(section_intro)
            
            # Section facts
            for fact in section.facts:
                if fact.is_disputed:
                    fact_text = self.templates['disputed_fact'].format(
                        paragraph_number=paragraph_counter,
                        fact_text=fact.text,
                        citation=fact.citation or "",
                        party_defendant=case_data.get('defendant_name', 'Defendant'),
                        dispute_description=self._generate_dispute_description(fact)
                    )
                else:
                    fact_text = self.templates['fact_paragraph'].format(
                        paragraph_number=paragraph_counter,
                        fact_text=fact.text,
                        citation=fact.citation or ""
                    )
                
                document_parts.append(fact_text)
                paragraph_counter += 1
            
            document_parts.append("")  # Add spacing between sections
        
        # Document conclusion
        conclusion = self.templates['conclusion'].format(
            conclusion_statement=case_data.get('conclusion_statement', 
                                             'the relief requested is appropriate and should be granted'),
            attorney_name=case_data.get('attorney_name', '[Attorney Name]'),
            attorney_title=case_data.get('attorney_title', 'Attorney at Law'),
            bar_number=case_data.get('bar_number', '[Bar Number]'),
            client_name=case_data.get('plaintiff_name', '[Client Name]')
        )
        document_parts.append(conclusion)
        
        return "\n".join(document_parts)
    
    def _format_fact_text(self, fact_data: Any) -> str:
        """Format raw fact data into proper legal writing style"""
        if isinstance(fact_data, str):
            text = fact_data
        elif isinstance(fact_data, dict):
            text = fact_data.get('text', fact_data.get('description', str(fact_data)))
        else:
            text = str(fact_data)
        
        # Ensure proper sentence structure
        text = text.strip()
        if not text.endswith('.'):
            text += '.'
        
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]
        
        # Clean up common formatting issues
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces
        text = re.sub(r'\.+', '.', text)  # Multiple periods
        
        return text
    
    def _format_citation(self, fact_data: Any) -> str:
        """Format Bluebook-compliant citations"""
        if not isinstance(fact_data, dict):
            return ""
        
        source_docs = fact_data.get('source_documents', [])
        if not source_docs:
            return ""
        
        # Format based on document type
        citations = []
        for doc in source_docs[:3]:  # Limit to 3 citations per fact
            if isinstance(doc, str):
                # Simple document reference
                if doc.endswith('.pdf'):
                    doc_name = doc.replace('.pdf', '').replace('_', ' ').title()
                    citations.append(f"(Ex. {doc_name})")
                else:
                    citations.append(f"(See {doc})")
            elif isinstance(doc, dict):
                # Structured citation
                if 'exhibit' in doc:
                    citations.append(f"(Ex. {doc['exhibit']})")
                elif 'page' in doc:
                    citations.append(f"(Doc. {doc.get('document', '')}, p. {doc['page']})")
        
        return " " + "; ".join(citations) if citations else ""
    
    def _populate_case_data_with_defaults(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Populate case_data with safe defaults to prevent template failures.
        This ensures all required fields have reasonable fallback values.
        """
        logger.debug("Populating case data with safe defaults")
        
        # Create a copy to avoid modifying the original
        populated_data = case_data.copy() if case_data else {}
        
        # Define comprehensive defaults
        defaults = {
            'plaintiff_name': '[Plaintiff Name - Please Update]',
            'defendant_name': '[Defendant Name - Please Update]',
            'case_number': '[Case Number - Please Update]',
            'court': '[Court Name - Please Update]',
            'document_purpose': 'the pending motion',
            'attorney_name': '[Attorney Name - Please Update]',
            'attorney_title': 'Attorney at Law',
            'bar_number': '[Bar Number - Please Update]',
            'conclusion_statement': 'the relief requested is appropriate and should be granted',
            'case_title': None,  # Will be auto-generated if not provided
            'filing_date': datetime.now().strftime('%B %d, %Y'),
            'jurisdiction_basis': 'diversity of citizenship and amount in controversy',
            'venue_basis': 'proper venue in this district'
        }
        
        # Apply defaults for missing values
        for key, default_value in defaults.items():
            if key not in populated_data or not populated_data[key]:
                populated_data[key] = default_value
                if key in ['plaintiff_name', 'defendant_name', 'case_number', 'court', 'attorney_name', 'bar_number']:
                    logger.warning(f"Using placeholder for {key}: {default_value}")
        
        # Auto-generate case title if not provided
        if not populated_data.get('case_title'):
            plaintiff = populated_data['plaintiff_name'].replace('[', '').replace(']', '').replace(' - Please Update', '')
            defendant = populated_data['defendant_name'].replace('[', '').replace(']', '').replace(' - Please Update', '')
            populated_data['case_title'] = f"{plaintiff} v. {defendant}"
        
        logger.debug(f"Case data populated with {len(defaults)} potential defaults")
        return populated_data

    def _format_case_caption(self, case_data: Dict[str, Any]) -> str:
        """Format proper case caption with robust error handling"""
        logger.debug("Formatting case caption")
        
        # Ensure we have populated case data
        populated_data = self._populate_case_data_with_defaults(case_data)
        
        plaintiff = populated_data['plaintiff_name']
        defendant = populated_data['defendant_name']
        case_number = populated_data['case_number']
        court = populated_data['court']
        
        # Format with proper legal document structure
        caption = f"""{plaintiff},
                        Plaintiff,
v.                                      Case No. {case_number}

{defendant},
                        Defendant.

{court}"""
        
        logger.debug("Case caption formatted successfully")
        return caption
    
    def _generate_parties_introduction(self, case_data: Dict[str, Any]) -> str:
        """Generate introduction to parties section with robust defaults"""
        logger.debug("Generating parties introduction")
        
        # Ensure we have populated case data
        populated_data = self._populate_case_data_with_defaults(case_data)
        
        plaintiff = populated_data['plaintiff_name']
        defendant = populated_data['defendant_name']
        
        # Create more sophisticated introduction based on available data
        intro_parts = []
        
        # Basic party identification
        intro_parts.append(f'This action involves a dispute between {plaintiff} ("Plaintiff") and {defendant} ("Defendant").')
        
        # Add case context if available
        if populated_data.get('case_type'):
            intro_parts.append(f'This {populated_data["case_type"]} case arises from the following circumstances.')
        
        # Add jurisdiction context if available
        if populated_data.get('jurisdiction_basis'):
            intro_parts.append(f'This Court has jurisdiction based on {populated_data["jurisdiction_basis"]}.')
        
        # Standard conclusion
        intro_parts.append('The following facts establish the identity and relevant background of the parties:')
        
        introduction = ' '.join(intro_parts)
        logger.debug("Parties introduction generated successfully")
        
        return introduction
    
    def _format_roman_numeral(self, num: int) -> str:
        """Convert number to Roman numeral"""
        roman_numerals = {
            1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V',
            6: 'VI', 7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X'
        }
        return roman_numerals.get(num, str(num))
    
    def _generate_dispute_description(self, fact: LegalFact) -> str:
        """Generate description of what is disputed about a fact"""
        # This could be enhanced with AI to generate more specific disputes
        return "the accuracy and completeness of this allegation"
    
    def _sort_facts_chronologically(self, facts: List[LegalFact]) -> List[LegalFact]:
        """Sort facts chronologically within their categories"""
        def sort_key(fact):
            # Sort by category first, then by date
            category_order = {
                FactCategory.BACKGROUND: 1,
                FactCategory.MATERIAL: 2,
                FactCategory.DISPUTED: 3,
                FactCategory.PROCEDURAL: 4,
                FactCategory.DAMAGES: 5
            }
            
            category_rank = category_order.get(fact.category, 6)
            
            # Try to parse date for chronological ordering
            date_rank = 9999  # Default for facts without dates
            if fact.date:
                try:
                    parsed_date = datetime.fromisoformat(fact.date.replace('Z', '+00:00'))
                    date_rank = parsed_date.timestamp()
                except (ValueError, AttributeError):
                    pass
            
            return (category_rank, date_rank)
        
        return sorted(facts, key=sort_key)
    
    def _create_verification_report(self, facts: List[LegalFact]) -> Dict[str, Any]:
        """Create verification report for attorney review"""
        total_facts = len(facts)
        high_confidence = len([f for f in facts if f.confidence >= 0.8])
        medium_confidence = len([f for f in facts if 0.6 <= f.confidence < 0.8])
        low_confidence = len([f for f in facts if f.confidence < 0.6])
        disputed_facts = len([f for f in facts if f.is_disputed])
        
        citation_coverage = len([f for f in facts if f.citation]) / total_facts if total_facts > 0 else 0
        
        return {
            'total_facts': total_facts,
            'confidence_distribution': {
                'high_confidence': high_confidence,
                'medium_confidence': medium_confidence,
                'low_confidence': low_confidence
            },
            'disputed_facts_count': disputed_facts,
            'citation_coverage': citation_coverage,
            'verification_recommendations': self._generate_verification_recommendations(facts),
            'quality_score': self._calculate_quality_score(facts)
        }
    
    def _identify_review_requirements(self, facts: List[LegalFact], 
                                    facts_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific attorney review requirements"""
        review_points = []
        
        # Low confidence facts
        low_confidence_facts = [f for f in facts if f.confidence < 0.6]
        if low_confidence_facts:
            review_points.append({
                'type': 'confidence_review',
                'priority': 'high',
                'description': f'{len(low_confidence_facts)} facts require confidence verification',
                'facts': [f.id for f in low_confidence_facts]
            })
        
        # Facts without citations
        uncited_facts = [f for f in facts if not f.citation]
        if len(uncited_facts) > len(facts) * 0.3:  # More than 30% uncited
            review_points.append({
                'type': 'citation_review',
                'priority': 'medium',
                'description': f'{len(uncited_facts)} facts need proper citations',
                'facts': [f.id for f in uncited_facts]
            })
        
        # Disputed facts requiring attention
        disputed_facts = [f for f in facts if f.is_disputed]
        if disputed_facts:
            review_points.append({
                'type': 'dispute_resolution',
                'priority': 'high',
                'description': f'{len(disputed_facts)} disputed facts need resolution strategy',
                'facts': [f.id for f in disputed_facts]
            })
        
        # Missing key elements
        attorney_review_points = facts_data.get('attorney_review_points', [])
        for point in attorney_review_points:
            review_points.append({
                'type': 'knowledge_graph_flag',
                'priority': point.get('priority', 'medium'),
                'description': point.get('description', ''),
                'details': point.get('details', {})
            })
        
        return review_points
    
    def _generate_export_formats(self, document: str, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate export capabilities for different formats"""
        return {
            'markdown': {
                'content': self._convert_to_markdown(document),
                'filename': f"statement_of_facts_{case_data.get('case_number', 'draft')}.md"
            },
            'word_ready': {
                'content': self._format_for_word(document),
                'filename': f"statement_of_facts_{case_data.get('case_number', 'draft')}.docx",
                'instructions': "Ready for import into Microsoft Word for final formatting"
            },
            'pdf_ready': {
                'content': document,
                'filename': f"statement_of_facts_{case_data.get('case_number', 'draft')}.pdf",
                'instructions': "Formatted for PDF generation with proper legal document structure"
            }
        }
    
    def _convert_to_markdown(self, document: str) -> str:
        """Convert document to Markdown format"""
        # Convert Roman numerals to Markdown headers
        lines = document.split('\n')
        markdown_lines = []
        
        for line in lines:
            line = line.strip()
            if re.match(r'^[IVX]+\.\s+[A-Z\s]+$', line):
                # Section header
                markdown_lines.append(f"## {line}")
            elif re.match(r'^\d+\.\s+', line):
                # Numbered paragraph
                markdown_lines.append(f"{line}")
            elif line.isupper() and len(line) > 5:
                # Title
                markdown_lines.append(f"# {line}")
            else:
                markdown_lines.append(line)
        
        return '\n'.join(markdown_lines)
    
    def _format_for_word(self, document: str) -> str:
        """Format document for Microsoft Word import"""
        # Add specific formatting markers for Word
        formatted = document.replace('\n\n', '\n\n---PAGE-BREAK---\n\n')
        return formatted
    
    def _assess_document_quality(self, document: str, facts: List[LegalFact]) -> Dict[str, Any]:
        """Assess overall document quality"""
        word_count = len(document.split())
        paragraph_count = len([p for p in document.split('\n') if p.strip() and p.strip()[0].isdigit()])
        
        avg_confidence = sum(f.confidence for f in facts) / len(facts) if facts else 0
        citation_rate = len([f for f in facts if f.citation]) / len(facts) if facts else 0
        
        quality_score = (
            (avg_confidence * 0.4) +
            (citation_rate * 0.3) +
            (min(word_count / 2000, 1.0) * 0.2) +  # Appropriate length
            (min(paragraph_count / 50, 1.0) * 0.1)  # Good paragraph count
        )
        
        return {
            'overall_quality_score': quality_score,
            'word_count': word_count,
            'paragraph_count': paragraph_count,
            'average_confidence': avg_confidence,
            'citation_coverage': citation_rate,
            'readability_assessment': self._assess_readability(document),
            'legal_writing_compliance': self._assess_legal_compliance(document)
        }
    
    def _assess_readability(self, document: str) -> Dict[str, Any]:
        """Assess document readability"""
        sentences = len([s for s in document.split('.') if s.strip()])
        words = len(document.split())
        avg_sentence_length = words / sentences if sentences > 0 else 0
        
        return {
            'average_sentence_length': avg_sentence_length,
            'complexity_level': 'appropriate' if 15 <= avg_sentence_length <= 25 else 'review_needed'
        }
    
    def _assess_legal_compliance(self, document: str) -> Dict[str, Any]:
        """Assess compliance with legal writing standards"""
        has_proper_caption = 'Case No.' in document
        has_proper_conclusion = 'Respectfully submitted' in document
        has_numbered_paragraphs = bool(re.search(r'^\d+\.', document, re.MULTILINE))
        
        compliance_score = sum([has_proper_caption, has_proper_conclusion, has_numbered_paragraphs]) / 3
        
        return {
            'compliance_score': compliance_score,
            'has_proper_caption': has_proper_caption,
            'has_proper_conclusion': has_proper_conclusion,
            'has_numbered_paragraphs': has_numbered_paragraphs,
            'frcp_compliance': 'good' if compliance_score >= 0.8 else 'needs_review'
        }
    
    def _generate_verification_recommendations(self, facts: List[LegalFact]) -> List[str]:
        """Generate specific verification recommendations"""
        recommendations = []
        
        low_confidence_count = len([f for f in facts if f.confidence < 0.6])
        if low_confidence_count > 0:
            recommendations.append(f"Verify {low_confidence_count} low-confidence facts with additional sources")
        
        uncited_count = len([f for f in facts if not f.citation])
        if uncited_count > 0:
            recommendations.append(f"Add proper citations for {uncited_count} facts")
        
        disputed_count = len([f for f in facts if f.is_disputed])
        if disputed_count > 0:
            recommendations.append(f"Develop litigation strategy for {disputed_count} disputed facts")
        
        return recommendations
    
    def _calculate_quality_score(self, facts: List[LegalFact]) -> float:
        """Calculate overall quality score for facts"""
        if not facts:
            return 0.0
        
        confidence_score = sum(f.confidence for f in facts) / len(facts)
        citation_score = len([f for f in facts if f.citation]) / len(facts)
        completeness_score = len([f for f in facts if f.source_documents]) / len(facts)
        
        return (confidence_score * 0.5 + citation_score * 0.3 + completeness_score * 0.2)
    
    def _section_to_dict(self, section: StatementSection) -> Dict[str, Any]:
        """Convert StatementSection to dictionary"""
        return {
            'title': section.title,
            'introduction': section.introduction,
            'conclusion': section.conclusion,
            'fact_count': len(section.facts),
            'facts': [
                {
                    'id': fact.id,
                    'text': fact.text,
                    'category': fact.category.value,
                    'confidence': fact.confidence,
                    'is_disputed': fact.is_disputed,
                    'citation': fact.citation
                }
                for fact in section.facts
            ]
        }


def create_statement_of_facts_generator() -> StatementOfFactsGenerator:
    """Factory function to create Statement of Facts generator"""
    return StatementOfFactsGenerator()


if __name__ == "__main__":
    # Example usage
    generator = create_statement_of_facts_generator()
    
    # Test case data
    test_case_data = {
        'plaintiff_name': 'John Doe',
        'defendant_name': 'MegaCorp Industries',
        'case_number': '2024-CV-12345',
        'court': 'Superior Court of California, County of Los Angeles',
        'document_purpose': 'Plaintiff\'s Motion for Summary Judgment',
        'attorney_name': 'Jane Attorney',
        'attorney_title': 'Attorney at Law',
        'bar_number': 'State Bar No. 123456'
    }
    
    print("Statement of Facts Generator initialized successfully")
    print("Ready for integration with knowledge graph system")