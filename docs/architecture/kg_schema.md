# Enhanced Knowledge Graph Schema for Legal Entity Processing

## Overview

This document specifies the enhanced knowledge graph schema that extends the current JSON-based entity storage to support sophisticated legal entity relationships, Named Entity Recognition (NER), and semantic search capabilities.

## Entity Type Hierarchy

### Core Legal Entity Types

```python
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

class EntityType(Enum):
    # Parties and People
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    ATTORNEY = "attorney"
    JUDGE = "judge"
    WITNESS = "witness"
    EXPERT_WITNESS = "expert_witness"
    
    # Legal Claims and Causes of Action
    CLAIM = "claim"
    CAUSE_OF_ACTION = "cause_of_action"
    COUNTERCLAIM = "counterclaim"
    
    # Legal Concepts
    STATUTE = "statute"
    REGULATION = "regulation"
    CASE_LAW = "case_law"
    LEGAL_STANDARD = "legal_standard"
    LEGAL_PRINCIPLE = "legal_principle"
    
    # Jurisdictional and Procedural
    JURISDICTION = "jurisdiction"
    VENUE = "venue"
    COURT = "court"
    CASE_NUMBER = "case_number"
    
    # Temporal and Factual
    EVENT = "event"
    DATE = "date"
    DEADLINE = "deadline"
    FACT = "fact"
    EVIDENCE = "evidence"
    
    # Financial and Damages
    DAMAGES = "damages"
    AMOUNT = "amount"
    CONTRACT = "contract"
    
    # Document Types
    DOCUMENT = "document"
    EXHIBIT = "exhibit"
    FILING = "filing"
```

## Entity Schema

```python
@dataclass
class LegalEntity:
    """Enhanced entity with legal domain-specific attributes"""
    
    # Core identification
    id: str
    type: EntityType
    name: str
    canonical_name: Optional[str] = None
    
    # Content and context
    description: Optional[str] = None
    source_text: Optional[str] = None
    context_window: Optional[str] = None
    
    # Metadata
    confidence: float = 1.0
    extraction_method: str = "manual"  # manual, ner, pattern, llm
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    
    # Source tracking
    source_documents: List[str] = None
    page_numbers: List[int] = None
    character_offsets: List[tuple] = None
    
    # Legal-specific attributes
    legal_attributes: Dict[str, Any] = None
    
    # Semantic representation
    embeddings: Optional[List[float]] = None
    
    # Validation status
    verified: bool = False
    verification_source: Optional[str] = None
    
    def __post_init__(self):
        if self.source_documents is None:
            self.source_documents = []
        if self.page_numbers is None:
            self.page_numbers = []
        if self.character_offsets is None:
            self.character_offsets = []
        if self.legal_attributes is None:
            self.legal_attributes = {}
```

## Legal-Specific Attribute Schemas

### Party Attributes
```python
@dataclass
class PartyAttributes:
    party_type: str  # individual, corporation, government_entity
    address: Optional[str] = None
    attorney: Optional[str] = None
    represented: bool = True
    service_address: Optional[str] = None
```

### Claim Attributes
```python
@dataclass
class ClaimAttributes:
    claim_type: str  # breach_of_contract, negligence, discrimination, etc.
    elements: List[str] = None  # Required legal elements
    damages_sought: Optional[str] = None
    statute_of_limitations: Optional[str] = None
    jurisdiction_requirements: List[str] = None
```

### Statute Attributes
```python
@dataclass
class StatuteAttributes:
    citation: str
    jurisdiction: str
    effective_date: Optional[datetime] = None
    superseded_by: Optional[str] = None
    elements: List[str] = None
    penalties: List[str] = None
```

### Case Law Attributes
```python
@dataclass
class CaseLawAttributes:
    citation: str
    court: str
    decided_date: datetime
    holding: str
    legal_principle: List[str] = None
    distinguishing_factors: List[str] = None
    overruled: bool = False
```

## Relationship Types and Schema

```python
class RelationshipType(Enum):
    # Party relationships
    REPRESENTS = "represents"  # attorney represents client
    OPPOSES = "opposes"  # plaintiff opposes defendant
    
    # Claim relationships  
    ASSERTS = "asserts"  # party asserts claim
    SUPPORTS = "supports"  # evidence supports claim
    CONTRADICTS = "contradicts"  # evidence contradicts claim
    
    # Legal authority relationships
    CITES = "cites"  # document cites case/statute
    GOVERNS = "governs"  # statute governs situation
    APPLIES_TO = "applies_to"  # legal principle applies to fact
    
    # Temporal relationships
    OCCURS_BEFORE = "occurs_before"
    OCCURS_AFTER = "occurs_after"
    CONTEMPORANEOUS_WITH = "contemporaneous_with"
    
    # Procedural relationships
    FILED_IN = "filed_in"  # case filed in court
    SUBJECT_TO = "subject_to"  # party subject to jurisdiction
    
    # Evidence relationships
    PROVES = "proves"  # evidence proves fact
    DISPROVES = "disproves"  # evidence disproves fact
    CORROBORATES = "corroborates"  # evidence corroborates other evidence

@dataclass
class LegalRelationship:
    """Enhanced relationship with legal domain context"""
    
    # Core relationship
    from_entity: str
    to_entity: str
    relationship_type: RelationshipType
    
    # Confidence and validation
    confidence: float = 1.0
    extraction_method: str = "manual"
    verified: bool = False
    
    # Context and evidence
    supporting_text: Optional[str] = None
    source_documents: List[str] = None
    page_references: List[int] = None
    
    # Temporal context
    temporal_context: Optional[str] = None  # "during contract period", "before filing"
    
    # Legal significance
    legal_significance: Optional[str] = None  # "establishes standing", "proves causation"
    
    # Metadata
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    
    def __post_init__(self):
        if self.source_documents is None:
            self.source_documents = []
        if self.page_references is None:
            self.page_references = []
```

## NER Integration Specifications

### Entity Extraction Patterns

```python
class NERPatterns:
    """Legal domain-specific NER patterns"""
    
    PARTY_PATTERNS = [
        r"\b([A-Z][a-z]+ (?:[A-Z][a-z]+ )*(?:Inc\.|LLC|Corp\.|Co\.)?)\b",
        r"\bPlaintiff[s]?\s+([A-Z][a-z]+ (?:[A-Z][a-z]+ )*)",
        r"\bDefendant[s]?\s+([A-Z][a-z]+ (?:[A-Z][a-z]+ )*)",
    ]
    
    CITATION_PATTERNS = [
        r"\b\d+\s+[A-Z][a-z\.]+\s+\d+\b",  # 123 F.3d 456
        r"\b\d+\s+U\.S\.C\.\s+§?\s*\d+",  # 42 U.S.C. § 1983
        r"\bCal\.\s*(?:Civ\.|Gov\.|Penal)\s*Code\s*§?\s*\d+",  # Cal. Civ. Code § 1234
    ]
    
    DATE_PATTERNS = [
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
        r"\b\d{1,2}/\d{1,2}/\d{4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b"
    ]
    
    CLAIM_PATTERNS = [
        r"\b(?:breach of|violation of|negligent|discrimination|harassment|defamation)\b",
        r"\bCause of Action\s*(?:No\.)?\s*\d*:?\s*([A-Z][a-z ]+)",
    ]
```

### NER Service Interface

```python
class NERService:
    """Named Entity Recognition service for legal documents"""
    
    def __init__(self):
        self.spacy_model = "en_core_web_lg"  # or custom legal model
        self.patterns = NERPatterns()
        self.legal_classifier = LegalEntityClassifier()
    
    async def extract_entities(self, text: str, document_id: str) -> List[LegalEntity]:
        """Extract legal entities from text"""
        entities = []
        
        # spaCy NER for general entities
        spacy_entities = self._extract_with_spacy(text)
        
        # Pattern-based extraction for legal-specific entities
        pattern_entities = self._extract_with_patterns(text)
        
        # LLM-based extraction for complex entities
        llm_entities = await self._extract_with_llm(text)
        
        # Merge and deduplicate
        all_entities = spacy_entities + pattern_entities + llm_entities
        entities = self._deduplicate_entities(all_entities)
        
        # Add source metadata
        for entity in entities:
            entity.source_documents = [document_id]
            entity.source_text = text
        
        return entities
    
    def _extract_with_spacy(self, text: str) -> List[LegalEntity]:
        """Extract entities using spaCy"""
        # Implementation details
        pass
    
    def _extract_with_patterns(self, text: str) -> List[LegalEntity]:
        """Extract entities using regex patterns"""
        # Implementation details
        pass
    
    async def _extract_with_llm(self, text: str) -> List[LegalEntity]:
        """Extract complex entities using LLM"""
        # Implementation details
        pass
```

## Knowledge Graph Storage Schema

### SQLite Database Schema

```sql
-- Entities table
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    canonical_name TEXT,
    description TEXT,
    source_text TEXT,
    context_window TEXT,
    confidence REAL DEFAULT 1.0,
    extraction_method TEXT DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    legal_attributes TEXT, -- JSON serialized
    embeddings BLOB, -- Vector embeddings
    verified BOOLEAN DEFAULT FALSE,
    verification_source TEXT
);

-- Relationships table
CREATE TABLE relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_entity TEXT NOT NULL,
    to_entity TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    extraction_method TEXT DEFAULT 'manual',
    verified BOOLEAN DEFAULT FALSE,
    supporting_text TEXT,
    temporal_context TEXT,
    legal_significance TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_entity) REFERENCES entities (id),
    FOREIGN KEY (to_entity) REFERENCES entities (id)
);

-- Document sources table
CREATE TABLE document_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    page_number INTEGER,
    char_start INTEGER,
    char_end INTEGER,
    FOREIGN KEY (entity_id) REFERENCES entities (id)
);

-- Observations table (enhanced from existing)
CREATE TABLE observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    entity_id TEXT,
    relationship_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    observation_type TEXT DEFAULT 'system',
    FOREIGN KEY (entity_id) REFERENCES entities (id),
    FOREIGN KEY (relationship_id) REFERENCES relationships (id)
);

-- Indexes for performance
CREATE INDEX idx_entities_type ON entities (type);
CREATE INDEX idx_entities_name ON entities (name);
CREATE INDEX idx_relationships_from ON relationships (from_entity);
CREATE INDEX idx_relationships_to ON relationships (to_entity);
CREATE INDEX idx_relationships_type ON relationships (relationship_type);
CREATE INDEX idx_document_sources_entity ON document_sources (entity_id);
CREATE INDEX idx_document_sources_document ON document_sources (document_id);
```

## Semantic Search Integration

### Vector Embeddings

```python
class SemanticSearchService:
    """Semantic search using vector embeddings"""
    
    def __init__(self):
        self.embedding_model = "text-embedding-ada-002"  # OpenAI
        self.dimension = 1536
        self.similarity_threshold = 0.7
    
    async def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for text using OpenAI"""
        # Implementation using OpenAI embeddings API
        pass
    
    async def find_similar_entities(self, query: str, limit: int = 10) -> List[LegalEntity]:
        """Find entities similar to query text"""
        query_embedding = await self.generate_embeddings(query)
        # Vector similarity search in database
        pass
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        # Implementation of cosine similarity
        pass
```

## Knowledge Graph Operations

### Core Graph Operations

```python
class EnhancedKnowledgeGraph:
    """Enhanced knowledge graph with legal domain support"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.ner_service = NERService()
        self.semantic_search = SemanticSearchService()
    
    async def add_entity(self, entity: LegalEntity) -> str:
        """Add entity with validation and deduplication"""
        # Check for existing entity
        existing = await self.find_similar_entities(entity.name)
        if existing:
            return await self._merge_or_link_entity(entity, existing[0])
        
        # Generate embeddings
        if entity.description:
            entity.embeddings = await self.semantic_search.generate_embeddings(
                f"{entity.name} {entity.description}"
            )
        
        # Store in database
        return await self._store_entity(entity)
    
    async def add_relationship(self, relationship: LegalRelationship) -> int:
        """Add relationship with validation"""
        # Validate entities exist
        if not await self._entity_exists(relationship.from_entity):
            raise ValueError(f"From entity {relationship.from_entity} does not exist")
        if not await self._entity_exists(relationship.to_entity):
            raise ValueError(f"To entity {relationship.to_entity} does not exist")
        
        # Check for conflicting relationships
        conflicts = await self._check_relationship_conflicts(relationship)
        if conflicts:
            await self._resolve_conflicts(relationship, conflicts)
        
        return await self._store_relationship(relationship)
    
    async def extract_entities_from_document(self, document_text: str, document_id: str) -> List[LegalEntity]:
        """Extract and store entities from document"""
        entities = await self.ner_service.extract_entities(document_text, document_id)
        
        stored_entities = []
        for entity in entities:
            entity_id = await self.add_entity(entity)
            stored_entities.append(entity_id)
        
        return stored_entities
    
    async def find_legal_precedents(self, claim_type: str, jurisdiction: str) -> List[LegalEntity]:
        """Find relevant case law and statutes for a claim type"""
        # Search for relevant legal authorities
        query = f"{claim_type} {jurisdiction} case law statute"
        similar_entities = await self.semantic_search.find_similar_entities(query)
        
        # Filter for legal authorities
        precedents = [
            entity for entity in similar_entities 
            if entity.type in [EntityType.CASE_LAW, EntityType.STATUTE, EntityType.REGULATION]
        ]
        
        return precedents
    
    async def build_case_timeline(self, case_entities: List[str]) -> List[tuple]:
        """Build chronological timeline of case events"""
        # Find temporal relationships between entities
        timeline_query = """
        SELECT e1.name, r.relationship_type, e2.name, e1.legal_attributes, e2.legal_attributes
        FROM relationships r
        JOIN entities e1 ON r.from_entity = e1.id
        JOIN entities e2 ON r.to_entity = e2.id
        WHERE (r.from_entity IN ({}) OR r.to_entity IN ({}))
        AND r.relationship_type IN ('occurs_before', 'occurs_after', 'contemporaneous_with')
        ORDER BY e1.created_at
        """.format(','.join(['?']*len(case_entities)), ','.join(['?']*len(case_entities)))
        
        # Execute query and build timeline
        # Implementation details
        pass
```

This enhanced knowledge graph schema provides the foundation for sophisticated legal entity processing, relationship mapping, and semantic search capabilities that will power the LawyerFactory's automated lawsuit generation system.