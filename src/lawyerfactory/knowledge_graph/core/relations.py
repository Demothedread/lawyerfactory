"""
# Script Name: relations.py
# Description: Legal Relationship Detection Engine Extracts and maps legal relationships from draft documents with confidence scoring
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Research
#   - Group Tags: knowledge-graph
Legal Relationship Detection Engine
Extracts and maps legal relationships from draft documents with confidence scoring
"""

import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from enhanced_knowledge_graph import (ConfidenceFactors,
                                      EnhancedKnowledgeGraph, LegalEntity,
                                      LegalEntityType, LegalRelationship,
                                      LegalRelationshipType)

logger = logging.getLogger(__name__)


class LegalRelationshipDetector:
    """Advanced legal relationship detection and extraction engine"""
    
    def __init__(self, enhanced_kg: EnhancedKnowledgeGraph):
        self.kg = enhanced_kg
        self.legal_patterns = self._initialize_legal_patterns()
        self.relationship_patterns = self._initialize_relationship_patterns()
        self.temporal_patterns = self._initialize_temporal_patterns()
        
    def _initialize_legal_patterns(self) -> Dict[str, List[str]]:
        """Initialize regex patterns for legal entity detection"""
        return {
            LegalEntityType.PLAINTIFF.value: [
                r"(?:plaintiff|claimant|petitioner)s?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:brings|filed|alleges|claims)",
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.?\s+",
                r"(?:case\s+of\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:vs?\.?|versus)"
            ],
            
            LegalEntityType.DEFENDANT.value: [
                r"(?:defendant|respondent)s?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"(?:vs?\.?|versus)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"against\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"sued\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
            ],
            
            LegalEntityType.DATE.value: [
                r"(?:on|dated?|occurring)\s+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})",
                r"(\d{1,2}/\d{1,2}/\d{4})",
                r"(\d{4}-\d{2}-\d{2})",
                r"(?:filed|served|executed)\s+(?:on\s+)?([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})"
            ],
            
            LegalEntityType.CLAIM.value: [
                r"claim[s]?\s+(?:for\s+)?([a-z\s]+(?:negligence|breach|fraud|defamation|discrimination))",
                r"cause[s]?\s+of\s+action\s+(?:for\s+)?([a-z\s]+)",
                r"alleges?\s+([a-z\s]+(?:negligence|breach|fraud|defamation|discrimination))",
                r"(?:first|second|third|fourth|fifth)\s+cause\s+of\s+action[:]?\s+([A-Z][a-z\s]+)"
            ],
            
            LegalEntityType.DAMAGES.value: [
                r"damages?\s+(?:in\s+the\s+amount\s+of\s+)?(\$[\d,]+(?:\.\d{2})?)",
                r"seek[s]?\s+(\$[\d,]+(?:\.\d{2})?)",
                r"monetary\s+relief\s+(?:of\s+)?(\$[\d,]+(?:\.\d{2})?)",
                r"compensation\s+(?:of\s+)?(\$[\d,]+(?:\.\d{2})?)"
            ],
            
            LegalEntityType.COURT.value: [
                r"(?:in\s+the\s+)?([A-Z][a-z\s]+(?:Court|Tribunal))",
                r"(?:before\s+the\s+)?([A-Z][a-z\s]+(?:Court|Tribunal))",
                r"filed\s+in\s+([A-Z][a-z\s]+(?:Court|Tribunal))"
            ],
            
            LegalEntityType.FACT.value: [
                r"(?:fact|allegation|assertion):\s+(.+?)(?:\.|$)",
                r"it\s+is\s+(?:alleged|claimed|asserted)\s+that\s+(.+?)(?:\.|$)",
                r"on\s+(?:or\s+about\s+)?[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}[,]?\s+(.+?)(?:\.|$)"
            ]
        }
    
    def _initialize_relationship_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for detecting legal relationships"""
        return {
            LegalRelationshipType.CAUSES.value: [
                r"(.+?)\s+(?:caused|resulted\s+in|led\s+to)\s+(.+)",
                r"(?:as\s+a\s+result\s+of|due\s+to|because\s+of)\s+(.+?)[,]?\s+(.+)",
                r"(.+?)\s+proximately\s+caused\s+(.+)"
            ],
            
            LegalRelationshipType.CONTRADICTS.value: [
                r"(.+?)\s+(?:contradicts|conflicts\s+with|is\s+inconsistent\s+with)\s+(.+)",
                r"(?:however|but|contrary\s+to)\s+(.+?)[,]?\s+(.+)",
                r"(.+?)\s+(?:denies|disputes|challenges)\s+(.+)"
            ],
            
            LegalRelationshipType.SUPPORTS.value: [
                r"(.+?)\s+(?:supports|corroborates|confirms)\s+(.+)",
                r"(.+?)\s+(?:is\s+evidence\s+of|demonstrates|proves)\s+(.+)",
                r"(?:evidence\s+shows|documentation\s+reveals)\s+that\s+(.+)"
            ],
            
            LegalRelationshipType.OCCURS_BEFORE.value: [
                r"(?:prior\s+to|before)\s+(.+?)[,]?\s+(.+)",
                r"(.+?)\s+(?:preceded|came\s+before)\s+(.+)",
                r"(?:first|initially)[,]?\s+(.+?)[,]?\s+(?:then|subsequently)\s+(.+)"
            ],
            
            LegalRelationshipType.OCCURS_AFTER.value: [
                r"(?:after|following|subsequent\s+to)\s+(.+?)[,]?\s+(.+)",
                r"(.+?)\s+(?:followed|came\s+after)\s+(.+)",
                r"(?:then|subsequently|later)[,]?\s+(.+)"
            ],
            
            LegalRelationshipType.PLAINTIFF_DEFENDANT.value: [
                r"([A-Z][a-z\s]+)\s+(?:vs?\.?|versus)\s+([A-Z][a-z\s]+)",
                r"([A-Z][a-z\s]+)\s+sued\s+([A-Z][a-z\s]+)",
                r"([A-Z][a-z\s]+)\s+(?:brings\s+(?:this\s+)?action\s+against|filed\s+suit\s+against)\s+([A-Z][a-z\s]+)"
            ],
            
            LegalRelationshipType.EVIDENCED_BY.value: [
                r"(.+?)\s+(?:is\s+evidenced\s+by|is\s+documented\s+in|is\s+shown\s+by)\s+(.+)",
                r"(?:evidence\s+of\s+)?(.+?)\s+(?:includes|consists\s+of)\s+(.+)",
                r"(.+?)\s+(?:as\s+shown\s+in|per|according\s+to)\s+(.+)"
            ]
        }
    
    def _initialize_temporal_patterns(self) -> Dict[str, str]:
        """Initialize patterns for temporal relationship detection"""
        return {
            'absolute_date': r'(?:on\s+)?([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
            'relative_time': r'(?:approximately|about|around)\s+(\d+\s+(?:days?|weeks?|months?|years?)\s+(?:ago|before|after))',
            'date_range': r'(?:between|from)\s+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})\s+(?:and|to)\s+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
            'sequence_markers': r'(?:first|second|third|then|next|subsequently|finally|lastly)'
        }
    
    def extract_legal_entities_from_text(self, text: str, draft_type: str = 'unknown', 
                                       source_credibility: float = 0.7) -> List[LegalEntity]:
        """Extract legal entities from text with confidence scoring"""
        entities = []
        
        for entity_type, patterns in self.legal_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity_text = match.group(1).strip()
                    if len(entity_text) < 2 or len(entity_text) > 200:  # Filter unreasonable matches
                        continue
                    
                    # Calculate confidence based on pattern quality and context
                    confidence_factors = self._calculate_entity_confidence(
                        entity_text, entity_type, match, text, source_credibility
                    )
                    
                    entity = LegalEntity(
                        id=str(uuid.uuid4()),
                        entity_type=LegalEntityType(entity_type),
                        name=entity_text,
                        description=f"Extracted from {draft_type} draft",
                        source_text=match.group(0),
                        context_window=self._get_context_window(text, match.start(), match.end()),
                        confidence_factors=confidence_factors,
                        extraction_method="pattern_based",
                        legal_attributes={
                            'draft_type': draft_type,
                            'pattern_match': pattern,
                            'match_position': {'start': match.start(), 'end': match.end()}
                        }
                    )
                    entities.append(entity)
        
        # Deduplicate similar entities
        return self._deduplicate_entities(entities)
    
    def extract_legal_relationships_from_text(self, text: str, entities: List[LegalEntity], 
                                            source_credibility: float = 0.7) -> List[LegalRelationship]:
        """Extract relationships between entities from text"""
        relationships = []
        
        # Create entity lookup for efficient matching
        entity_lookup = {entity.name.lower(): entity for entity in entities}
        
        for relationship_type, patterns in self.relationship_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Extract potential entity names from match groups
                    if len(match.groups()) >= 2:
                        from_text = match.group(1).strip()
                        to_text = match.group(2).strip()
                        
                        # Find matching entities
                        from_entity = self._find_best_entity_match(from_text, entities)
                        to_entity = self._find_best_entity_match(to_text, entities)
                        
                        if from_entity and to_entity and from_entity != to_entity:
                            confidence_factors = self._calculate_relationship_confidence(
                                from_entity, to_entity, relationship_type, match, text, source_credibility
                            )
                            
                            relationship = LegalRelationship(
                                from_entity=from_entity.id,
                                to_entity=to_entity.id,
                                relationship_type=LegalRelationshipType(relationship_type),
                                confidence_factors=confidence_factors,
                                extraction_method="pattern_based",
                                supporting_text=match.group(0),
                                temporal_context=self._extract_temporal_context(text, match.start(), match.end()),
                                legal_significance=self._assess_legal_significance(relationship_type)
                            )
                            relationships.append(relationship)
        
        return relationships
    
    def _calculate_entity_confidence(self, entity_text: str, entity_type: str, 
                                   match: re.Match, full_text: str, 
                                   source_credibility: float) -> ConfidenceFactors:
        """Calculate confidence factors for an extracted entity"""
        
        # Base confidence from extraction method
        extraction_reliability = 0.7  # Pattern-based extraction
        
        # Boost confidence for well-formed entities
        if entity_type in [LegalEntityType.PLAINTIFF.value, LegalEntityType.DEFENDANT.value]:
            if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', entity_text):
                extraction_reliability += 0.1
        
        # Boost confidence for formal legal language
        context = self._get_context_window(full_text, match.start(), match.end(), window_size=100)
        legal_terms = ['plaintiff', 'defendant', 'alleges', 'claims', 'court', 'filed', 'served']
        legal_term_count = sum(1 for term in legal_terms if term.lower() in context.lower())
        legal_context_boost = min(0.2, legal_term_count * 0.05)
        
        return ConfidenceFactors(
            source_credibility=source_credibility,
            extraction_method_reliability=extraction_reliability + legal_context_boost,
            evidence_support=0.0,  # Will be updated when evidence is linked
            temporal_consistency=1.0,  # Assume consistent until proven otherwise
            cross_validation=0.0,  # Will be updated during cross-validation
            legal_precedence=0.5  # Default legal precedence
        )
    
    def _calculate_relationship_confidence(self, from_entity: LegalEntity, to_entity: LegalEntity,
                                         relationship_type: str, match: re.Match, full_text: str,
                                         source_credibility: float) -> ConfidenceFactors:
        """Calculate confidence factors for an extracted relationship"""
        
        # Base confidence from extraction method
        extraction_reliability = 0.6  # Relationship extraction is more complex
        
        # Boost confidence based on entity confidence
        entity_confidence_avg = (from_entity.overall_confidence + to_entity.overall_confidence) / 2
        extraction_reliability += (entity_confidence_avg - 0.5) * 0.3
        
        # Boost confidence for strong relationship indicators
        relationship_text = match.group(0).lower()
        strong_indicators = {
            LegalRelationshipType.CAUSES.value: ['caused', 'resulted in', 'proximately caused'],
            LegalRelationshipType.CONTRADICTS.value: ['contradicts', 'conflicts with', 'denies'],
            LegalRelationshipType.SUPPORTS.value: ['proves', 'demonstrates', 'corroborates']
        }
        
        if relationship_type in strong_indicators:
            for indicator in strong_indicators[relationship_type]:
                if indicator in relationship_text:
                    extraction_reliability += 0.1
                    break
        
        return ConfidenceFactors(
            source_credibility=source_credibility,
            extraction_method_reliability=min(1.0, extraction_reliability),
            evidence_support=0.0,
            temporal_consistency=1.0,
            cross_validation=0.0,
            legal_precedence=self._get_relationship_legal_precedence(relationship_type)
        )
    
    def _find_best_entity_match(self, text: str, entities: List[LegalEntity]) -> Optional[LegalEntity]:
        """Find the best matching entity for given text"""
        text_lower = text.lower().strip()
        
        # Exact match first
        for entity in entities:
            if entity.name.lower() == text_lower:
                return entity
        
        # Partial match
        for entity in entities:
            if text_lower in entity.name.lower() or entity.name.lower() in text_lower:
                # Check if it's a meaningful partial match (not just common words)
                if len(text_lower) > 3 and len(entity.name) > 3:
                    return entity
        
        return None
    
    def _get_context_window(self, text: str, start: int, end: int, window_size: int = 50) -> str:
        """Extract context window around a match"""
        context_start = max(0, start - window_size)
        context_end = min(len(text), end + window_size)
        return text[context_start:context_end]
    
    def _extract_temporal_context(self, text: str, start: int, end: int) -> Optional[str]:
        """Extract temporal context from the surrounding text"""
        context = self._get_context_window(text, start, end, window_size=100)
        
        # Look for temporal indicators
        for pattern_name, pattern in self.temporal_patterns.items():
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return f"{pattern_name}: {match.group(0)}"
        
        return None
    
    def _assess_legal_significance(self, relationship_type: str) -> str:
        """Assess the legal significance of a relationship type"""
        significance_mapping = {
            LegalRelationshipType.CAUSES.value: "establishes causation - critical for liability",
            LegalRelationshipType.CONTRADICTS.value: "creates factual dispute - requires resolution",
            LegalRelationshipType.SUPPORTS.value: "strengthens legal position - favorable evidence",
            LegalRelationshipType.PLAINTIFF_DEFENDANT.value: "defines party relationship - procedural foundation",
            LegalRelationshipType.EVIDENCED_BY.value: "provides evidentiary support - strengthens claims",
            LegalRelationshipType.OCCURS_BEFORE.value: "establishes temporal sequence - relevant for causation",
            LegalRelationshipType.OCCURS_AFTER.value: "establishes temporal sequence - relevant for damages"
        }
        
        return significance_mapping.get(relationship_type, "general legal relationship")
    
    def _get_relationship_legal_precedence(self, relationship_type: str) -> float:
        """Get legal precedence score for relationship type"""
        precedence_mapping = {
            LegalRelationshipType.CAUSES.value: 0.9,  # Causation is highly significant
            LegalRelationshipType.CONTRADICTS.value: 0.8,  # Conflicts need resolution
            LegalRelationshipType.SUPPORTS.value: 0.7,  # Supporting evidence is important
            LegalRelationshipType.PLAINTIFF_DEFENDANT.value: 0.9,  # Party relationships are fundamental
            LegalRelationshipType.EVIDENCED_BY.value: 0.6,  # Evidence links are significant
            LegalRelationshipType.OCCURS_BEFORE.value: 0.5,  # Temporal relationships are contextual
            LegalRelationshipType.OCCURS_AFTER.value: 0.5   # Temporal relationships are contextual
        }
        
        return precedence_mapping.get(relationship_type, 0.5)
    
    def _deduplicate_entities(self, entities: List[LegalEntity]) -> List[LegalEntity]:
        """Remove duplicate entities based on name and type similarity"""
        unique_entities = []
        seen_combinations = set()
        
        for entity in entities:
            # Create a key for deduplication
            key = (entity.entity_type.value, entity.name.lower().strip())
            
            if key not in seen_combinations:
                seen_combinations.add(key)
                unique_entities.append(entity)
            else:
                # Update confidence of existing entity if this one has higher confidence
                for existing in unique_entities:
                    if (existing.entity_type == entity.entity_type and 
                        existing.name.lower().strip() == entity.name.lower().strip()):
                        if entity.overall_confidence > existing.overall_confidence:
                            existing.confidence_factors = entity.confidence_factors
                        break
        
        return unique_entities
    
    def process_draft_document(self, document_content: str, draft_type: str,
                             source_credibility: float = 0.8) -> Dict[str, Any]:
        """Process a complete draft document and extract entities and relationships"""
        logger.info(f"Processing {draft_type} draft document with {len(document_content)} characters")
        
        # Extract entities
        entities = self.extract_legal_entities_from_text(
            document_content, draft_type, source_credibility
        )
        
        # Extract relationships
        relationships = self.extract_legal_relationships_from_text(
            document_content, entities, source_credibility
        )
        
        # Store entities in knowledge graph
        stored_entity_ids = []
        for entity in entities:
            try:
                entity_id = self.kg.add_legal_entity(entity)
                stored_entity_ids.append(entity_id)
            except Exception as e:
                logger.error(f"Failed to store entity {entity.name}: {e}")
        
        # Store relationships in knowledge graph
        stored_relationship_ids = []
        for relationship in relationships:
            try:
                rel_id = self.kg.add_legal_relationship(relationship)
                stored_relationship_ids.append(rel_id)
            except Exception as e:
                logger.error(f"Failed to store relationship: {e}")
        
        result = {
            'draft_type': draft_type,
            'entities_extracted': len(entities),
            'relationships_extracted': len(relationships),
            'entities_stored': len(stored_entity_ids),
            'relationships_stored': len(stored_relationship_ids),
            'entity_details': [
                {
                    'id': entity.id,
                    'type': entity.entity_type.value,
                    'name': entity.name,
                    'confidence': entity.overall_confidence
                }
                for entity in entities
            ],
            'relationship_details': [
                {
                    'type': rel.relationship_type.value,
                    'from_entity': next((e.name for e in entities if e.id == rel.from_entity), 'Unknown'),
                    'to_entity': next((e.name for e in entities if e.id == rel.to_entity), 'Unknown'),
                    'confidence': rel.overall_confidence,
                    'legal_significance': rel.legal_significance
                }
                for rel in relationships
            ]
        }
        
        logger.info(f"Completed processing: {result['entities_extracted']} entities, {result['relationships_extracted']} relationships")
        return result


if __name__ == "__main__":
    # Test the legal relationship detector
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    # Create test knowledge graph
    ekg = EnhancedKnowledgeGraph("test_detector_kg.db")
    detector = LegalRelationshipDetector(ekg)
    
    # Test text
    test_text = """
    Plaintiff John Doe brings this action against Defendant MegaCorp Inc. 
    On January 15, 2024, the defendant negligently operated its vehicle, 
    which caused significant injuries to the plaintiff. The plaintiff seeks 
    damages in the amount of $100,000 for medical expenses and pain and suffering.
    Evidence shows that the defendant was speeding at the time of the incident.
    """
    
    try:
        result = detector.process_draft_document(test_text, "fact_statement", 0.8)
        print(f"Processing result: {json.dumps(result, indent=2)}")
        
        # Test statistics
        stats = ekg.get_enhanced_statistics()
        print(f"Knowledge graph statistics: {json.dumps(stats, indent=2)}")
        
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    finally:
        ekg.close()