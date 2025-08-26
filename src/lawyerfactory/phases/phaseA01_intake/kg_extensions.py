"""
# Script Name: knowledge_graph_extensions.py
# Description: Extensions to the KnowledgeGraph class to support the enhanced web interface.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Ingestion
#   - Group Tags: knowledge-graph
Extensions to the KnowledgeGraph class to support the enhanced web interface.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class KnowledgeGraphExtensions:
    """Extensions for the KnowledgeGraph class to support web interface features"""
    
    def __init__(self, kg):
        self.kg = kg
    
    def get_entity_relationships(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get all relationships for a specific entity"""
        try:
            # Get relationships where entity is the source
            from_relationships = self.kg._fetchall(
                "SELECT * FROM relationships WHERE from_entity = ?", 
                (entity_id,)
            )
            
            # Get relationships where entity is the target
            to_relationships = self.kg._fetchall(
                "SELECT * FROM relationships WHERE to_entity = ?", 
                (entity_id,)
            )
            
            relationships = []
            
            # Process from relationships
            for rel in from_relationships:
                relationships.append({
                    'id': rel[0],
                    'from_entity': rel[1],
                    'to_entity': rel[2],
                    'relationship_type': rel[3],
                    'confidence': rel[4],
                    'direction': 'outgoing'
                })
            
            # Process to relationships
            for rel in to_relationships:
                relationships.append({
                    'id': rel[0],
                    'from_entity': rel[1],
                    'to_entity': rel[2],
                    'relationship_type': rel[3],
                    'confidence': rel[4],
                    'direction': 'incoming'
                })
            
            return relationships
            
        except Exception as e:
            logger.error(f"Failed to get entity relationships for {entity_id}: {e}")
            return []
    
    def get_all_relationships(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all relationships with optional limit"""
        try:
            relationships = self.kg._fetchall(
                "SELECT * FROM relationships ORDER BY id DESC LIMIT ?", 
                (limit,)
            )
            
            return [{
                'id': rel[0],
                'from_entity': rel[1],
                'to_entity': rel[2],
                'relationship_type': rel[3],
                'confidence': rel[4],
                'extraction_method': rel[5],
                'verified': rel[6],
                'supporting_text': rel[7]
            } for rel in relationships]
            
        except Exception as e:
            logger.error(f"Failed to get all relationships: {e}")
            return []
    
    def get_entity_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific entity by ID"""
        try:
            entity = self.kg._fetchone(
                "SELECT * FROM entities WHERE id = ?", 
                (entity_id,)
            )
            
            if entity:
                return {
                    'id': entity[0],
                    'type': entity[1],
                    'name': entity[2],
                    'canonical_name': entity[3],
                    'description': entity[4],
                    'source_text': entity[5],
                    'context_window': entity[6],
                    'confidence': entity[7],
                    'extraction_method': entity[8],
                    'created_at': entity[9],
                    'updated_at': entity[10],
                    'legal_attributes': entity[11],
                    'verified': entity[13],
                    'verification_source': entity[14]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get entity {entity_id}: {e}")
            return None
    
    def add_entity_dict(self, entity_data: Dict[str, Any]) -> str:
        """Add an entity from a dictionary"""
        import uuid
        try:
            entity_id = entity_data.get('id') or str(uuid.uuid4())
            
            self.kg._execute("""
                INSERT OR REPLACE INTO entities 
                (id, type, name, canonical_name, description, source_text, 
                 context_window, confidence, extraction_method, legal_attributes, 
                 verified, verification_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_id,
                entity_data.get('type', 'UNKNOWN'),
                entity_data.get('name', ''),
                entity_data.get('canonical_name'),
                entity_data.get('description'),
                entity_data.get('source_text'),
                entity_data.get('context_window'),
                entity_data.get('confidence', 1.0),
                entity_data.get('extraction_method', 'manual'),
                entity_data.get('legal_attributes'),
                entity_data.get('verified', False),
                entity_data.get('verification_source')
            ))
            
            return entity_id
            
        except Exception as e:
            logger.error(f"Failed to add entity: {e}")
            raise
    
    def add_relationship_dict(self, relationship_data: Dict[str, Any]) -> int:
        """Add a relationship from a dictionary"""
        try:
            cursor = self.kg.conn.cursor()
            cursor.execute("""
                INSERT INTO relationships 
                (from_entity, to_entity, relationship_type, confidence, 
                 extraction_method, verified, supporting_text, temporal_context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                relationship_data.get('from_entity'),
                relationship_data.get('to_entity'),
                relationship_data.get('relationship_type', 'related_to'),
                relationship_data.get('confidence', 1.0),
                relationship_data.get('extraction_method', 'manual'),
                relationship_data.get('verified', False),
                relationship_data.get('supporting_text'),
                relationship_data.get('temporal_context')
            ))
            
            relationship_id = cursor.lastrowid
            self.kg.conn.commit()
            cursor.close()
            
            return relationship_id
            
        except Exception as e:
            logger.error(f"Failed to add relationship: {e}")
            raise
    
    def get_entity_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        try:
            # Entity counts by type
            entity_counts = self.kg._fetchall(
                "SELECT type, COUNT(*) FROM entities GROUP BY type ORDER BY COUNT(*) DESC"
            )
            
            # Relationship counts by type
            relationship_counts = self.kg._fetchall(
                "SELECT relationship_type, COUNT(*) FROM relationships GROUP BY relationship_type ORDER BY COUNT(*) DESC"
            )
            
            # Total counts
            total_entities = self.kg._fetchone("SELECT COUNT(*) FROM entities")[0]
            total_relationships = self.kg._fetchone("SELECT COUNT(*) FROM relationships")[0]
            
            return {
                'total_entities': total_entities,
                'total_relationships': total_relationships,
                'entity_types': [{'type': row[0], 'count': row[1]} for row in entity_counts],
                'relationship_types': [{'type': row[0], 'count': row[1]} for row in relationship_counts]
            }
            
        except Exception as e:
            logger.error(f"Failed to get entity statistics: {e}")
            return {
                'total_entities': 0,
                'total_relationships': 0,
                'entity_types': [],
                'relationship_types': []
            }


# Monkey patch the KnowledgeGraph class with these extensions
def extend_knowledge_graph(kg):
    """Extend a KnowledgeGraph instance with web interface methods"""
    extensions = KnowledgeGraphExtensions(kg)
    
    # Add methods to the knowledge graph instance
    kg.get_entity_relationships = extensions.get_entity_relationships
    kg.get_all_relationships = extensions.get_all_relationships
    kg.get_entity_by_id = extensions.get_entity_by_id
    kg.add_entity_dict = extensions.add_entity_dict
    kg.add_relationship_dict = extensions.add_relationship_dict
    kg.get_entity_statistics = extensions.get_entity_statistics
    
    return kg