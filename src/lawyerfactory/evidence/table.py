"""
# Script Name: table.py
# Description: Enhanced Evidence Table Module for LawyerFactory Implements interactive, sortable, filterable evidence management with facts and claims linking.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: evidence-processing
Enhanced Evidence Table Module for LawyerFactory
Implements interactive, sortable, filterable evidence management with facts and claims linking.
"""

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Import unified storage API
try:
    from lawyerfactory.storage.unified_storage_api import get_unified_storage_api, UnifiedStorageAPI
    UNIFIED_STORAGE_AVAILABLE = True
except ImportError:
    UNIFIED_STORAGE_AVAILABLE = False
    logger.warning("Unified storage API not available, using standalone mode")


class EvidenceType(Enum):
    """Types of evidence for classification"""
    DOCUMENTARY = "documentary"
    TESTIMONIAL = "testimonial"
    EXPERT = "expert"
    PHYSICAL = "physical"
    DIGITAL = "digital"
    PHOTOGRAPHIC = "photographic"


class PrivilegeMarker(Enum):
    """Privilege protection markers"""
    NONE = "none"
    ATTORNEY_CLIENT = "attorney_client"
    WORK_PRODUCT = "work_product"
    CONFIDENTIAL = "confidential"
    REDACTED = "redacted"


class RelevanceLevel(Enum):
    """Evidence relevance classification"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class EvidenceEntry:
    """Enhanced evidence entry with comprehensive metadata"""
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    object_id: Optional[str] = None  # Unified storage ObjectID
    source_document: str = ""
    page_section: str = ""
    content: str = ""
    evidence_type: EvidenceType = EvidenceType.DOCUMENTARY
    relevance_score: float = 0.0
    relevance_level: RelevanceLevel = RelevanceLevel.UNKNOWN
    supporting_facts: List[str] = field(default_factory=list)
    bluebook_citation: str = ""
    privilege_marker: PrivilegeMarker = PrivilegeMarker.NONE
    extracted_date: Optional[str] = None
    witness_name: Optional[str] = None
    key_terms: List[str] = field(default_factory=list)
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by: str = "system"
    
    def update_modified(self):
        """Update the last modified timestamp"""
        self.last_modified = datetime.now().isoformat()
    
    def add_supporting_fact(self, fact_id: str):
        """Add a fact ID to supporting facts"""
        if fact_id not in self.supporting_facts:
            self.supporting_facts.append(fact_id)
            self.update_modified()
    
    def remove_supporting_fact(self, fact_id: str):
        """Remove a fact ID from supporting facts"""
        if fact_id in self.supporting_facts:
            self.supporting_facts.remove(fact_id)
            self.update_modified()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert enums to their values
        result['evidence_type'] = self.evidence_type.value
        result['relevance_level'] = self.relevance_level.value
        result['privilege_marker'] = self.privilege_marker.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvidenceEntry':
        """Create from dictionary with enum conversion"""
        # Convert enum values back to enums
        if 'evidence_type' in data:
            data['evidence_type'] = EvidenceType(data['evidence_type'])
        if 'relevance_level' in data:
            data['relevance_level'] = RelevanceLevel(data['relevance_level'])
        if 'privilege_marker' in data:
            data['privilege_marker'] = PrivilegeMarker(data['privilege_marker'])
        
        return cls(**data)


@dataclass
class FactAssertion:
    """Fact assertion with evidence linking"""
    fact_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fact_text: str = ""
    confidence_score: float = 0.0
    supporting_evidence: List[str] = field(default_factory=list)
    related_claims: List[str] = field(default_factory=list)
    chronological_order: int = 0
    date_occurred: Optional[str] = None
    location: str = ""
    parties_involved: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def update_modified(self):
        """Update the last modified timestamp"""
        self.last_modified = datetime.now().isoformat()
    
    def add_supporting_evidence(self, evidence_id: str):
        """Add evidence ID to supporting evidence"""
        if evidence_id not in self.supporting_evidence:
            self.supporting_evidence.append(evidence_id)
            self.update_modified()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FactAssertion':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class LegalElement:
    """Legal element for cause of action"""
    element_name: str = ""
    supporting_facts: List[str] = field(default_factory=list)
    legal_standard: str = ""
    court_test: str = ""
    citations: List[str] = field(default_factory=list)
    element_met: bool = False
    notes: str = ""


@dataclass
class ClaimEntry:
    """Claim/cause of action with legal elements"""
    claim_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cause_of_action: str = ""
    legal_elements: List[LegalElement] = field(default_factory=list)
    claim_strength: float = 0.0
    jurisdiction: str = ""
    statute_of_limitations: str = ""
    damages_sought: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def update_modified(self):
        """Update the last modified timestamp"""
        self.last_modified = datetime.now().isoformat()
    
    def add_element(self, element: LegalElement):
        """Add a legal element"""
        self.legal_elements.append(element)
        self.update_modified()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClaimEntry':
        """Create from dictionary"""
        # Convert legal elements
        if 'legal_elements' in data:
            elements = []
            for elem_data in data['legal_elements']:
                elements.append(LegalElement(**elem_data))
            data['legal_elements'] = elements
        
        return cls(**data)


class EnhancedEvidenceTable:
    """Enhanced evidence table manager with facts and claims integration"""

    def __init__(self, storage_path: str = "evidence_table.json"):
        self.storage_path = Path(storage_path)
        self.evidence_entries: Dict[str, EvidenceEntry] = {}
        self.fact_assertions: Dict[str, FactAssertion] = {}
        self.claim_entries: Dict[str, ClaimEntry] = {}

        # Initialize unified storage integration
        self.unified_storage = None
        if UNIFIED_STORAGE_AVAILABLE:
            try:
                self.unified_storage = get_unified_storage_api()
                self.unified_storage.register_storage_client("evidence", self)
                logger.info("Evidence table integrated with unified storage API")
            except Exception as e:
                logger.warning(f"Failed to initialize unified storage: {e}")
                self.unified_storage = None

        self._load_data()

    # Unified Storage API Interface Methods
    async def store_evidence_data(self, evidence_id: str, data: Dict[str, Any]) -> bool:
        """Store evidence data from unified storage API"""
        try:
            # Create evidence entry from data
            entry = EvidenceEntry.from_dict(data)
            entry.evidence_id = evidence_id
            self.evidence_entries[evidence_id] = entry
            self._save_data()
            return True
        except Exception as e:
            logger.error(f"Failed to store evidence data {evidence_id}: {e}")
            return False

    async def get_evidence_data(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve evidence data for unified storage API"""
        try:
            if evidence_id in self.evidence_entries:
                return self.evidence_entries[evidence_id].to_dict()
            return None
        except Exception as e:
            logger.error(f"Failed to get evidence data {evidence_id}: {e}")
            return None

    async def search_evidence_data(self, query: str) -> List[Dict[str, Any]]:
        """Search evidence data for unified storage API"""
        try:
            results = []
            query_lower = query.lower()

            for entry in self.evidence_entries.values():
                # Simple text search in content and notes
                if (query_lower in entry.content.lower() or
                    query_lower in entry.notes.lower() or
                    any(query_lower in term.lower() for term in entry.key_terms)):
                    results.append(entry.to_dict())

            return results
        except Exception as e:
            logger.error(f"Failed to search evidence data: {e}")
    async def add_evidence_with_unified_storage(self, file_content: bytes, filename: str,
                                                metadata: Optional[Dict[str, Any]] = None,
                                                source_phase: str = "intake") -> str:
        """Add evidence using the unified storage API"""
        if not self.unified_storage:
            # Fallback to regular method
            evidence = EvidenceEntry(
                source_document=filename,
                content="",  # Will be populated if text extraction is available
                created_by="system"
            )
            return self.add_evidence(evidence)

        try:
            # Store through unified storage API
            result = await self.unified_storage.store_evidence(
                file_content=file_content,
                filename=filename,
                metadata=metadata,
                source_phase=source_phase
            )

            if result.success:
                # Create evidence entry with ObjectID
                evidence = EvidenceEntry(
                    evidence_id=result.evidence_id or str(uuid.uuid4()),
                    object_id=result.object_id,
                    source_document=filename,
                    content="",  # Will be populated by unified storage
                    created_by="system"
                )

                # Add to local table
                evidence_id = self.add_evidence(evidence)

                # Update with ObjectID link
                evidence.object_id = result.object_id
                self.evidence_entries[evidence_id] = evidence
                self._save_data()

                return evidence_id
            else:
                logger.error(f"Unified storage failed: {result.error}")
                # Fallback to regular method
                evidence = EvidenceEntry(
                    source_document=filename,
                    content="",
                    created_by="system"
                )
                return self.add_evidence(evidence)

        except Exception as e:
            logger.error(f"Failed to add evidence with unified storage: {e}")
            # Fallback to regular method
            evidence = EvidenceEntry(
                source_document=filename,
                content="",
                created_by="system"
            )
            return self.add_evidence(evidence)

    async def get_evidence_with_unified_storage(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Get evidence with unified storage data"""
        evidence = self.evidence_entries.get(evidence_id)
        if not evidence or not evidence.object_id:
            return evidence.to_dict() if evidence else None

        if self.unified_storage:
            try:
                unified_data = await self.unified_storage.get_evidence(evidence.object_id)
                if unified_data and "error" not in unified_data:
                    # Merge unified storage data with local evidence data
                    result = evidence.to_dict()
                    result["unified_storage"] = unified_data
                    return result
            except Exception as e:
                logger.warning(f"Failed to get unified storage data for {evidence_id}: {e}")

        return evidence.to_dict()

    async def search_evidence_with_unified_storage(self, query: str) -> List[Dict[str, Any]]:
        """Search evidence using unified storage"""
        if self.unified_storage:
            try:
                unified_results = await self.unified_storage.search_evidence(query)
                if unified_results:
                    # Convert to evidence table format
                    results = []
                    for result in unified_results:
                        evidence_id = result.get("object_id")
                        if evidence_id in self.evidence_entries:
                            evidence_data = self.evidence_entries[evidence_id].to_dict()
                            evidence_data["unified_storage"] = result
                            results.append(evidence_data)
                    return results
            except Exception as e:
                logger.warning(f"Unified storage search failed: {e}")

        # Fallback to local search
        return await self.search_evidence_data(query)
            return []</search>
</search_and_replace>
    
    def _load_data(self):
        """Load evidence table data from storage"""
        try:
            if self.storage_path.exists():
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                
                # Load evidence entries
                for entry_data in data.get("evidence_entries", []):
                    entry = EvidenceEntry.from_dict(entry_data)
                    self.evidence_entries[entry.evidence_id] = entry
                
                # Load fact assertions
                for fact_data in data.get("fact_assertions", []):
                    fact = FactAssertion.from_dict(fact_data)
                    self.fact_assertions[fact.fact_id] = fact
                
                # Load claim entries
                for claim_data in data.get("claim_entries", []):
                    claim = ClaimEntry.from_dict(claim_data)
                    self.claim_entries[claim.claim_id] = claim
                
                logger.info(f"Loaded {len(self.evidence_entries)} evidence entries, "
                          f"{len(self.fact_assertions)} facts, {len(self.claim_entries)} claims")
            else:
                logger.info("No existing evidence table found, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load evidence table: {e}")
            # Initialize empty collections on error
            self.evidence_entries = {}
            self.fact_assertions = {}
            self.claim_entries = {}
    
    def _save_data(self):
        """Save evidence table data to storage"""
        try:
            data = {
                "evidence_entries": [entry.to_dict() for entry in self.evidence_entries.values()],
                "fact_assertions": [fact.to_dict() for fact in self.fact_assertions.values()],
                "claim_entries": [claim.to_dict() for claim in self.claim_entries.values()],
                "last_updated": datetime.now().isoformat(),
                "version": "2.0"
            }
            
            self.storage_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            logger.debug(f"Saved evidence table with {len(self.evidence_entries)} entries")
        except Exception as e:
            logger.error(f"Failed to save evidence table: {e}")
    
    def add_evidence(self, evidence: EvidenceEntry) -> str:
        """Add evidence entry"""
        self.evidence_entries[evidence.evidence_id] = evidence
        self._save_data()
        return evidence.evidence_id
    
    def get_evidence(self, evidence_id: str) -> Optional[EvidenceEntry]:
        """Get evidence entry by ID"""
        return self.evidence_entries.get(evidence_id)
    
    def update_evidence(self, evidence_id: str, updates: Dict[str, Any]) -> bool:
        """Update evidence entry"""
        if evidence_id in self.evidence_entries:
            entry = self.evidence_entries[evidence_id]
            for key, value in updates.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
            entry.update_modified()
            self._save_data()
            return True
        return False
    
    def delete_evidence(self, evidence_id: str) -> bool:
        """Delete evidence entry"""
        if evidence_id in self.evidence_entries:
            del self.evidence_entries[evidence_id]
            self._save_data()
            return True
        return False
    
    def add_fact(self, fact: FactAssertion) -> str:
        """Add fact assertion"""
        self.fact_assertions[fact.fact_id] = fact
        self._save_data()
        return fact.fact_id
    
    def get_fact(self, fact_id: str) -> Optional[FactAssertion]:
        """Get fact assertion by ID"""
        return self.fact_assertions.get(fact_id)
    
    def link_evidence_to_fact(self, evidence_id: str, fact_id: str) -> bool:
        """Link evidence to fact assertion"""
        if evidence_id in self.evidence_entries and fact_id in self.fact_assertions:
            self.evidence_entries[evidence_id].add_supporting_fact(fact_id)
            self.fact_assertions[fact_id].add_supporting_evidence(evidence_id)
            self._save_data()
            return True
        return False
    
    def add_claim(self, claim: ClaimEntry) -> str:
        """Add claim entry"""
        self.claim_entries[claim.claim_id] = claim
        self._save_data()
        return claim.claim_id
    
    def get_evidence_by_filters(self, 
                               evidence_type: Optional[EvidenceType] = None,
                               relevance_level: Optional[RelevanceLevel] = None,
                               source_document: Optional[str] = None,
                               min_relevance_score: Optional[float] = None) -> List[EvidenceEntry]:
        """Get filtered evidence entries"""
        results = []
        for entry in self.evidence_entries.values():
            if evidence_type and entry.evidence_type != evidence_type:
                continue
            if relevance_level and entry.relevance_level != relevance_level:
                continue
            if source_document and source_document.lower() not in entry.source_document.lower():
                continue
            if min_relevance_score and entry.relevance_score < min_relevance_score:
                continue
            results.append(entry)
        
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get evidence table statistics"""
        evidence_by_type = {}
        total_relevance = 0
        
        for entry in self.evidence_entries.values():
            evidence_by_type[entry.evidence_type.value] = evidence_by_type.get(entry.evidence_type.value, 0) + 1
            total_relevance += entry.relevance_score
        
        avg_relevance = total_relevance / len(self.evidence_entries) if self.evidence_entries else 0
        
        return {
            "total_evidence": len(self.evidence_entries),
            "total_facts": len(self.fact_assertions),
            "total_claims": len(self.claim_entries),
            "evidence_by_type": evidence_by_type,
            "average_relevance_score": round(avg_relevance, 2),
            "last_updated": datetime.now().isoformat()
        }
    
    def export_to_dict(self) -> Dict[str, Any]:
        """Export all data to dictionary for API responses"""
        return {
            "evidence_entries": [entry.to_dict() for entry in self.evidence_entries.values()],
            "fact_assertions": [fact.to_dict() for fact in self.fact_assertions.values()],
            "claim_entries": [claim.to_dict() for claim in self.claim_entries.values()],
            "stats": self.get_stats()
        }


# Legacy compatibility function
def migrate_legacy_evidence_table(legacy_path: str, new_path: str) -> bool:
    """Migrate legacy evidence table format to enhanced format"""
    try:
        legacy_data = json.loads(Path(legacy_path).read_text(encoding="utf-8"))
        enhanced_table = EnhancedEvidenceTable(new_path)
        
        # Migrate legacy rows to new format
        for i, row in enumerate(legacy_data.get("rows", [])):
            evidence = EvidenceEntry(
                source_document=row.get("source", "Unknown"),
                content=row.get("content", ""),
                evidence_type=EvidenceType.DOCUMENTARY,  # Default type
                created_by="migration"
            )
            enhanced_table.add_evidence(evidence)
        
        logger.info(f"Migrated {len(legacy_data.get('rows', []))} legacy evidence entries")
        return True
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False