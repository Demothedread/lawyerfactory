# Script Name: prompt_integration.py
# Description: Integration layer for LLM-powered prompt deconstruction with LawyerFactory enhanced system. Connects the prompt analysis engine with the maestro orchestration and WebSocket events.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
Integration layer for LLM-powered prompt deconstruction with LawyerFactory enhanced system.
Connects the prompt analysis engine with the maestro orchestration and WebSocket events.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from maestro.enhanced_maestro import EnhancedMaestro
from maestro.workflow_models import WorkflowPhase

from .prompt_deconstruction import PromptDeconstructionService

logger = logging.getLogger(__name__)


class EnhancedPromptProcessor:
    """Enhanced prompt processor that integrates with the maestro orchestration system"""
    
    def __init__(self, maestro: EnhancedMaestro, llm_service=None):
        self.maestro = maestro
        self.prompt_service = PromptDeconstructionService(llm_service)
        self.active_analyses = {}  # session_id -> analysis_result
        self.mcp_memory_manager = None  # Optional MCP memory integration
        
    async def process_case_prompt(self, session_id: str, case_prompt: str, 
                                document_type_hint: Optional[str] = None,
                                socketio=None) -> Dict[str, Any]:
        """
        Process a case prompt with LLM-powered analysis and integrate with workflow system
        
        Args:
            session_id: Unique session identifier
            case_prompt: User's case description prompt
            document_type_hint: Optional hint about document type
            socketio: SocketIO instance for real-time updates
            
        Returns:
            Dictionary containing analysis results and workflow integration data
        """
        try:
            logger.info(f"Processing case prompt for session {session_id}")
            
            # Emit processing start event
            if socketio:
                await socketio.emit('prompt_analysis_started', {
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat(),
                    'stage': 'deconstruction'
                })
            
            # Step 1: Perform LLM-powered prompt deconstruction
            analysis_result = await self.prompt_service.analyze_prompt(
                case_prompt, 
                document_type_hint
            )
            
            # Store analysis for later use
            self.active_analyses[session_id] = analysis_result
            
            # Step 2: Generate workflow context from analysis
            workflow_context = self._create_workflow_context(analysis_result)
            
            # Step 3: Extract case data for workflow initiation
            case_data = self._extract_case_data(analysis_result)
            
            # Emit intermediate results
            if socketio:
                await socketio.emit('prompt_analysis_progress', {
                    'session_id': session_id,
                    'stage': 'keyword_extraction',
                    'keywords_found': len(analysis_result['keywords']),
                    'confidence_score': analysis_result['confidence_score'],
                    'document_type': analysis_result['document_type']
                })
            
            # Step 4: Create enhanced result with integration data
            enhanced_result = {
                **analysis_result,
                'workflow_context': workflow_context,
                'case_data': case_data,
                'suggested_workflow_phases': self._suggest_workflow_phases(analysis_result),
                'integration_metadata': {
                    'session_id': session_id,
                    'processing_timestamp': datetime.now().isoformat(),
                    'maestro_ready': True,
                    'requires_human_review': analysis_result['confidence_score'] < 0.7
                }
            }
            
            # Emit completion event
            if socketio:
                await socketio.emit('prompt_analysis_completed', {
                    'session_id': session_id,
                    'analysis_result': enhanced_result,
                    'ready_for_workflow': True
                })
            
            logger.info(f"Prompt analysis completed for session {session_id}")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Prompt processing failed for session {session_id}: {e}")
            
            # Emit error event
            if socketio:
                await socketio.emit('prompt_analysis_error', {
                    'session_id': session_id,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
            
            # Return basic fallback result
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id,
                'fallback_analysis': True
            }
    
    def _create_workflow_context(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create workflow context from prompt analysis results"""
        
        # Extract key information for workflow
        keywords = analysis_result.get('keywords', [])
        
        # Organize keywords by type for workflow phases
        parties = [kw for kw in keywords if kw['type'] == 'parties']
        legal_issues = [kw for kw in keywords if kw['type'] == 'legal_issue']
        facts = [kw for kw in keywords if kw['type'] == 'facts']
        relief_sought = [kw for kw in keywords if kw['type'] == 'relief_sought']
        
        return {
            'document_type': analysis_result.get('document_type', 'legal_claim'),
            'confidence_score': analysis_result.get('confidence_score', 0.0),
            'extracted_parties': [kw['text'] for kw in parties],
            'identified_legal_issues': [kw['text'] for kw in legal_issues],
            'case_facts': [kw['text'] for kw in facts],
            'desired_relief': [kw['text'] for kw in relief_sought],
            'semantic_relationships': analysis_result.get('semantic_relationships', {}),
            'generated_prompts': analysis_result.get('generated_prompts', []),
            'processing_notes': analysis_result.get('preprocessing_notes', [])
        }
    
    def _extract_case_data(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured case data for workflow processing"""
        
        keywords = analysis_result.get('keywords', [])
        
        # Find primary entities
        parties = [kw['text'] for kw in keywords if kw['type'] == 'parties']
        plaintiff = parties[0] if parties else "Plaintiff"
        defendant = parties[1] if len(parties) > 1 else "Defendant"
        
        # Extract case details
        legal_issues = [kw['text'] for kw in keywords if kw['type'] == 'legal_issue']
        primary_cause = legal_issues[0] if legal_issues else "General Legal Claim"
        
        return {
            'case_name': f"{plaintiff} v. {defendant}",
            'plaintiff_name': plaintiff,
            'defendant_name': defendant,
            'primary_cause_of_action': primary_cause,
            'document_type': analysis_result.get('document_type', 'legal_claim'),
            'case_description': analysis_result.get('original_prompt', ''),
            'extracted_entities': {
                'parties': [kw['text'] for kw in keywords if kw['type'] == 'parties'],
                'legal_issues': [kw['text'] for kw in keywords if kw['type'] == 'legal_issue'],
                'facts': [kw['text'] for kw in keywords if kw['type'] == 'facts'],
                'relief_sought': [kw['text'] for kw in keywords if kw['type'] == 'relief_sought']
            },
            'confidence_metadata': {
                'overall_confidence': analysis_result.get('confidence_score', 0.0),
                'high_confidence_extractions': len([k for k in keywords if k['confidence'] >= 0.8]),
                'requires_validation': analysis_result.get('confidence_score', 0.0) < 0.7
            }
        }
    
    def _suggest_workflow_phases(self, analysis_result: Dict[str, Any]) -> list:
        """Suggest appropriate workflow phases based on analysis"""
        
        confidence = analysis_result.get('confidence_score', 0.0)
        document_type = analysis_result.get('document_type', 'legal_claim')
        keywords = analysis_result.get('keywords', [])
        
        suggested_phases = []
        
        # Always start with intake
        suggested_phases.append({
            'phase': WorkflowPhase.INTAKE.value,
            'priority': 'high',
            'reason': 'Document processing and initial analysis'
        })
        
        # Outline phase - especially important for low confidence
        if confidence < 0.7:
            suggested_phases.append({
                'phase': WorkflowPhase.OUTLINE.value,
                'priority': 'high',
                'reason': 'Human review required due to low confidence analysis',
                'requires_human_approval': True
            })
        else:
            suggested_phases.append({
                'phase': WorkflowPhase.OUTLINE.value,
                'priority': 'medium',
                'reason': 'Case structure planning'
            })
        
        # Research phase - depends on legal issues identified
        legal_issues = [kw for kw in keywords if kw['type'] == 'legal_issue']
        if legal_issues:
            suggested_phases.append({
                'phase': WorkflowPhase.RESEARCH.value,
                'priority': 'high',
                'reason': f'Legal research required for {len(legal_issues)} identified issues'
            })
        
        # Drafting phase
        suggested_phases.append({
            'phase': WorkflowPhase.DRAFTING.value,
            'priority': 'high',
            'reason': f'Document generation for {document_type}',
            'estimated_duration': 2400  # 40 minutes
        })
        
        # Legal review - always include for legal documents
        if document_type == 'legal_claim':
            suggested_phases.append({
                'phase': WorkflowPhase.LEGAL_REVIEW.value,
                'priority': 'critical',
                'reason': 'Legal compliance verification required',
                'requires_human_approval': True
            })
        
        # Final phases
        suggested_phases.extend([
            {
                'phase': WorkflowPhase.EDITING.value,
                'priority': 'medium',
                'reason': 'Document refinement and formatting'
            },
            {
                'phase': WorkflowPhase.ORCHESTRATION.value,
                'priority': 'high',
                'reason': 'Final assembly and delivery preparation'
            }
        ])
        
        return suggested_phases
    
    async def get_analysis_for_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored analysis results for a session"""
        return self.active_analyses.get(session_id)
    
    async def update_analysis_with_feedback(self, session_id: str, 
                                          human_feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Update analysis results with human feedback"""
        
        if session_id not in self.active_analyses:
            raise ValueError(f"No analysis found for session {session_id}")
        
        analysis = self.active_analyses[session_id]
        
        # Update analysis with human corrections
        if 'document_type_correction' in human_feedback:
            analysis['document_type'] = human_feedback['document_type_correction']
        
        if 'keyword_corrections' in human_feedback:
            # Apply keyword corrections
            for correction in human_feedback['keyword_corrections']:
                # Find and update specific keywords
                for keyword in analysis['keywords']:
                    if keyword['text'] == correction.get('original_text'):
                        keyword['text'] = correction.get('corrected_text', keyword['text'])
                        keyword['confidence'] = correction.get('confidence', keyword['confidence'])
        
        # Regenerate workflow context with corrections
        analysis['workflow_context'] = self._create_workflow_context(analysis)
        analysis['case_data'] = self._extract_case_data(analysis)
        
        # Mark as human-reviewed
        analysis['integration_metadata']['human_reviewed'] = True
        analysis['integration_metadata']['review_timestamp'] = datetime.now().isoformat()
        
        return analysis
    
    def get_keyword_summary_for_ui(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get keyword summary formatted for UI display"""
        
        if session_id not in self.active_analyses:
            return None
        
        analysis = self.active_analyses[session_id]
        return self.prompt_service.get_keyword_summary(analysis)
    
    def cleanup_session(self, session_id: str):
        """Clean up stored analysis for completed sessions"""
        if session_id in self.active_analyses:
            del self.active_analyses[session_id]
            logger.info(f"Cleaned up analysis data for session {session_id}")


# Helper function for easy integration with Flask app
def create_prompt_processor(maestro: EnhancedMaestro, llm_service=None) -> EnhancedPromptProcessor:
    """Factory function to create configured prompt processor"""
    return EnhancedPromptProcessor(maestro, llm_service)


def create_prompt_processor(maestro, llm_service=None, mcp_memory_manager=None):
    """Create an enhanced prompt processor with optional MCP memory integration"""
    processor = EnhancedPromptProcessor(maestro, llm_service)
    
    # Add MCP memory integration if available
    if mcp_memory_manager:
        processor.mcp_memory_manager = mcp_memory_manager
        logger.info("Prompt processor configured with MCP memory integration")
    
    return processor