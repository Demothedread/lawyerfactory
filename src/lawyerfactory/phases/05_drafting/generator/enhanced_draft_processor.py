"""
# Script Name: enhanced_draft_processor.py
# Description: Enhanced Draft Document Processor Integrates legal relationship detection with the enhanced maestro workflow
# Relationships:
#   - Entity Type: Engine
#   - Directory Group: Workflow
#   - Group Tags: null
Enhanced Draft Document Processor
Integrates legal relationship detection with the enhanced maestro workflow
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from enhanced_knowledge_graph import EnhancedKnowledgeGraph
from legal_relationship_detector import LegalRelationshipDetector

logger = logging.getLogger(__name__)


class EnhancedDraftProcessor:
    """Enhanced processor for draft documents with relationship mapping"""
    
    def __init__(self, knowledge_graph_path: str = 'knowledge_graphs/main.db'):
        self.kg = EnhancedKnowledgeGraph(knowledge_graph_path)
        self.relationship_detector = LegalRelationshipDetector(self.kg)
        self.processing_stats = {
            'documents_processed': 0,
            'entities_extracted': 0,
            'relationships_mapped': 0,
            'conflicts_detected': 0
        }
    
    def process_fact_statement_drafts(self, fact_drafts: List[Dict[str, Any]], 
                                    session_id: str) -> Dict[str, Any]:
        """Process fact statement drafts with enhanced relationship mapping"""
        logger.info(f"Processing {len(fact_drafts)} fact statement drafts for session {session_id}")
        
        all_entities = []
        all_relationships = []
        processing_results = []
        
        for i, draft in enumerate(fact_drafts):
            try:
                # Read draft content
                content = self._read_draft_content(draft)
                if not content:
                    continue
                
                # Enhanced processing with high source credibility for fact statements
                result = self.relationship_detector.process_draft_document(
                    content, 
                    "fact_statement", 
                    source_credibility=0.9  # High credibility for fact statements
                )
                
                # Enhance result with draft metadata
                result.update({
                    'draft_index': i,
                    'file_path': draft.get('file_path', ''),
                    'upload_timestamp': draft.get('timestamp', ''),
                    'session_id': session_id
                })
                
                processing_results.append(result)
                all_entities.extend(result.get('entity_details', []))
                all_relationships.extend(result.get('relationship_details', []))
                
                self.processing_stats['documents_processed'] += 1
                self.processing_stats['entities_extracted'] += result.get('entities_extracted', 0)
                self.processing_stats['relationships_mapped'] += result.get('relationships_extracted', 0)
                
            except Exception as e:
                logger.error(f"Failed to process fact draft {i}: {e}")
                continue
        
        # Aggregate and analyze facts across all drafts
        aggregated_facts = self._aggregate_fact_statements(processing_results)
        
        # Detect conflicts between fact statements
        conflicts = self._detect_fact_conflicts(all_entities, all_relationships)
        self.processing_stats['conflicts_detected'] += len(conflicts)
        
        # Build temporal timeline
        timeline = self._build_fact_timeline(all_entities, all_relationships)
        
        result = {
            'session_id': session_id,
            'draft_type': 'fact_statement',
            'drafts_processed': len(fact_drafts),
            'total_entities': len(all_entities),
            'total_relationships': len(all_relationships),
            'conflicts_detected': len(conflicts),
            'processing_results': processing_results,
            'aggregated_facts': aggregated_facts,
            'detected_conflicts': conflicts,
            'fact_timeline': timeline,
            'confidence_summary': self._calculate_confidence_summary(all_entities, all_relationships),
            'legal_significance_summary': self._analyze_legal_significance(all_relationships)
        }
        
        logger.info(f"Fact statement processing complete: {result['total_entities']} entities, {result['total_relationships']} relationships, {result['conflicts_detected']} conflicts")
        return result
    
    def process_case_complaint_drafts(self, case_drafts: List[Dict[str, Any]], 
                                    session_id: str) -> Dict[str, Any]:
        """Process case/complaint drafts with legal issue extraction"""
        logger.info(f"Processing {len(case_drafts)} case/complaint drafts for session {session_id}")
        
        all_entities = []
        all_relationships = []
        processing_results = []
        
        for i, draft in enumerate(case_drafts):
            try:
                content = self._read_draft_content(draft)
                if not content:
                    continue
                
                # Process with high credibility for legal documents
                result = self.relationship_detector.process_draft_document(
                    content, 
                    "case_complaint", 
                    source_credibility=0.85
                )
                
                result.update({
                    'draft_index': i,
                    'file_path': draft.get('file_path', ''),
                    'upload_timestamp': draft.get('timestamp', ''),
                    'session_id': session_id
                })
                
                processing_results.append(result)
                all_entities.extend(result.get('entity_details', []))
                all_relationships.extend(result.get('relationship_details', []))
                
                self.processing_stats['documents_processed'] += 1
                self.processing_stats['entities_extracted'] += result.get('entities_extracted', 0)
                self.processing_stats['relationships_mapped'] += result.get('relationships_extracted', 0)
                
            except Exception as e:
                logger.error(f"Failed to process case draft {i}: {e}")
                continue
        
        # Extract legal issues and claims structure
        legal_issues = self._extract_legal_issues_structure(all_entities, all_relationships)
        
        # Analyze party relationships
        party_analysis = self._analyze_party_relationships(all_entities, all_relationships)
        
        # Build claims hierarchy
        claims_hierarchy = self._build_claims_hierarchy(all_entities, all_relationships)
        
        result = {
            'session_id': session_id,
            'draft_type': 'case_complaint',
            'drafts_processed': len(case_drafts),
            'total_entities': len(all_entities),
            'total_relationships': len(all_relationships),
            'processing_results': processing_results,
            'legal_issues': legal_issues,
            'party_analysis': party_analysis,
            'claims_hierarchy': claims_hierarchy,
            'confidence_summary': self._calculate_confidence_summary(all_entities, all_relationships),
            'procedural_requirements': self._identify_procedural_requirements(all_entities)
        }
        
        logger.info(f"Case/complaint processing complete: {result['total_entities']} entities, {result['legal_issues']['total_issues']} legal issues")
        return result
    
    def aggregate_draft_results(self, fact_results: Dict[str, Any], 
                              case_results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from both fact statement and case drafts"""
        logger.info("Aggregating fact statement and case draft results")
        
        # Combine entities and relationships
        all_entities = []
        all_relationships = []
        
        if fact_results:
            all_entities.extend(fact_results.get('processing_results', []))
            all_relationships.extend([
                rel for result in fact_results.get('processing_results', [])
                for rel in result.get('relationship_details', [])
            ])
        
        if case_results:
            all_entities.extend(case_results.get('processing_results', []))
            all_relationships.extend([
                rel for result in case_results.get('processing_results', [])
                for rel in result.get('relationship_details', [])
            ])
        
        # Cross-validate information between fact statements and case documents
        cross_validation = self._cross_validate_draft_information(fact_results, case_results)
        
        # Build comprehensive case foundation
        case_foundation = self._build_case_foundation(fact_results, case_results, cross_validation)
        
        # Generate facts matrix
        facts_matrix = self._generate_facts_matrix(case_foundation)
        
        return {
            'aggregation_type': 'fact_and_case_drafts',
            'total_drafts': (fact_results.get('drafts_processed', 0) + 
                           case_results.get('drafts_processed', 0)),
            'total_entities': len(all_entities),
            'total_relationships': len(all_relationships),
            'fact_results': fact_results,
            'case_results': case_results,
            'cross_validation': cross_validation,
            'case_foundation': case_foundation,
            'facts_matrix': facts_matrix,
            'processing_stats': self.processing_stats,
            'recommendations': self._generate_processing_recommendations(case_foundation)
        }
    
    def _read_draft_content(self, draft: Dict[str, Any]) -> str:
        """Read content from draft document"""
        try:
            file_path = draft.get('file_path', '')
            if not file_path or not Path(file_path).exists():
                return draft.get('content', '')
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read draft content: {e}")
            return draft.get('content', '')
    
    def _aggregate_fact_statements(self, processing_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate fact statements across multiple drafts"""
        fact_categories = {
            'material_facts': [],
            'background_facts': [],
            'disputed_facts': [],
            'undisputed_facts': []
        }
        
        confidence_distribution = []
        
        for result in processing_results:
            for entity in result.get('entity_details', []):
                if entity.get('type') == 'fact':
                    confidence = entity.get('confidence', 0.5)
                    confidence_distribution.append(confidence)
                    
                    # Categorize facts based on confidence and context
                    if confidence > 0.8:
                        fact_categories['material_facts'].append(entity)
                    elif confidence > 0.6:
                        fact_categories['background_facts'].append(entity)
                    else:
                        fact_categories['disputed_facts'].append(entity)
        
        return {
            'categories': fact_categories,
            'total_facts': sum(len(facts) for facts in fact_categories.values()),
            'confidence_distribution': {
                'average': sum(confidence_distribution) / len(confidence_distribution) if confidence_distribution else 0,
                'high_confidence_count': sum(1 for c in confidence_distribution if c > 0.8),
                'medium_confidence_count': sum(1 for c in confidence_distribution if 0.6 <= c <= 0.8),
                'low_confidence_count': sum(1 for c in confidence_distribution if c < 0.6)
            }
        }
    
    def _detect_fact_conflicts(self, entities: List[Dict[str, Any]], 
                             relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect conflicts between facts from different drafts"""
        conflicts = []
        
        # Look for contradictory relationships
        contradiction_rels = [rel for rel in relationships 
                             if rel.get('type') == 'contradicts']
        
        for rel in contradiction_rels:
            conflict = {
                'type': 'factual_contradiction',
                'from_entity': rel.get('from_entity', ''),
                'to_entity': rel.get('to_entity', ''),
                'confidence': rel.get('confidence', 0.0),
                'legal_significance': rel.get('legal_significance', ''),
                'severity': 'high' if rel.get('confidence', 0) > 0.7 else 'medium'
            }
            conflicts.append(conflict)
        
        # Detect temporal inconsistencies using knowledge graph
        temporal_conflicts = self.kg.detect_fact_conflicts()
        for conflict in temporal_conflicts:
            conflicts.append({
                'type': 'temporal_inconsistency',
                'entity_a': conflict.get('entity_a_name', ''),
                'entity_b': conflict.get('entity_b_name', ''),
                'conflict_type': conflict.get('conflict_type', ''),
                'severity': conflict.get('severity', 'medium')
            })
        
        return conflicts
    
    def _build_fact_timeline(self, entities: List[Dict[str, Any]], 
                           relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build chronological timeline of facts"""
        temporal_entities = [entity for entity in entities 
                           if entity.get('type') in ['date', 'event', 'fact']]
        
        # Extract entity IDs for timeline building
        entity_ids = [entity['id'] for entity in temporal_entities]
        
        # Use knowledge graph temporal timeline functionality
        timeline = self.kg.get_temporal_timeline(entity_ids)
        
        # Enhance timeline with relationship context
        for timeline_item in timeline:
            # Find relationships involving this entity
            related_relationships = [rel for rel in relationships 
                                   if (rel.get('from_entity') == timeline_item.get('entity_name') or
                                       rel.get('to_entity') == timeline_item.get('entity_name'))]
            timeline_item['related_relationships'] = related_relationships
        
        return sorted(timeline, key=lambda x: x.get('sequence_order', 0))
    
    def _calculate_confidence_summary(self, entities: List[Dict[str, Any]], 
                                    relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall confidence metrics"""
        entity_confidences = [entity.get('confidence', 0.5) for entity in entities]
        relationship_confidences = [rel.get('confidence', 0.5) for rel in relationships]
        
        all_confidences = entity_confidences + relationship_confidences
        
        return {
            'overall_average': sum(all_confidences) / len(all_confidences) if all_confidences else 0,
            'entity_average': sum(entity_confidences) / len(entity_confidences) if entity_confidences else 0,
            'relationship_average': sum(relationship_confidences) / len(relationship_confidences) if relationship_confidences else 0,
            'high_confidence_items': sum(1 for c in all_confidences if c > 0.8),
            'medium_confidence_items': sum(1 for c in all_confidences if 0.6 <= c <= 0.8),
            'low_confidence_items': sum(1 for c in all_confidences if c < 0.6),
            'total_items': len(all_confidences)
        }
    
    def _analyze_legal_significance(self, relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze legal significance of relationships"""
        significance_categories = {
            'critical': [],
            'important': [],
            'supportive': [],
            'contextual': []
        }
        
        for rel in relationships:
            significance = rel.get('legal_significance', '').lower()
            rel_type = rel.get('type', '')
            
            if 'critical' in significance or rel_type in ['causes', 'plaintiff_defendant']:
                significance_categories['critical'].append(rel)
            elif 'strengthens' in significance or rel_type in ['supports', 'evidenced_by']:
                significance_categories['important'].append(rel)
            elif 'favorable' in significance or rel_type == 'supports':
                significance_categories['supportive'].append(rel)
            else:
                significance_categories['contextual'].append(rel)
        
        return {
            'categories': significance_categories,
            'critical_count': len(significance_categories['critical']),
            'important_count': len(significance_categories['important']),
            'supportive_count': len(significance_categories['supportive']),
            'contextual_count': len(significance_categories['contextual']),
            'total_relationships': len(relationships)
        }
    
    def _extract_legal_issues_structure(self, entities: List[Dict[str, Any]], 
                                      relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract structured legal issues from case drafts"""
        legal_issues = [entity for entity in entities 
                       if entity.get('type') in ['claim', 'cause_of_action']]
        
        issues_structure = {
            'primary_claims': [],
            'secondary_claims': [],
            'counterclaims': [],
            'causes_of_action': []
        }
        
        for issue in legal_issues:
            issue_name = issue.get('name', '').lower()
            issue_type = issue.get('type', '')
            
            if issue_type == 'cause_of_action':
                issues_structure['causes_of_action'].append(issue)
            elif 'counter' in issue_name:
                issues_structure['counterclaims'].append(issue)
            elif issue.get('confidence', 0) > 0.7:
                issues_structure['primary_claims'].append(issue)
            else:
                issues_structure['secondary_claims'].append(issue)
        
        return {
            'structure': issues_structure,
            'total_issues': len(legal_issues),
            'primary_claims_count': len(issues_structure['primary_claims']),
            'causes_of_action_count': len(issues_structure['causes_of_action'])
        }
    
    def _analyze_party_relationships(self, entities: List[Dict[str, Any]], 
                                   relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze relationships between legal parties"""
        parties = [entity for entity in entities 
                  if entity.get('type') in ['plaintiff', 'defendant', 'attorney']]
        
        party_relationships = [rel for rel in relationships 
                             if rel.get('type') in ['plaintiff_defendant', 'attorney_client', 'represents']]
        
        return {
            'parties': parties,
            'party_count': len(parties),
            'party_relationships': party_relationships,
            'plaintiff_count': sum(1 for p in parties if p.get('type') == 'plaintiff'),
            'defendant_count': sum(1 for p in parties if p.get('type') == 'defendant'),
            'attorney_count': sum(1 for p in parties if p.get('type') == 'attorney')
        }
    
    def _build_claims_hierarchy(self, entities: List[Dict[str, Any]], 
                              relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build hierarchical structure of claims and supporting elements"""
        claims = [entity for entity in entities if entity.get('type') == 'claim']
        
        hierarchy = {}
        for claim in claims:
            claim_name = claim.get('name', '')
            
            # Find supporting relationships
            supporting_rels = [rel for rel in relationships 
                             if rel.get('to_entity') == claim_name and 
                                rel.get('type') in ['supports', 'evidenced_by']]
            
            hierarchy[claim_name] = {
                'claim': claim,
                'supporting_relationships': supporting_rels,
                'strength_score': self._calculate_claim_strength(claim, supporting_rels)
            }
        
        return hierarchy
    
    def _calculate_claim_strength(self, claim: Dict[str, Any], 
                                supporting_rels: List[Dict[str, Any]]) -> float:
        """Calculate strength score for a legal claim"""
        base_confidence = claim.get('confidence', 0.5)
        support_count = len(supporting_rels)
        support_strength = sum(rel.get('confidence', 0.5) for rel in supporting_rels)
        
        if support_count == 0:
            return base_confidence
        
        avg_support = support_strength / support_count
        # Combine base confidence with support strength
        return min(1.0, (base_confidence + avg_support) / 2 + (support_count * 0.1))
    
    def _identify_procedural_requirements(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify procedural requirements from case entities"""
        procedural_entities = [entity for entity in entities 
                             if entity.get('type') in ['court', 'jurisdiction', 'venue', 'deadline']]
        
        requirements = []
        for entity in procedural_entities:
            requirements.append({
                'type': entity.get('type'),
                'requirement': entity.get('name'),
                'confidence': entity.get('confidence', 0.5),
                'urgency': 'high' if entity.get('type') == 'deadline' else 'medium'
            })
        
        return requirements
    
    def _cross_validate_draft_information(self, fact_results: Dict[str, Any], 
                                        case_results: Dict[str, Any]) -> Dict[str, Any]:
        """Cross-validate information between fact statements and case documents"""
        validation_results = {
            'consistent_entities': [],
            'inconsistent_entities': [],
            'fact_only_entities': [],
            'case_only_entities': [],
            'confidence_adjustments': []
        }
        
        if not fact_results or not case_results:
            return validation_results
        
        fact_entities = {entity['name'].lower(): entity 
                        for result in fact_results.get('processing_results', [])
                        for entity in result.get('entity_details', [])}
        
        case_entities = {entity['name'].lower(): entity 
                        for result in case_results.get('processing_results', [])
                        for entity in result.get('entity_details', [])}
        
        # Find consistent entities (appear in both fact and case drafts)
        common_names = set(fact_entities.keys()) & set(case_entities.keys())
        for name in common_names:
            fact_entity = fact_entities[name]
            case_entity = case_entities[name]
            
            if fact_entity.get('type') == case_entity.get('type'):
                validation_results['consistent_entities'].append({
                    'name': name,
                    'fact_confidence': fact_entity.get('confidence', 0.5),
                    'case_confidence': case_entity.get('confidence', 0.5),
                    'cross_validated': True
                })
            else:
                validation_results['inconsistent_entities'].append({
                    'name': name,
                    'fact_type': fact_entity.get('type'),
                    'case_type': case_entity.get('type'),
                    'requires_review': True
                })
        
        # Entities that appear only in facts or only in case
        fact_only = set(fact_entities.keys()) - common_names
        case_only = set(case_entities.keys()) - common_names
        
        validation_results['fact_only_entities'] = [fact_entities[name] for name in fact_only]
        validation_results['case_only_entities'] = [case_entities[name] for name in case_only]
        
        return validation_results
    
    def _build_case_foundation(self, fact_results: Dict[str, Any], 
                             case_results: Dict[str, Any], 
                             cross_validation: Dict[str, Any]) -> Dict[str, Any]:
        """Build comprehensive case foundation from all draft sources"""
        foundation = {
            'foundational_facts': [],
            'legal_framework': {},
            'party_structure': {},
            'evidence_requirements': [],
            'procedural_checklist': [],
            'strength_assessment': {}
        }
        
        # Combine high-confidence facts from both sources
        if fact_results:
            high_confidence_facts = [
                fact for category in fact_results.get('aggregated_facts', {}).get('categories', {}).values()
                for fact in category if fact.get('confidence', 0) > 0.7
            ]
            foundation['foundational_facts'].extend(high_confidence_facts)
        
        # Extract legal framework from case results
        if case_results:
            foundation['legal_framework'] = case_results.get('legal_issues', {})
            foundation['party_structure'] = case_results.get('party_analysis', {})
            foundation['procedural_checklist'] = case_results.get('procedural_requirements', [])
        
        # Add cross-validated entities for higher confidence
        cross_validated = cross_validation.get('consistent_entities', [])
        foundation['cross_validated_entities'] = cross_validated
        
        # Calculate overall case strength
        foundation['strength_assessment'] = self._assess_case_strength(foundation)
        
        return foundation
    
    def _assess_case_strength(self, foundation: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall strength of the case based on foundation"""
        factual_strength = len(foundation.get('foundational_facts', []))
        legal_strength = len(foundation.get('legal_framework', {}).get('structure', {}).get('primary_claims', []))
        procedural_strength = len(foundation.get('procedural_checklist', []))
        cross_validation_strength = len(foundation.get('cross_validated_entities', []))
        
        total_strength = factual_strength + legal_strength + procedural_strength + cross_validation_strength
        
        return {
            'factual_strength': factual_strength,
            'legal_strength': legal_strength,
            'procedural_strength': procedural_strength,
            'cross_validation_strength': cross_validation_strength,
            'total_strength_score': total_strength,
            'strength_rating': (
                'strong' if total_strength > 20 else
                'moderate' if total_strength > 10 else
                'developing'
            ),
            'recommendations': self._generate_strength_recommendations(
                factual_strength, legal_strength, procedural_strength
            )
        }
    
    def _generate_strength_recommendations(self, factual: int, legal: int, procedural: int) -> List[str]:
        """Generate recommendations based on case strength analysis"""
        recommendations = []
        
        if factual < 5:
            recommendations.append("Gather additional factual evidence to strengthen case foundation")
        
        if legal < 3:
            recommendations.append("Develop additional legal theories or claims")
        
        if procedural < 2:
            recommendations.append("Review procedural requirements and deadlines")
        
        if factual > 10 and legal > 5:
            recommendations.append("Case shows strong foundation - consider aggressive litigation strategy")
        
        return recommendations
    
    def _generate_facts_matrix(self, case_foundation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate facts matrix for statement of facts preparation"""
        matrix = {
            'chronological_facts': [],
            'party_facts': {},
            'claim_supporting_facts': {},
            'disputed_facts': [],
            'undisputed_facts': []
        }
        
        # Organize facts chronologically
        foundational_facts = case_foundation.get('foundational_facts', [])
        matrix['chronological_facts'] = sorted(
            foundational_facts, 
            key=lambda x: x.get('confidence', 0), 
            reverse=True
        )
        
        # Categorize facts by dispute status
        for fact in foundational_facts:
            confidence = fact.get('confidence', 0.5)
            if confidence > 0.8:
                matrix['undisputed_facts'].append(fact)
            elif confidence < 0.6:
                matrix['disputed_facts'].append(fact)
        
        return matrix
    
    def _generate_processing_recommendations(self, case_foundation: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on processing results"""
        recommendations = []
        
        strength = case_foundation.get('strength_assessment', {})
        
        if strength.get('factual_strength', 0) < 5:
            recommendations.append("Consider gathering additional witness statements or documentation")
        
        if strength.get('legal_strength', 0) < 3:
            recommendations.append("Research additional legal theories that may apply to the facts")
        
        if len(case_foundation.get('cross_validated_entities', [])) < 3:
            recommendations.append("Review consistency between fact statements and case documents")
        
        return recommendations
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        kg_stats = self.kg.get_enhanced_statistics()
        
        return {
            'processing_stats': self.processing_stats,
            'knowledge_graph_stats': kg_stats,
            'session_timestamp': json.dumps({"timestamp": "2024-01-01T00:00:00Z"})  # Current time placeholder
        }
    
    def close(self):
        """Close resources"""
        if self.kg:
            self.kg.close()


if __name__ == "__main__":
    # Test the enhanced draft processor
    import os
    import tempfile
    
    logging.basicConfig(level=logging.INFO)
    
    # Create test processor
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        processor = EnhancedDraftProcessor(tmp.name)
    
    try:
        # Test fact statement processing
        test_fact_drafts = [{
            'content': """
            On January 15, 2024, plaintiff John Doe was driving southbound on Main Street when 
            defendant MegaCorp's delivery truck ran a red light and collided with plaintiff's vehicle.
            The impact caused significant damage to plaintiff's vehicle and resulted in serious injuries
            including a broken leg and concussion. Witnesses at the scene confirm that the defendant's
            truck was speeding and failed to stop at the red light.
            """,
            'file_path': '',
            'timestamp': '2024-01-20T10:00:00Z'
        }]
        
        test_case_drafts = [{
            'content': """
            Plaintiff John Doe brings this action against Defendant MegaCorp Inc. for negligence
            arising from a motor vehicle accident. Plaintiff seeks damages in the amount of $150,000
            for medical expenses, lost wages, pain and suffering, and property damage.
            
            First Cause of Action: Negligence
            Defendant owed plaintiff a duty of care while operating its vehicle on public roads.
            Defendant breached this duty by running a red light and speeding.
            """,
            'file_path': '',
            'timestamp': '2024-01-21T14:00:00Z'
        }]
        
        # Process drafts
        fact_results = processor.process_fact_statement_drafts(test_fact_drafts, "test_session_001")
        case_results = processor.process_case_complaint_drafts(test_case_drafts, "test_session_001")
        
        # Aggregate results
        aggregated = processor.aggregate_draft_results(fact_results, case_results)
        
        print("Enhanced Draft Processing Test Results:")
        print(f"Fact Results: {fact_results['total_entities']} entities, {fact_results['total_relationships']} relationships")
        print(f"Case Results: {case_results['total_entities']} entities, {case_results['legal_issues']['total_issues']} legal issues")
        print(f"Aggregated: {aggregated['total_entities']} total entities")
        print(f"Case Foundation Strength: {aggregated['case_foundation']['strength_assessment']['strength_rating']}")
        
        # Get statistics
        stats = processor.get_processing_statistics()
        print(f"Processing Statistics: {stats['processing_stats']}")
        
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        processor.close()
        os.unlink(tmp.name)