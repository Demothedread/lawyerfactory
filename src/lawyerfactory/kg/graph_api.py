"""
# Script Name: enhanced_graph.py
# Description: Enhanced Knowledge Graph for Legal Entity Relationship Mapping Extends the base knowledge graph with advanced legal relationship detection, confidence scoring, and temporal sequencing capabilities.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Research
#   - Group Tags: knowledge-graph
Enhanced Knowledge Graph for Legal Entity Relationship Mapping
Extends the base knowledge graph with advanced legal relationship detection,
confidence scoring, and temporal sequencing capabilities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
from typing import Any, Dict, List, Optional
import uuid

from lawyerfactory.knowledge_graph.api.graph_api import KnowledgeGraph

logger = logging.getLogger(__name__)


class LegalEntityType(Enum):
    """Legal-specific entity types for enhanced classification"""

    # Parties and People
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    ATTORNEY = "attorney"
    JUDGE = "judge"
    WITNESS = "witness"
    EXPERT_WITNESS = "expert_witness"

    # Legal Claims and Causes
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


class LegalRelationshipType(Enum):
    """Legal-specific relationship types with legal significance"""

    # Causal relationships
    CAUSES = "causes"
    RESULTS_IN = "results_in"
    LEADS_TO = "leads_to"

    # Temporal relationships
    OCCURS_BEFORE = "occurs_before"
    OCCURS_AFTER = "occurs_after"
    CONTEMPORANEOUS_WITH = "contemporaneous_with"
    DURING = "during"

    # Legal relationships
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    ESTABLISHES = "establishes"
    REFUTES = "refutes"
    PROVES = "proves"
    DISPROVES = "disproves"

    # Party relationships
    PLAINTIFF_DEFENDANT = "plaintiff_defendant"
    ATTORNEY_CLIENT = "attorney_client"
    PARTY_TO = "party_to"
    REPRESENTS = "represents"

    # Evidence relationships
    EVIDENCED_BY = "evidenced_by"
    DOCUMENTED_IN = "documented_in"
    REFERENCED_IN = "referenced_in"

    # Logical relationships
    DEPENDS_ON = "depends_on"
    REQUIRES = "requires"
    IMPLIES = "implies"

    # Conflict relationships
    INCONSISTENT_WITH = "inconsistent_with"
    CONFLICTS_WITH = "conflicts_with"


@dataclass
class ConfidenceFactors:
    """Multi-dimensional confidence scoring factors"""

    source_credibility: float = 0.5  # 0-1 scale
    extraction_method_reliability: float = 0.8  # NER vs manual vs pattern
    evidence_support: float = 0.0  # Supporting evidence strength
    temporal_consistency: float = 1.0  # Timeline consistency
    cross_validation: float = 0.0  # Validation from other sources
    legal_precedence: float = 0.5  # Legal authority/precedence

    def calculate_overall_confidence(self) -> float:
        """Calculate weighted overall confidence score"""
        weights = {
            "source_credibility": 0.25,
            "extraction_method_reliability": 0.20,
            "evidence_support": 0.20,
            "temporal_consistency": 0.15,
            "cross_validation": 0.15,
            "legal_precedence": 0.05,
        }

        weighted_sum = (
            self.source_credibility * weights["source_credibility"]
            + self.extraction_method_reliability * weights["extraction_method_reliability"]
            + self.evidence_support * weights["evidence_support"]
            + self.temporal_consistency * weights["temporal_consistency"]
            + self.cross_validation * weights["cross_validation"]
            + self.legal_precedence * weights["legal_precedence"]
        )

        return min(1.0, max(0.0, weighted_sum))


@dataclass
class CauseOfAction:
    """Represents a cause of action with jurisdiction-specific definition"""

    id: Optional[int] = None
    jurisdiction: str = ""
    cause_name: str = ""
    legal_definition: Optional[str] = None
    authority_citation: Optional[str] = None
    federal_preempted: bool = False
    confidence_threshold: float = 0.7
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = field(default_factory=datetime.now)


@dataclass
class LegalElement:
    """Represents a legal element within a cause of action"""

    id: Optional[int] = None
    cause_of_action_id: int = 0
    element_name: str = ""
    element_order: int = 1
    element_definition: Optional[str] = None
    authority_citation: Optional[str] = None
    burden_of_proof: str = (
        "preponderance"  # preponderance, clear_and_convincing, beyond_reasonable_doubt
    )
    created_at: Optional[datetime] = field(default_factory=datetime.now)


@dataclass
class ElementQuestion:
    """Represents a provable question for a legal element"""

    id: Optional[int] = None
    legal_element_id: int = 0
    question_text: str = ""
    question_order: int = 1
    question_type: str = "factual"  # factual, legal, mixed
    suggested_evidence_types: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = field(default_factory=datetime.now)


@dataclass
class JurisdictionAuthority:
    """Represents legal authority within a jurisdiction"""

    id: Optional[int] = None
    jurisdiction: str = ""
    authority_type: str = ""  # constitution, statute, regulation, case_law
    authority_name: str = ""
    authority_citation: Optional[str] = None
    precedence_level: int = 5  # 1=highest, 10=lowest
    federal_preemption_scope: str = "none"  # none, partial, complete
    effective_date: Optional[str] = None
    superseded_date: Optional[str] = None
    created_at: Optional[datetime] = field(default_factory=datetime.now)


@dataclass
class FactElementAttachment:
    """Represents attachment of case facts to legal elements"""

    id: Optional[int] = None
    fact_entity_id: str = ""
    legal_element_id: int = 0
    attachment_type: str = "supports"  # supports, contradicts, neutral
    relevance_score: float = 0.5
    confidence_score: float = 0.5
    attorney_reviewed: bool = False
    attachment_reasoning: Optional[str] = None
    created_at: Optional[datetime] = field(default_factory=datetime.now)


@dataclass
class LegalEntity:
    """Enhanced entity with legal domain-specific attributes"""

    id: str
    entity_type: LegalEntityType
    name: str
    canonical_name: Optional[str] = None
    description: Optional[str] = None
    source_text: Optional[str] = None
    context_window: Optional[str] = None
    confidence_factors: Optional[ConfidenceFactors] = field(default_factory=ConfidenceFactors)
    extraction_method: str = "manual"
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = field(default_factory=datetime.now)
    source_documents: List[str] = field(default_factory=list)
    legal_attributes: Dict[str, Any] = field(default_factory=dict)
    verified: bool = False
    verification_source: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.confidence_factors is None:
            self.confidence_factors = ConfidenceFactors()

    @property
    def overall_confidence(self) -> float:
        """Get the overall confidence score for this entity"""
        if self.confidence_factors:
            return self.confidence_factors.calculate_overall_confidence()
        return 0.5


@dataclass
class LegalRelationship:
    """Enhanced relationship with legal domain context and confidence"""

    from_entity: str
    to_entity: str
    relationship_type: LegalRelationshipType
    confidence_factors: Optional[ConfidenceFactors] = field(default_factory=ConfidenceFactors)
    extraction_method: str = "manual"
    verified: bool = False
    supporting_text: Optional[str] = None
    source_documents: List[str] = field(default_factory=list)
    temporal_context: Optional[str] = None
    legal_significance: Optional[str] = None
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = field(default_factory=datetime.now)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.confidence_factors is None:
            self.confidence_factors = ConfidenceFactors()

    @property
    def overall_confidence(self) -> float:
        """Get the overall confidence score for this relationship"""
        if self.confidence_factors:
            return self.confidence_factors.calculate_overall_confidence()
        return 0.5


class EnhancedKnowledgeGraph(KnowledgeGraph):
    """Enhanced knowledge graph with legal relationship capabilities"""

    def __init__(self, db_path: str = "knowledge_graph.db", key: str = ""):
        super().__init__(db_path, key)
        self._initialize_enhanced_schema()

    def _initialize_enhanced_schema(self):
        """Initialize enhanced schema for legal relationships"""
        enhanced_sql = """
        -- Enhanced entity confidence tracking
        CREATE TABLE IF NOT EXISTS entity_confidence_metrics (
            entity_id TEXT NOT NULL,
            source_credibility REAL DEFAULT 0.5,
            extraction_method_reliability REAL DEFAULT 0.8,
            evidence_support REAL DEFAULT 0.0,
            temporal_consistency REAL DEFAULT 1.0,
            cross_validation REAL DEFAULT 0.0,
            legal_precedence REAL DEFAULT 0.5,
            overall_confidence REAL DEFAULT 0.5,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (entity_id) REFERENCES entities (id)
        );
        
        -- Temporal context for entities
        CREATE TABLE IF NOT EXISTS entity_temporal_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id TEXT NOT NULL,
            temporal_type TEXT, -- absolute_date, relative_time, duration
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            temporal_description TEXT,
            confidence REAL DEFAULT 1.0,
            FOREIGN KEY (entity_id) REFERENCES entities (id)
        );
        
        -- Enhanced relationships with confidence factors
        CREATE TABLE IF NOT EXISTS legal_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_entity TEXT NOT NULL,
            to_entity TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            source_credibility REAL DEFAULT 0.5,
            extraction_method_reliability REAL DEFAULT 0.8,
            evidence_support REAL DEFAULT 0.0,
            temporal_consistency REAL DEFAULT 1.0,
            cross_validation REAL DEFAULT 0.0,
            legal_precedence REAL DEFAULT 0.5,
            overall_confidence REAL DEFAULT 0.5,
            extraction_method TEXT DEFAULT 'manual',
            verified BOOLEAN DEFAULT FALSE,
            supporting_text TEXT,
            temporal_context TEXT,
            legal_significance TEXT,
            source_documents TEXT, -- JSON array
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_entity) REFERENCES entities (id),
            FOREIGN KEY (to_entity) REFERENCES entities (id)
        );
        
        -- Relationship evidence support tracking
        CREATE TABLE IF NOT EXISTS relationship_evidence_support (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            relationship_id INTEGER NOT NULL,
            evidence_entity_id TEXT,
            support_strength REAL DEFAULT 0.5,
            evidence_type TEXT, -- direct, circumstantial, expert_opinion
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (relationship_id) REFERENCES legal_relationships (id),
            FOREIGN KEY (evidence_entity_id) REFERENCES entities (id)
        );
        
        -- Temporal event sequencing
        CREATE TABLE IF NOT EXISTS temporal_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id TEXT NOT NULL,
            event_type TEXT, -- fact, action, decision, filing
            sequence_order INTEGER,
            absolute_timestamp TIMESTAMP,
            relative_description TEXT,
            duration_minutes INTEGER,
            certainty_level REAL DEFAULT 0.5,
            source_description TEXT,
            FOREIGN KEY (entity_id) REFERENCES entities (id)
        );
        
        -- Fact conflicts and resolutions
        CREATE TABLE IF NOT EXISTS fact_conflicts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_a_id TEXT NOT NULL,
            entity_b_id TEXT NOT NULL,
            conflict_type TEXT, -- contradiction, inconsistency, ambiguity
            severity TEXT, -- high, medium, low
            resolution_strategy TEXT,
            resolved_entity_id TEXT,
            resolution_confidence REAL,
            attorney_reviewed BOOLEAN DEFAULT FALSE,
            resolution_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (entity_a_id) REFERENCES entities (id),
            FOREIGN KEY (entity_b_id) REFERENCES entities (id),
            FOREIGN KEY (resolved_entity_id) REFERENCES entities (id)
        );
        
        -- Draft document metadata
        CREATE TABLE IF NOT EXISTS draft_documents (
            id TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            draft_type TEXT, -- fact_statement, case_complaint
            priority_level INTEGER DEFAULT 5,
            author_credibility REAL DEFAULT 0.5,
            creation_date TIMESTAMP,
            processing_status TEXT DEFAULT 'pending',
            fact_count INTEGER DEFAULT 0,
            conflict_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Claims Matrix Tables for Phase 3.1
        CREATE TABLE IF NOT EXISTS causes_of_action (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jurisdiction TEXT NOT NULL,
            cause_name TEXT NOT NULL,
            legal_definition TEXT,
            authority_citation TEXT,
            federal_preempted BOOLEAN DEFAULT FALSE,
            confidence_threshold REAL DEFAULT 0.7,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(jurisdiction, cause_name)
        );
        
        -- Legal elements for each cause of action
        CREATE TABLE IF NOT EXISTS legal_elements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cause_of_action_id INTEGER NOT NULL,
            element_name TEXT NOT NULL,
            element_order INTEGER DEFAULT 1,
            element_definition TEXT,
            authority_citation TEXT,
            burden_of_proof TEXT, -- preponderance, clear_and_convincing, beyond_reasonable_doubt
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cause_of_action_id) REFERENCES causes_of_action (id),
            UNIQUE(cause_of_action_id, element_name)
        );
        
        -- Provable questions for each legal element
        CREATE TABLE IF NOT EXISTS element_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            legal_element_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            question_order INTEGER DEFAULT 1,
            question_type TEXT DEFAULT 'factual', -- factual, legal, mixed
            suggested_evidence_types TEXT, -- JSON array of evidence types
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (legal_element_id) REFERENCES legal_elements (id)
        );
        
        -- Jurisdiction-specific legal authorities
        CREATE TABLE IF NOT EXISTS jurisdiction_authorities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jurisdiction TEXT NOT NULL,
            authority_type TEXT NOT NULL, -- constitution, statute, regulation, case_law
            authority_name TEXT NOT NULL,
            authority_citation TEXT,
            precedence_level INTEGER DEFAULT 5, -- 1=highest, 10=lowest
            federal_preemption_scope TEXT, -- none, partial, complete
            effective_date DATE,
            superseded_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(jurisdiction, authority_citation)
        );
        
        -- Fact-to-element attachments for case building
        CREATE TABLE IF NOT EXISTS fact_element_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact_entity_id TEXT NOT NULL,
            legal_element_id INTEGER NOT NULL,
            attachment_type TEXT DEFAULT 'supports', -- supports, contradicts, neutral
            relevance_score REAL DEFAULT 0.5,
            confidence_score REAL DEFAULT 0.5,
            attorney_reviewed BOOLEAN DEFAULT FALSE,
            attachment_reasoning TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fact_entity_id) REFERENCES entities (id),
            FOREIGN KEY (legal_element_id) REFERENCES legal_elements (id),
            UNIQUE(fact_entity_id, legal_element_id)
        );
        
        -- Legal research cache for external API results
        CREATE TABLE IF NOT EXISTS legal_research_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jurisdiction TEXT NOT NULL,
            search_query TEXT NOT NULL,
            api_source TEXT NOT NULL, -- courtlistener, google_scholar, openalex
            result_data TEXT, -- JSON response
            relevance_score REAL DEFAULT 0.5,
            cache_expiry TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Legal definition cache per jurisdiction
        CREATE TABLE IF NOT EXISTS definition_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jurisdiction TEXT NOT NULL,
            legal_term TEXT NOT NULL,
            definition_text TEXT,
            authority_citation TEXT,
            confidence_score REAL DEFAULT 0.7,
            cache_expiry TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(jurisdiction, legal_term)
        );
        
        -- Case law cache with relevance scoring
        CREATE TABLE IF NOT EXISTS case_law_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jurisdiction TEXT NOT NULL,
            cause_of_action TEXT,
            case_citation TEXT NOT NULL,
            case_summary TEXT,
            relevance_score REAL DEFAULT 0.5,
            authority_level INTEGER DEFAULT 5, -- 1=supreme_court, 5=trial_court
            decision_date DATE,
            cache_expiry TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_entity_confidence ON entity_confidence_metrics(entity_id);
        CREATE INDEX IF NOT EXISTS idx_temporal_context ON entity_temporal_context(entity_id);
        CREATE INDEX IF NOT EXISTS idx_legal_relationships_from ON legal_relationships(from_entity);
        CREATE INDEX IF NOT EXISTS idx_legal_relationships_to ON legal_relationships(to_entity);
        CREATE INDEX IF NOT EXISTS idx_legal_relationships_type ON legal_relationships(relationship_type);
        CREATE INDEX IF NOT EXISTS idx_temporal_events_entity ON temporal_events(entity_id);
        CREATE INDEX IF NOT EXISTS idx_temporal_events_order ON temporal_events(sequence_order);
        CREATE INDEX IF NOT EXISTS idx_fact_conflicts_entities ON fact_conflicts(entity_a_id, entity_b_id);
        
        -- Claims Matrix indexes for performance optimization
        CREATE INDEX IF NOT EXISTS idx_causes_jurisdiction ON causes_of_action(jurisdiction);
        CREATE INDEX IF NOT EXISTS idx_legal_elements_cause ON legal_elements(cause_of_action_id);
        CREATE INDEX IF NOT EXISTS idx_element_questions_element ON element_questions(legal_element_id);
        CREATE INDEX IF NOT EXISTS idx_jurisdiction_authorities_jurisdiction ON jurisdiction_authorities(jurisdiction);
        CREATE INDEX IF NOT EXISTS idx_fact_attachments_element ON fact_element_attachments(legal_element_id);
        CREATE INDEX IF NOT EXISTS idx_fact_attachments_fact ON fact_element_attachments(fact_entity_id);
        
        -- Additional indexes for the research and case law cache tables
        CREATE INDEX IF NOT EXISTS idx_research_cache_jurisdiction_query ON legal_research_cache(jurisdiction, search_query);
        CREATE INDEX IF NOT EXISTS idx_research_cache_expiry ON legal_research_cache(cache_expiry);
        CREATE INDEX IF NOT EXISTS idx_case_law_jurisdiction_cause ON case_law_cache(jurisdiction, cause_of_action);
        CREATE INDEX IF NOT EXISTS idx_case_law_relevance ON case_law_cache(relevance_score DESC);
        """

        try:
            cursor = self.conn.cursor()
            cursor.executescript(enhanced_sql)
            cursor.close()
            self.conn.commit()
            logger.info("Enhanced knowledge graph schema initialized successfully")
        except Exception as e:
            logger.exception("Failed to initialize enhanced schema: %s", e)
            raise

    def add_legal_entity(self, entity: LegalEntity) -> str:
        """Add a legal entity with enhanced confidence tracking"""
        try:
            # Insert into base entities table
            self._execute(
                """
                INSERT OR REPLACE INTO entities
                (id, type, name, canonical_name, description, source_text,
                 context_window, confidence, extraction_method, legal_attributes,
                 verified, verification_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    entity.id,
                    entity.entity_type.value,
                    entity.name,
                    entity.canonical_name,
                    entity.description,
                    entity.source_text,
                    entity.context_window,
                    entity.overall_confidence,
                    entity.extraction_method,
                    (json.dumps(entity.legal_attributes) if entity.legal_attributes else None),
                    entity.verified,
                    entity.verification_source,
                ),
            )

            # Insert confidence factors
            cf = entity.confidence_factors or ConfidenceFactors()
            self._execute(
                """
                INSERT OR REPLACE INTO entity_confidence_metrics
                (entity_id, source_credibility, extraction_method_reliability,
                 evidence_support, temporal_consistency, cross_validation,
                 legal_precedence, overall_confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    entity.id,
                    cf.source_credibility,
                    cf.extraction_method_reliability,
                    cf.evidence_support,
                    cf.temporal_consistency,
                    cf.cross_validation,
                    cf.legal_precedence,
                    entity.overall_confidence,
                ),
            )

            logger.info(
                f"Added legal entity: {entity.name} ({entity.entity_type.value}) with confidence {entity.overall_confidence:.2f}"
            )
            return entity.id

        except Exception as e:
            logger.exception(f"Failed to add legal entity {entity.name}: {e}")
            raise

    def add_legal_relationship(self, relationship: LegalRelationship) -> int:
        """Add a legal relationship with enhanced confidence tracking"""
        try:
            cursor = self.conn.cursor()
            cf = relationship.confidence_factors or ConfidenceFactors()

            cursor.execute(
                """
                INSERT INTO legal_relationships
                (from_entity, to_entity, relationship_type, source_credibility,
                 extraction_method_reliability, evidence_support, temporal_consistency,
                 cross_validation, legal_precedence, overall_confidence,
                 extraction_method, verified, supporting_text, temporal_context,
                 legal_significance, source_documents)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    relationship.from_entity,
                    relationship.to_entity,
                    relationship.relationship_type.value,
                    cf.source_credibility,
                    cf.extraction_method_reliability,
                    cf.evidence_support,
                    cf.temporal_consistency,
                    cf.cross_validation,
                    cf.legal_precedence,
                    relationship.overall_confidence,
                    relationship.extraction_method,
                    relationship.verified,
                    relationship.supporting_text,
                    relationship.temporal_context,
                    relationship.legal_significance,
                    (
                        json.dumps(relationship.source_documents)
                        if relationship.source_documents
                        else None
                    ),
                ),
            )

            relationship_id = cursor.lastrowid or 0
            self.conn.commit()
            cursor.close()

            logger.info(
                f"Added legal relationship: {relationship.relationship_type.value} between {relationship.from_entity} and {relationship.to_entity} with confidence {relationship.overall_confidence:.2f}"
            )
            return relationship_id

        except Exception as e:
            logger.exception(f"Failed to add legal relationship: {e}")
            raise

    def get_entity_legal_relationships(
        self,
        entity_id: str,
        relationship_types: Optional[List[LegalRelationshipType]] = None,
        min_confidence: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Get legal relationships for an entity with filtering options"""
        try:
            base_query = """
                SELECT lr.*, e1.name as from_name, e2.name as to_name
                FROM legal_relationships lr
                JOIN entities e1 ON lr.from_entity = e1.id
                JOIN entities e2 ON lr.to_entity = e2.id
                WHERE (lr.from_entity = ? OR lr.to_entity = ?)
                AND lr.overall_confidence >= ?
            """
            params = [entity_id, entity_id, min_confidence]

            if relationship_types:
                type_placeholders = ",".join(["?" for _ in relationship_types])
                base_query += f" AND lr.relationship_type IN ({type_placeholders})"
                params.extend([rt.value for rt in relationship_types])

            base_query += " ORDER BY lr.overall_confidence DESC"

            rows = self._fetchall(base_query, tuple(params))

            relationships = []
            for row in rows:
                relationships.append(
                    {
                        "id": row[0],
                        "from_entity": row[1],
                        "to_entity": row[2],
                        "relationship_type": row[3],
                        "overall_confidence": row[10],
                        "extraction_method": row[11],
                        "verified": row[12],
                        "supporting_text": row[13],
                        "temporal_context": row[14],
                        "legal_significance": row[15],
                        "source_documents": json.loads(row[16]) if row[16] else [],
                        "from_name": row[18],
                        "to_name": row[19],
                        "direction": "outgoing" if row[1] == entity_id else "incoming",
                    }
                )

            return relationships

        except Exception as e:
            logger.exception(f"Failed to get legal relationships for entity {entity_id}: {e}")
            return []

    def update_entity_confidence(self, entity_id: str, confidence_factors: ConfidenceFactors):
        """Update confidence factors for an entity"""
        try:
            overall_confidence = confidence_factors.calculate_overall_confidence()

            # Update confidence metrics
            self._execute(
                """
                UPDATE entity_confidence_metrics SET
                source_credibility = ?, extraction_method_reliability = ?,
                evidence_support = ?, temporal_consistency = ?,
                cross_validation = ?, legal_precedence = ?,
                overall_confidence = ?, last_updated = CURRENT_TIMESTAMP
                WHERE entity_id = ?
            """,
                (
                    confidence_factors.source_credibility,
                    confidence_factors.extraction_method_reliability,
                    confidence_factors.evidence_support,
                    confidence_factors.temporal_consistency,
                    confidence_factors.cross_validation,
                    confidence_factors.legal_precedence,
                    overall_confidence,
                    entity_id,
                ),
            )

            # Update base entity confidence
            self._execute(
                """
                UPDATE entities SET confidence = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (overall_confidence, entity_id),
            )

            logger.info(f"Updated confidence for entity {entity_id}: {overall_confidence:.2f}")

        except Exception as e:
            logger.exception(f"Failed to update confidence for entity {entity_id}: {e}")
            raise

    def detect_fact_conflicts(self, min_similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Detect potential conflicts between facts/entities"""
        try:
            # Simple implementation - can be enhanced with semantic similarity
            conflicts = []

            # Find entities with similar names but different details
            similar_entities_query = """
                SELECT e1.id, e1.name, e1.description, e2.id, e2.name, e2.description
                FROM entities e1, entities e2
                WHERE e1.id < e2.id
                AND e1.type = e2.type
                AND (
                    LOWER(e1.name) = LOWER(e2.name) OR
                    (LENGTH(e1.name) > 3 AND LENGTH(e2.name) > 3 AND 
                     LOWER(e1.name) LIKE '%' || LOWER(e2.name) || '%')
                )
                AND (e1.description != e2.description OR e1.source_text != e2.source_text)
            """

            rows = self._fetchall(similar_entities_query)

            for row in rows:
                conflict = {
                    "entity_a_id": row[0],
                    "entity_a_name": row[1],
                    "entity_a_description": row[2],
                    "entity_b_id": row[3],
                    "entity_b_name": row[4],
                    "entity_b_description": row[5],
                    "conflict_type": "potential_duplicate",
                    "severity": "medium",
                }
                conflicts.append(conflict)

            # Store detected conflicts
            for conflict in conflicts:
                self._execute(
                    """
                    INSERT OR IGNORE INTO fact_conflicts
                    (entity_a_id, entity_b_id, conflict_type, severity)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        conflict["entity_a_id"],
                        conflict["entity_b_id"],
                        conflict["conflict_type"],
                        conflict["severity"],
                    ),
                )

            logger.info(f"Detected {len(conflicts)} potential fact conflicts")
            return conflicts

        except Exception as e:
            logger.exception(f"Failed to detect fact conflicts: {e}")
            return []

    def get_temporal_timeline(self, entity_ids: List[str]) -> List[Dict[str, Any]]:
        """Build chronological timeline for specified entities"""
        try:
            if not entity_ids:
                return []

            placeholders = ",".join(["?" for _ in entity_ids])
            timeline_query = f"""
                SELECT te.*, e.name, e.type
                FROM temporal_events te
                JOIN entities e ON te.entity_id = e.id
                WHERE te.entity_id IN ({placeholders})
                ORDER BY te.sequence_order ASC, te.absolute_timestamp ASC
            """

            rows = self._fetchall(timeline_query, tuple(entity_ids))

            timeline = []
            for row in rows:
                timeline.append(
                    {
                        "id": row[0],
                        "entity_id": row[1],
                        "entity_name": row[7],
                        "entity_type": row[8],
                        "event_type": row[2],
                        "sequence_order": row[3],
                        "absolute_timestamp": row[4],
                        "relative_description": row[5],
                        "duration_minutes": row[6],
                        "certainty_level": row[7],
                        "source_description": row[8],
                    }
                )

            return timeline

        except Exception as e:
            logger.exception(f"Failed to build temporal timeline: {e}")
            return []

    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics for the enhanced knowledge graph"""
        try:
            # Get base statistics using the parent class method if available
            base_stats = {}
            if hasattr(self, "get_entity_statistics"):
                try:
                    base_stats = super(EnhancedKnowledgeGraph, self).get_entity_statistics()
                except AttributeError:
                    # Fallback to basic entity count
                    total_entities = self._fetchone("SELECT COUNT(*) FROM entities")
                    base_stats = {"total_entities": total_entities[0] if total_entities else 0}

            # Enhanced statistics
            legal_relationship_counts = self._fetchall(
                """
                SELECT relationship_type, COUNT(*) 
                FROM legal_relationships 
                GROUP BY relationship_type 
                ORDER BY COUNT(*) DESC
            """
            )

            confidence_distribution = self._fetchone(
                """
                SELECT 
                    AVG(overall_confidence) as avg_confidence,
                    MIN(overall_confidence) as min_confidence,
                    MAX(overall_confidence) as max_confidence,
                    COUNT(*) as total_with_confidence
                FROM entity_confidence_metrics
            """
            )

            conflict_counts = self._fetchone(
                """
                SELECT COUNT(*) as total_conflicts,
                       SUM(CASE WHEN attorney_reviewed = 1 THEN 1 ELSE 0 END) as reviewed_conflicts
                FROM fact_conflicts
            """
            )

            enhanced_stats = {
                **base_stats,
                "legal_relationships": [
                    {"type": row[0], "count": row[1]} for row in legal_relationship_counts
                ],
                "confidence_metrics": {
                    "average": (confidence_distribution[0] if confidence_distribution else 0),
                    "minimum": (confidence_distribution[1] if confidence_distribution else 0),
                    "maximum": (confidence_distribution[2] if confidence_distribution else 0),
                    "entities_with_confidence": (
                        confidence_distribution[3] if confidence_distribution else 0
                    ),
                },
                "conflicts": {
                    "total": conflict_counts[0] if conflict_counts else 0,
                    "reviewed": conflict_counts[1] if conflict_counts else 0,
                },
            }

            return enhanced_stats

        except Exception as e:
            logger.exception(f"Failed to get enhanced statistics: {e}")
            return {}

    # ========== Claims Matrix Methods ==========

    def add_cause_of_action(self, cause: CauseOfAction) -> int:
        """Add a cause of action to the knowledge graph"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO causes_of_action
                (jurisdiction, cause_name, legal_definition, authority_citation,
                 federal_preempted, confidence_threshold)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    cause.jurisdiction,
                    cause.cause_name,
                    cause.legal_definition,
                    cause.authority_citation,
                    cause.federal_preempted,
                    cause.confidence_threshold,
                ),
            )

            cause_id = cursor.lastrowid
            cursor.close()
            self.conn.commit()

            logger.info(f"Added cause of action: {cause.cause_name} for {cause.jurisdiction}")
            return cause_id

        except Exception as e:
            logger.exception(f"Failed to add cause of action: {e}")
            raise

    def get_causes_of_action_by_jurisdiction(self, jurisdiction: str) -> List[Dict[str, Any]]:
        """Get all causes of action for a specific jurisdiction"""
        try:
            rows = self._fetchall(
                """
                SELECT id, jurisdiction, cause_name, legal_definition,
                       authority_citation, federal_preempted, confidence_threshold,
                       created_at, updated_at
                FROM causes_of_action
                WHERE jurisdiction = ?
                ORDER BY cause_name ASC
            """,
                (jurisdiction,),
            )

            causes = []
            for row in rows:
                causes.append(
                    {
                        "id": row[0],
                        "jurisdiction": row[1],
                        "cause_name": row[2],
                        "legal_definition": row[3],
                        "authority_citation": row[4],
                        "federal_preempted": bool(row[5]),
                        "confidence_threshold": row[6],
                        "created_at": row[7],
                        "updated_at": row[8],
                    }
                )

            return causes

        except Exception as e:
            logger.exception(f"Failed to get causes of action for jurisdiction {jurisdiction}: {e}")
            return []

    def add_legal_element(self, element: LegalElement) -> int:
        """Add a legal element to a cause of action"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO legal_elements
                (cause_of_action_id, element_name, element_order, element_definition,
                 authority_citation, burden_of_proof)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    element.cause_of_action_id,
                    element.element_name,
                    element.element_order,
                    element.element_definition,
                    element.authority_citation,
                    element.burden_of_proof,
                ),
            )

            element_id = cursor.lastrowid
            cursor.close()
            self.conn.commit()

            logger.info(
                f"Added legal element: {element.element_name} to cause {element.cause_of_action_id}"
            )
            return element_id

        except Exception as e:
            logger.exception(f"Failed to add legal element: {e}")
            raise

    def get_legal_elements_for_cause(self, cause_of_action_id: int) -> List[Dict[str, Any]]:
        """Get all legal elements for a specific cause of action"""
        try:
            rows = self._fetchall(
                """
                SELECT le.id, le.cause_of_action_id, le.element_name, le.element_order,
                       le.element_definition, le.authority_citation, le.burden_of_proof,
                       le.created_at, coa.cause_name, coa.jurisdiction
                FROM legal_elements le
                JOIN causes_of_action coa ON le.cause_of_action_id = coa.id
                WHERE le.cause_of_action_id = ?
                ORDER BY le.element_order ASC
            """,
                (cause_of_action_id,),
            )

            elements = []
            for row in rows:
                elements.append(
                    {
                        "id": row[0],
                        "cause_of_action_id": row[1],
                        "element_name": row[2],
                        "element_order": row[3],
                        "element_definition": row[4],
                        "authority_citation": row[5],
                        "burden_of_proof": row[6],
                        "created_at": row[7],
                        "cause_name": row[8],
                        "jurisdiction": row[9],
                    }
                )

            return elements

        except Exception as e:
            logger.exception(f"Failed to get legal elements for cause {cause_of_action_id}: {e}")
            return []

    def add_element_question(self, question: ElementQuestion) -> int:
        """Add a provable question to a legal element"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO element_questions
                (legal_element_id, question_text, question_order, question_type,
                 suggested_evidence_types)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    question.legal_element_id,
                    question.question_text,
                    question.question_order,
                    question.question_type,
                    json.dumps(question.suggested_evidence_types),
                ),
            )

            question_id = cursor.lastrowid
            cursor.close()
            self.conn.commit()

            logger.info(f"Added element question to legal element {question.legal_element_id}")
            return question_id

        except Exception as e:
            logger.exception(f"Failed to add element question: {e}")
            raise

    def get_element_questions(self, legal_element_id: int) -> List[Dict[str, Any]]:
        """Get all provable questions for a legal element"""
        try:
            rows = self._fetchall(
                """
                SELECT eq.id, eq.legal_element_id, eq.question_text, eq.question_order,
                       eq.question_type, eq.suggested_evidence_types, eq.created_at,
                       le.element_name
                FROM element_questions eq
                JOIN legal_elements le ON eq.legal_element_id = le.id
                WHERE eq.legal_element_id = ?
                ORDER BY eq.question_order ASC
            """,
                (legal_element_id,),
            )

            questions = []
            for row in rows:
                questions.append(
                    {
                        "id": row[0],
                        "legal_element_id": row[1],
                        "question_text": row[2],
                        "question_order": row[3],
                        "question_type": row[4],
                        "suggested_evidence_types": (json.loads(row[5]) if row[5] else []),
                        "created_at": row[6],
                        "element_name": row[7],
                    }
                )

            return questions

        except Exception as e:
            logger.exception(
                f"Failed to get element questions for legal element {legal_element_id}: {e}"
            )
            return []

    def attach_fact_to_element(self, attachment: FactElementAttachment) -> int:
        """Attach a case fact to a legal element"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO fact_element_attachments
                (fact_entity_id, legal_element_id, attachment_type, relevance_score,
                 confidence_score, attorney_reviewed, attachment_reasoning)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    attachment.fact_entity_id,
                    attachment.legal_element_id,
                    attachment.attachment_type,
                    attachment.relevance_score,
                    attachment.confidence_score,
                    attachment.attorney_reviewed,
                    attachment.attachment_reasoning,
                ),
            )

            attachment_id = cursor.lastrowid
            cursor.close()
            self.conn.commit()

            logger.info(
                f"Attached fact {attachment.fact_entity_id} to element {attachment.legal_element_id}"
            )
            return attachment_id

        except Exception as e:
            logger.exception(f"Failed to attach fact to element: {e}")
            raise

    def get_fact_attachments_for_element(self, legal_element_id: int) -> List[Dict[str, Any]]:
        """Get all fact attachments for a legal element"""
        try:
            rows = self._fetchall(
                """
                SELECT fea.id, fea.fact_entity_id, fea.legal_element_id, fea.attachment_type,
                       fea.relevance_score, fea.confidence_score, fea.attorney_reviewed,
                       fea.attachment_reasoning, fea.created_at,
                       e.name as fact_name, e.type as fact_type, le.element_name
                FROM fact_element_attachments fea
                JOIN entities e ON fea.fact_entity_id = e.id
                JOIN legal_elements le ON fea.legal_element_id = le.id
                WHERE fea.legal_element_id = ?
                ORDER BY fea.relevance_score DESC, fea.confidence_score DESC
            """,
                (legal_element_id,),
            )

            attachments = []
            for row in rows:
                attachments.append(
                    {
                        "id": row[0],
                        "fact_entity_id": row[1],
                        "legal_element_id": row[2],
                        "attachment_type": row[3],
                        "relevance_score": row[4],
                        "confidence_score": row[5],
                        "attorney_reviewed": bool(row[6]),
                        "attachment_reasoning": row[7],
                        "created_at": row[8],
                        "fact_name": row[9],
                        "fact_type": row[10],
                        "element_name": row[11],
                    }
                )

            return attachments

        except Exception as e:
            logger.exception(f"Failed to get fact attachments for element {legal_element_id}: {e}")
            return []

    def get_case_strength_analysis(self, cause_of_action_id: int) -> Dict[str, Any]:
        """Analyze case strength for a specific cause of action"""
        try:
            # Get all elements for the cause
            elements = self.get_legal_elements_for_cause(cause_of_action_id)

            if not elements:
                return {"error": "No legal elements found for cause of action"}

            element_analysis = []
            total_strength = 0.0

            for element in elements:
                # Get fact attachments for this element
                attachments = self.get_fact_attachments_for_element(element["id"])

                supporting_facts = [a for a in attachments if a["attachment_type"] == "supports"]
                contradicting_facts = [
                    a for a in attachments if a["attachment_type"] == "contradicts"
                ]

                support_score = sum(
                    a["relevance_score"] * a["confidence_score"] for a in supporting_facts
                )
                contradiction_score = sum(
                    a["relevance_score"] * a["confidence_score"] for a in contradicting_facts
                )

                element_strength = max(0.0, support_score - contradiction_score)
                total_strength += element_strength

                element_analysis.append(
                    {
                        "element_id": element["id"],
                        "element_name": element["element_name"],
                        "element_order": element["element_order"],
                        "supporting_facts_count": len(supporting_facts),
                        "contradicting_facts_count": len(contradicting_facts),
                        "support_score": support_score,
                        "contradiction_score": contradiction_score,
                        "element_strength": element_strength,
                        "burden_of_proof": element["burden_of_proof"],
                    }
                )

            overall_strength = total_strength / len(elements) if elements else 0.0

            return {
                "cause_of_action_id": cause_of_action_id,
                "overall_strength": overall_strength,
                "total_elements": len(elements),
                "elements_with_support": len(
                    [e for e in element_analysis if e["supporting_facts_count"] > 0]
                ),
                "elements_with_contradictions": len(
                    [e for e in element_analysis if e["contradicting_facts_count"] > 0]
                ),
                "element_analysis": element_analysis,
            }

        except Exception as e:
            logger.exception(f"Failed to analyze case strength for cause {cause_of_action_id}: {e}")
            return {"error": str(e)}

    def search_entities_by_type(self, entity_types: List[str]) -> List[Dict[str, Any]]:
        """Search for entities by their types"""
        try:
            if not entity_types:
                return []

            placeholders = ",".join(["?" for _ in entity_types])
            query = f"""
                SELECT id, name, type, description, created_at
                FROM entities
                WHERE type IN ({placeholders})
                ORDER BY created_at DESC
            """

            rows = self._fetchall(query, tuple(entity_types))

            entities = []
            for row in rows:
                entities.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "type": row[2],
                        "description": row[3],
                        "created_at": row[4],
                    }
                )

            return entities

        except Exception as e:
            logger.exception(f"Failed to search entities by type: {e}")
            return []


if __name__ == "__main__":
    # Test the enhanced knowledge graph
    import sys

    logging.basicConfig(level=logging.INFO)

    ekg = EnhancedKnowledgeGraph("test_enhanced_kg.db")

    try:
        # Test entity creation
        test_entity = LegalEntity(
            id=str(uuid.uuid4()),
            entity_type=LegalEntityType.PLAINTIFF,
            name="John Doe",
            description="Primary plaintiff in contract dispute",
            confidence_factors=ConfidenceFactors(
                source_credibility=0.8,
                evidence_support=0.6,
                extraction_method_reliability=0.9,
            ),
        )

        entity_id = ekg.add_legal_entity(test_entity)
        print(f"Added test entity: {entity_id}")

        # Test relationship creation
        defendant_entity = LegalEntity(
            id=str(uuid.uuid4()),
            entity_type=LegalEntityType.DEFENDANT,
            name="MegaCorp Inc",
            description="Defendant corporation",
        )

        defendant_id = ekg.add_legal_entity(defendant_entity)

        test_relationship = LegalRelationship(
            from_entity=entity_id,
            to_entity=defendant_id,
            relationship_type=LegalRelationshipType.PLAINTIFF_DEFENDANT,
            confidence_factors=ConfidenceFactors(source_credibility=0.9),
        )

        rel_id = ekg.add_legal_relationship(test_relationship)
        print(f"Added test relationship: {rel_id}")

        # Test queries
        relationships = ekg.get_entity_legal_relationships(entity_id)
        print(f"Found {len(relationships)} relationships for entity")

        stats = ekg.get_enhanced_statistics()
        print(f"Enhanced statistics: {stats}")

    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    finally:
        ekg.close()
