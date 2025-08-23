# Script Name: attorney_review_interface.py
# Description: Attorney Review Interface for Statement of Facts Generation Provides comprehensive review, modification, and approval capabilities for generated legal documents with version control and change tracking.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
Attorney Review Interface for Statement of Facts Generation
Provides comprehensive review, modification, and approval capabilities
for generated legal documents with version control and change tracking.
"""

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    """Review status for facts and documents"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVISION = "requires_revision"
    UNDER_REVIEW = "under_review"


class ReviewPriority(Enum):
    """Priority levels for attorney review"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ChangeType(Enum):
    """Types of changes made during review"""
    FACT_MODIFICATION = "fact_modification"
    CITATION_UPDATE = "citation_update"
    FACT_ADDITION = "fact_addition"
    FACT_DELETION = "fact_deletion"
    STRUCTURAL_CHANGE = "structural_change"
    DISPUTE_RESOLUTION = "dispute_resolution"


@dataclass
class ReviewComment:
    """Individual review comment"""
    id: str
    reviewer: str
    timestamp: datetime
    fact_id: Optional[str]
    comment_type: str
    content: str
    priority: ReviewPriority
    resolved: bool = False
    resolution_notes: str = ""


@dataclass
class FactRevision:
    """Revision to a legal fact"""
    revision_id: str
    fact_id: str
    original_text: str
    revised_text: str
    change_type: ChangeType
    reviewer: str
    timestamp: datetime
    justification: str
    confidence_change: Optional[float] = None
    citation_changes: List[str] = field(default_factory=list)


@dataclass
class DocumentVersion:
    """Version of Statement of Facts document"""
    version_id: str
    document_content: str
    creation_timestamp: datetime
    creator: str
    version_notes: str
    fact_revisions: List[FactRevision] = field(default_factory=list)
    review_comments: List[ReviewComment] = field(default_factory=list)
    approval_status: ReviewStatus = ReviewStatus.PENDING


class AttorneyReviewInterface:
    """Comprehensive attorney review interface for Statement of Facts"""
    
    def __init__(self, storage_path: str = "review_storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.active_reviews: Dict[str, Dict[str, Any]] = {}
        self.review_history: Dict[str, List[DocumentVersion]] = {}
        
    def initiate_review_session(self, session_id: str, document_data: Dict[str, Any],
                              reviewer: str) -> Dict[str, Any]:
        """Initiate new attorney review session"""
        logger.info(f"Initiating review session {session_id} for reviewer {reviewer}")
        
        review_session = {
            'session_id': session_id,
            'reviewer': reviewer,
            'start_timestamp': datetime.now(),
            'document_data': document_data,
            'review_items': self._create_review_items(document_data),
            'pending_decisions': self._identify_pending_decisions(document_data),
            'quality_metrics': self._calculate_review_metrics(document_data),
            'status': ReviewStatus.UNDER_REVIEW.value
        }
        
        self.active_reviews[session_id] = review_session
        self._save_review_session(session_id, review_session)
        
        return {
            'session_id': session_id,
            'review_items_count': len(review_session['review_items']),
            'pending_decisions_count': len(review_session['pending_decisions']),
            'estimated_review_time': self._estimate_review_time(review_session),
            'priority_items': self._get_priority_review_items(review_session),
            'review_checklist': self._generate_review_checklist(document_data)
        }
    
    def _create_review_items(self, document_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create structured review items from document data"""
        review_items = []
        item_id_counter = 1
        
        # Review facts for accuracy and completeness
        if 'document' in document_data and 'sections' in document_data['document']:
            for section in document_data['document']['sections']:
                for fact in section.get('facts', []):
                    priority = self._determine_fact_priority(fact)
                    
                    review_items.append({
                        'item_id': f"fact_{item_id_counter:03d}",
                        'type': 'fact_verification',
                        'priority': priority.value,
                        'fact_id': fact['id'],
                        'fact_text': fact['text'],
                        'confidence': fact['confidence'],
                        'is_disputed': fact['is_disputed'],
                        'citation': fact.get('citation', ''),
                        'review_questions': self._generate_fact_review_questions(fact),
                        'suggested_actions': self._suggest_fact_actions(fact)
                    })
                    item_id_counter += 1
        
        # Review citations for Bluebook compliance
        citation_items = self._extract_citation_review_items(document_data)
        review_items.extend(citation_items)
        
        # Review document structure and compliance
        structure_items = self._extract_structure_review_items(document_data)
        review_items.extend(structure_items)
        
        return review_items
    
    def _determine_fact_priority(self, fact: Dict[str, Any]) -> ReviewPriority:
        """Determine review priority for a fact"""
        confidence = fact.get('confidence', 0.5)
        is_disputed = fact.get('is_disputed', False)
        has_citation = bool(fact.get('citation'))
        
        if confidence < 0.6 or is_disputed:
            return ReviewPriority.HIGH
        elif not has_citation or confidence < 0.8:
            return ReviewPriority.MEDIUM
        else:
            return ReviewPriority.LOW
    
    def _generate_fact_review_questions(self, fact: Dict[str, Any]) -> List[str]:
        """Generate specific review questions for a fact"""
        questions = []
        
        # Standard questions for all facts
        questions.append("Is this fact accurate and complete?")
        questions.append("Is the citation properly formatted and sufficient?")
        
        # Confidence-based questions
        if fact.get('confidence', 0.5) < 0.7:
            questions.append("Can additional evidence support this fact?")
            questions.append("Should this fact be verified through discovery?")
        
        # Dispute-based questions
        if fact.get('is_disputed', False):
            questions.append("What is the nature of the dispute regarding this fact?")
            questions.append("How should this dispute be addressed in litigation?")
        
        # Citation-based questions
        if not fact.get('citation'):
            questions.append("What record evidence supports this fact?")
            questions.append("How should this fact be properly cited?")
        
        return questions
    
    def _suggest_fact_actions(self, fact: Dict[str, Any]) -> List[str]:
        """Suggest specific actions for fact review"""
        actions = []
        
        confidence = fact.get('confidence', 0.5)
        has_citation = bool(fact.get('citation'))
        is_disputed = fact.get('is_disputed', False)
        
        if confidence < 0.6:
            actions.append("Verify fact with additional sources")
            actions.append("Consider removing if insufficient support")
        
        if not has_citation:
            actions.append("Add proper Bluebook citation")
            actions.append("Identify supporting evidence")
        
        if is_disputed:
            actions.append("Develop litigation strategy for disputed fact")
            actions.append("Consider alternative fact formulation")
        
        if confidence > 0.9 and has_citation:
            actions.append("Approve fact as stated")
        
        return actions
    
    def _identify_pending_decisions(self, document_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify decisions requiring attorney input"""
        pending_decisions = []
        
        # Check attorney review points from knowledge graph
        review_points = document_data.get('attorney_review_points', [])
        for point in review_points:
            pending_decisions.append({
                'decision_id': str(uuid.uuid4()),
                'type': point.get('type', 'general_review'),
                'priority': point.get('priority', 'medium'),
                'description': point.get('description', ''),
                'options': self._generate_decision_options(point),
                'deadline': self._calculate_decision_deadline(point)
            })
        
        # Check for conflicts requiring resolution
        verification_report = document_data.get('verification_report', {})
        if verification_report.get('disputed_facts_count', 0) > 0:
            pending_decisions.append({
                'decision_id': str(uuid.uuid4()),
                'type': 'dispute_resolution',
                'priority': 'high',
                'description': f"Resolve {verification_report['disputed_facts_count']} disputed facts",
                'options': ['Accept plaintiff version', 'Accept defendant version', 'Seek discovery', 'Remove disputed fact'],
                'deadline': datetime.now() + timedelta(days=7)
            })
        
        return pending_decisions
    
    def _generate_decision_options(self, review_point: Dict[str, Any]) -> List[str]:
        """Generate decision options for review point"""
        point_type = review_point.get('type', '')
        
        if point_type == 'confidence_review':
            return ['Verify facts with additional evidence', 'Accept facts with disclaimer', 'Remove low-confidence facts']
        elif point_type == 'citation_review':
            return ['Add missing citations', 'Request discovery for evidence', 'Remove uncited facts']
        elif point_type == 'dispute_resolution':
            return ['Maintain current position', 'Seek compromise language', 'Pursue discovery']
        else:
            return ['Approve as is', 'Request revision', 'Require additional review']
    
    def review_fact(self, session_id: str, fact_id: str, reviewer_decision: Dict[str, Any]) -> Dict[str, Any]:
        """Process attorney review of individual fact"""
        logger.info(f"Processing fact review for {fact_id} in session {session_id}")
        
        if session_id not in self.active_reviews:
            raise ValueError(f"No active review session found: {session_id}")
        
        review_session = self.active_reviews[session_id]
        
        # Find the review item
        review_item = None
        for item in review_session['review_items']:
            if item.get('fact_id') == fact_id:
                review_item = item
                break
        
        if not review_item:
            raise ValueError(f"Review item not found for fact: {fact_id}")
        
        # Process the decision
        decision_type = reviewer_decision.get('decision', 'approve')
        
        if decision_type == 'approve':
            review_item['status'] = ReviewStatus.APPROVED.value
            review_item['reviewer_notes'] = reviewer_decision.get('notes', '')
            
        elif decision_type == 'revise':
            revision = self._create_fact_revision(fact_id, reviewer_decision, review_session['reviewer'])
            review_item['status'] = ReviewStatus.REQUIRES_REVISION.value
            review_item['revision'] = asdict(revision)
            
        elif decision_type == 'reject':
            review_item['status'] = ReviewStatus.REJECTED.value
            review_item['rejection_reason'] = reviewer_decision.get('reason', '')
            
        # Add review comment if provided
        if reviewer_decision.get('comment'):
            comment = ReviewComment(
                id=str(uuid.uuid4()),
                reviewer=review_session['reviewer'],
                timestamp=datetime.now(),
                fact_id=fact_id,
                comment_type=decision_type,
                content=reviewer_decision['comment'],
                priority=ReviewPriority(reviewer_decision.get('priority', 'medium'))
            )
            review_session.setdefault('comments', []).append(asdict(comment))
        
        # Update session
        review_item['review_timestamp'] = datetime.now().isoformat()
        self._save_review_session(session_id, review_session)
        
        return {
            'fact_id': fact_id,
            'new_status': review_item['status'],
            'revision_created': decision_type == 'revise',
            'remaining_items': len([item for item in review_session['review_items'] 
                                  if item.get('status') != ReviewStatus.APPROVED.value])
        }
    
    def _create_fact_revision(self, fact_id: str, reviewer_decision: Dict[str, Any], reviewer: str) -> FactRevision:
        """Create fact revision from reviewer decision"""
        return FactRevision(
            revision_id=str(uuid.uuid4()),
            fact_id=fact_id,
            original_text=reviewer_decision.get('original_text', ''),
            revised_text=reviewer_decision.get('revised_text', ''),
            change_type=ChangeType(reviewer_decision.get('change_type', 'fact_modification')),
            reviewer=reviewer,
            timestamp=datetime.now(),
            justification=reviewer_decision.get('justification', ''),
            confidence_change=reviewer_decision.get('confidence_change'),
            citation_changes=reviewer_decision.get('citation_changes', [])
        )
    
    def generate_revised_document(self, session_id: str) -> Dict[str, Any]:
        """Generate revised Statement of Facts incorporating attorney changes"""
        logger.info(f"Generating revised document for session {session_id}")
        
        if session_id not in self.active_reviews:
            raise ValueError(f"No active review session found: {session_id}")
        
        review_session = self.active_reviews[session_id]
        original_document = review_session['document_data']
        
        # Apply all approved revisions
        revised_document = self._apply_revisions(original_document, review_session)
        
        # Create new document version
        version = DocumentVersion(
            version_id=str(uuid.uuid4()),
            document_content=revised_document,
            creation_timestamp=datetime.now(),
            creator=review_session['reviewer'],
            version_notes=f"Attorney review incorporating {len(review_session.get('comments', []))} comments"
        )
        
        # Store version history
        self.review_history.setdefault(session_id, []).append(version)
        
        # Generate quality assessment of revised document
        quality_assessment = self._assess_revised_document_quality(revised_document, review_session)
        
        return {
            'session_id': session_id,
            'version_id': version.version_id,
            'revised_document': revised_document,
            'revision_summary': self._generate_revision_summary(review_session),
            'quality_assessment': quality_assessment,
            'export_ready': quality_assessment['overall_score'] >= 0.8
        }
    
    def _apply_revisions(self, original_document: Dict[str, Any], review_session: Dict[str, Any]) -> str:
        """Apply attorney revisions to generate revised document"""
        # This would integrate with the statement_of_facts_generator to apply changes
        # For now, return a placeholder
        revisions_count = len([item for item in review_session['review_items'] 
                              if item.get('status') == ReviewStatus.REQUIRES_REVISION.value])
        
        return f"Revised Statement of Facts incorporating {revisions_count} attorney revisions"
    
    def _generate_revision_summary(self, review_session: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of revisions made"""
        approved_count = len([item for item in review_session['review_items'] 
                             if item.get('status') == ReviewStatus.APPROVED.value])
        revised_count = len([item for item in review_session['review_items'] 
                            if item.get('status') == ReviewStatus.REQUIRES_REVISION.value])
        rejected_count = len([item for item in review_session['review_items'] 
                             if item.get('status') == ReviewStatus.REJECTED.value])
        
        return {
            'total_items_reviewed': len(review_session['review_items']),
            'approved_facts': approved_count,
            'revised_facts': revised_count,
            'rejected_facts': rejected_count,
            'comments_added': len(review_session.get('comments', [])),
            'review_completion_percentage': (approved_count + revised_count + rejected_count) / len(review_session['review_items']) * 100
        }
    
    def get_review_dashboard(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive review dashboard for attorney"""
        if session_id not in self.active_reviews:
            raise ValueError(f"No active review session found: {session_id}")
        
        review_session = self.active_reviews[session_id]
        
        # Calculate progress metrics
        total_items = len(review_session['review_items'])
        completed_items = len([item for item in review_session['review_items'] 
                              if 'status' in item])
        
        high_priority_items = [item for item in review_session['review_items'] 
                              if item.get('priority') == 'high' and 'status' not in item]
        
        return {
            'session_info': {
                'session_id': session_id,
                'reviewer': review_session['reviewer'],
                'start_time': review_session['start_timestamp'],
                'status': review_session['status']
            },
            'progress': {
                'total_items': total_items,
                'completed_items': completed_items,
                'completion_percentage': (completed_items / total_items * 100) if total_items > 0 else 0,
                'estimated_time_remaining': self._estimate_remaining_time(review_session)
            },
            'priority_items': high_priority_items[:10],  # Top 10 priority items
            'pending_decisions': review_session.get('pending_decisions', []),
            'quality_metrics': review_session.get('quality_metrics', {}),
            'recent_activity': self._get_recent_review_activity(session_id)
        }
    
    def export_review_report(self, session_id: str) -> Dict[str, Any]:
        """Export comprehensive review report"""
        if session_id not in self.active_reviews:
            raise ValueError(f"No active review session found: {session_id}")
        
        review_session = self.active_reviews[session_id]
        
        report = {
            'report_metadata': {
                'session_id': session_id,
                'reviewer': review_session['reviewer'],
                'generation_timestamp': datetime.now().isoformat(),
                'document_title': 'Attorney Review Report - Statement of Facts'
            },
            'review_summary': self._generate_revision_summary(review_session),
            'detailed_findings': self._generate_detailed_findings(review_session),
            'recommendations': self._generate_review_recommendations(review_session),
            'next_steps': self._generate_next_steps(review_session),
            'appendices': {
                'all_comments': review_session.get('comments', []),
                'revision_log': self._generate_revision_log(review_session),
                'quality_metrics': review_session.get('quality_metrics', {})
            }
        }
        
        # Save report
        report_path = self.storage_path / f"review_report_{session_id}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report
    
    def _calculate_review_metrics(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate initial review metrics"""
        verification_report = document_data.get('verification_report', {})
        
        return {
            'total_facts': verification_report.get('total_facts', 0),
            'high_confidence_facts': verification_report.get('confidence_distribution', {}).get('high_confidence', 0),
            'citation_coverage': verification_report.get('citation_coverage', 0),
            'disputed_facts': verification_report.get('disputed_facts_count', 0),
            'quality_score': verification_report.get('quality_score', 0)
        }
    
    def _estimate_review_time(self, review_session: Dict[str, Any]) -> str:
        """Estimate time required for review"""
        item_count = len(review_session['review_items'])
        high_priority_count = len([item for item in review_session['review_items'] 
                                  if item.get('priority') == 'high'])
        
        # Estimate 2 minutes per normal item, 5 minutes per high priority item
        estimated_minutes = (item_count - high_priority_count) * 2 + high_priority_count * 5
        
        if estimated_minutes < 60:
            return f"{estimated_minutes} minutes"
        else:
            hours = estimated_minutes // 60
            minutes = estimated_minutes % 60
            return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minutes"
    
    def _get_priority_review_items(self, review_session: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get high priority review items"""
        return [item for item in review_session['review_items'] 
                if item.get('priority') in ['high', 'urgent']][:5]
    
    def _generate_review_checklist(self, document_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate attorney review checklist"""
        return [
            {'item': 'Verify all material facts are accurate and complete', 'category': 'fact_accuracy'},
            {'item': 'Ensure all facts have proper Bluebook citations', 'category': 'citations'},
            {'item': 'Review disputed facts and litigation strategy', 'category': 'disputes'},
            {'item': 'Confirm document structure complies with FRCP', 'category': 'compliance'},
            {'item': 'Verify party identifications are correct', 'category': 'parties'},
            {'item': 'Check chronological organization of facts', 'category': 'organization'},
            {'item': 'Assess overall persuasive impact', 'category': 'strategy'},
            {'item': 'Confirm all deadlines and procedural requirements', 'category': 'deadlines'}
        ]
    
    def _save_review_session(self, session_id: str, review_session: Dict[str, Any]):
        """Save review session to storage"""
        session_path = self.storage_path / f"session_{session_id}.json"
        with open(session_path, 'w') as f:
            json.dump(review_session, f, indent=2, default=str)
    
    def _extract_citation_review_items(self, document_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract citation review items"""
        # Implementation for citation-specific review items
        return []
    
    def _extract_structure_review_items(self, document_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract document structure review items"""
        # Implementation for structure-specific review items
        return []
    
    def _calculate_decision_deadline(self, review_point: Dict[str, Any]) -> datetime:
        """Calculate deadline for review decision"""
        priority = review_point.get('priority', 'medium')
        
        if priority == 'urgent':
            return datetime.now() + timedelta(hours=24)
        elif priority == 'high':
            return datetime.now() + timedelta(days=3)
        elif priority == 'medium':
            return datetime.now() + timedelta(days=7)
        else:
            return datetime.now() + timedelta(days=14)
    
    def _assess_revised_document_quality(self, revised_document: str, review_session: Dict[str, Any]) -> Dict[str, Any]:
        """Assess quality of revised document"""
        return {
            'overall_score': 0.85,  # Placeholder
            'citation_compliance': 0.9,
            'fact_accuracy': 0.8,
            'structural_compliance': 0.9,
            'readability': 0.85
        }
    
    def _estimate_remaining_time(self, review_session: Dict[str, Any]) -> str:
        """Estimate remaining review time"""
        return "30 minutes"  # Placeholder
    
    def _get_recent_review_activity(self, session_id: str) -> List[Dict[str, Any]]:
        """Get recent review activity"""
        return []  # Placeholder
    
    def _generate_detailed_findings(self, review_session: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate detailed review findings"""
        return []  # Placeholder
    
    def _generate_review_recommendations(self, review_session: Dict[str, Any]) -> List[str]:
        """Generate review recommendations"""
        return []  # Placeholder
    
    def _generate_next_steps(self, review_session: Dict[str, Any]) -> List[str]:
        """Generate next steps"""
        return []  # Placeholder
    
    def _generate_revision_log(self, review_session: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate revision log"""
        return []  # Placeholder


def create_attorney_review_interface(storage_path: str = "review_storage") -> AttorneyReviewInterface:
    """Factory function to create attorney review interface"""
    return AttorneyReviewInterface(storage_path)


if __name__ == "__main__":
    # Example usage
    interface = create_attorney_review_interface()
    
    print("Attorney Review Interface initialized successfully")
    print("Ready for comprehensive legal document review")