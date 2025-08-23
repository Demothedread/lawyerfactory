"""
# Script Name: integration_legacy.py
# Description: Skeletal Outline Integration Module Integrates the skeletal outline generation system with the Maestro orchestrator and provides API endpoints for the complete workflow.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
Skeletal Outline Integration Module
Integrates the skeletal outline generation system with the Maestro orchestrator
and provides API endpoints for the complete workflow.
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from enhanced_knowledge_graph import EnhancedKnowledgeGraph
from prompt_chain_orchestrator import (PromptChainOrchestrator,
                                       PromptChainResult)
from skeletal_outline_generator import (SkeletalOutline,
                                        SkeletalOutlineGenerator)

from maestro.evidence_api import EvidenceAPI
from src.claims_matrix.comprehensive_claims_matrix_integration import \
    ComprehensiveClaimsMatrixIntegration

try:
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except ImportError:
    web = None
    AIOHTTP_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class SkeletalOutlineWorkflow:
    """Complete skeletal outline workflow state"""
    workflow_id: str
    case_id: str
    session_id: str
    status: str  # generating, completed, failed
    skeletal_outline: Optional[SkeletalOutline] = None
    prompt_chain_result: Optional[PromptChainResult] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        if self.skeletal_outline:
            result['skeletal_outline'] = self.skeletal_outline.to_dict()
        if self.prompt_chain_result:
            result['prompt_chain_result'] = asdict(self.prompt_chain_result)
        return result


class SkeletalOutlineIntegration:
    """Integration layer for skeletal outline generation system"""
    
    def __init__(self, enhanced_kg: EnhancedKnowledgeGraph,
                 claims_matrix: ComprehensiveClaimsMatrixIntegration,
                 evidence_api: EvidenceAPI,
                 llm_service=None,
                 storage_path: str = "skeletal_outlines"):
        
        self.kg = enhanced_kg
        self.claims_matrix = claims_matrix
        self.evidence_api = evidence_api
        self.llm_service = llm_service
        
        # Initialize core components
        self.outline_generator = SkeletalOutlineGenerator(
            enhanced_kg, claims_matrix, evidence_api
        )
        self.prompt_orchestrator = PromptChainOrchestrator(
            enhanced_kg, llm_service
        )
        
        # Storage setup
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Workflow tracking
        self.active_workflows: Dict[str, SkeletalOutlineWorkflow] = {}
        
        logger.info("Skeletal Outline Integration initialized")
    
    async def start_skeletal_outline_workflow(self, case_id: str, session_id: str,
                                            document_type: str = "complaint") -> str:
        """Start complete skeletal outline generation workflow"""
        try:
            workflow_id = f"outline_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.active_workflows)}"
            
            # Create workflow tracking
            workflow = SkeletalOutlineWorkflow(
                workflow_id=workflow_id,
                case_id=case_id,
                session_id=session_id,
                status="generating"
            )
            
            self.active_workflows[workflow_id] = workflow
            
            logger.info(f"Starting skeletal outline workflow {workflow_id} for case {case_id}")
            
            # Start async generation
            asyncio.create_task(self._execute_workflow(workflow))
            
            return workflow_id
            
        except Exception as e:
            logger.exception(f"Failed to start skeletal outline workflow: {e}")
            raise
    
    async def _execute_workflow(self, workflow: SkeletalOutlineWorkflow):
        """Execute complete skeletal outline generation workflow"""
        try:
            logger.info(f"Executing workflow {workflow.workflow_id}")
            
            # Step 1: Generate skeletal outline
            logger.info("Generating skeletal outline...")
            skeletal_outline = self.outline_generator.generate_skeletal_outline(
                workflow.case_id, workflow.session_id
            )
            workflow.skeletal_outline = skeletal_outline
            
            # Step 2: Execute prompt chain
            logger.info("Executing prompt chain...")
            prompt_result = await self.prompt_orchestrator.execute_prompt_chain(skeletal_outline)
            workflow.prompt_chain_result = prompt_result
            
            # Step 3: Save results
            await self._save_workflow_results(workflow)
            
            # Update workflow status
            workflow.status = "completed" if prompt_result.success else "failed"
            workflow.completed_at = datetime.now()
            
            if not prompt_result.success:
                workflow.error_message = "; ".join(prompt_result.errors)
            
            logger.info(f"Workflow {workflow.workflow_id} completed with status: {workflow.status}")
            
        except Exception as e:
            logger.exception(f"Workflow {workflow.workflow_id} failed: {e}")
            workflow.status = "failed"
            workflow.error_message = str(e)
            workflow.completed_at = datetime.now()
    
    async def _save_workflow_results(self, workflow: SkeletalOutlineWorkflow):
        """Save workflow results to storage"""
        try:
            workflow_file = self.storage_path / f"{workflow.workflow_id}.json"
            
            # Save complete workflow data
            with open(workflow_file, 'w') as f:
                json.dump(workflow.to_dict(), f, indent=2, default=str)
            
            # Save final document separately
            if workflow.prompt_chain_result and workflow.prompt_chain_result.final_document:
                document_file = self.storage_path / f"{workflow.workflow_id}_complaint.txt"
                with open(document_file, 'w') as f:
                    f.write(workflow.prompt_chain_result.final_document)
            
            logger.info(f"Saved workflow results for {workflow.workflow_id}")
            
        except Exception as e:
            logger.error(f"Failed to save workflow results: {e}")
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status and results"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return None
        
        status_data = {
            'workflow_id': workflow.workflow_id,
            'case_id': workflow.case_id,
            'session_id': workflow.session_id,
            'status': workflow.status,
            'created_at': workflow.created_at.isoformat(),
            'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None,
            'error_message': workflow.error_message
        }
        
        # Add skeletal outline summary
        if workflow.skeletal_outline:
            status_data['outline_summary'] = {
                'outline_id': workflow.skeletal_outline.outline_id,
                'section_count': len(workflow.skeletal_outline.sections),
                'estimated_pages': workflow.skeletal_outline.estimated_page_count
            }
        
        # Add prompt chain results
        if workflow.prompt_chain_result:
            status_data['generation_results'] = {
                'success': workflow.prompt_chain_result.success,
                'word_count': workflow.prompt_chain_result.total_word_count,
                'estimated_pages': workflow.prompt_chain_result.estimated_pages,
                'rule_12b6_compliance_score': workflow.prompt_chain_result.rule_12b6_compliance_score,
                'generation_time_seconds': workflow.prompt_chain_result.generation_time_seconds,
                'sections_generated': len(workflow.prompt_chain_result.generated_sections),
                'errors': workflow.prompt_chain_result.errors,
                'warnings': workflow.prompt_chain_result.warnings
            }
        
        return status_data
    
    def get_generated_document(self, workflow_id: str) -> Optional[str]:
        """Get the final generated document"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow or not workflow.prompt_chain_result:
            return None
        
        return workflow.prompt_chain_result.final_document
    
    def get_section_content(self, workflow_id: str, section_id: str) -> Optional[str]:
        """Get content for specific section"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow or not workflow.prompt_chain_result:
            return None
        
        return workflow.prompt_chain_result.generated_sections.get(section_id)
    
    def list_active_workflows(self) -> List[Dict[str, Any]]:
        """List all active workflows"""
        return [
            {
                'workflow_id': wf.workflow_id,
                'case_id': wf.case_id,
                'status': wf.status,
                'created_at': wf.created_at.isoformat(),
                'completed_at': wf.completed_at.isoformat() if wf.completed_at else None
            }
            for wf in self.active_workflows.values()
        ]
    
    async def regenerate_section(self, workflow_id: str, section_id: str, 
                               custom_prompt: Optional[str] = None) -> bool:
        """Regenerate specific section with optional custom prompt"""
        try:
            workflow = self.active_workflows.get(workflow_id)
            if not workflow or not workflow.skeletal_outline:
                return False
            
            # Find the section
            target_section = None
            for section in workflow.skeletal_outline.sections:
                if section.section_id == section_id:
                    target_section = section
                    break
                # Check subsections
                for subsection in section.subsections:
                    if subsection.section_id == section_id:
                        target_section = subsection
                        break
            
            if not target_section:
                return False
            
            # Override prompt if custom provided
            if custom_prompt:
                target_section.prompt_template = custom_prompt
            
            # Regenerate section
            if workflow.prompt_chain_result:
                context = workflow.prompt_chain_result.generation_context
                new_content = await self.prompt_orchestrator._execute_section_prompt(
                    target_section, workflow.skeletal_outline, context
                )
                
                # Update results
                workflow.prompt_chain_result.generated_sections[section_id] = new_content
                workflow.prompt_chain_result.final_document = self.prompt_orchestrator._compile_final_document(
                    workflow.skeletal_outline, context
                )
                
                # Save updated results
                await self._save_workflow_results(workflow)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to regenerate section {section_id}: {e}")
            return False


class SkeletalOutlineAPI:
    """API endpoints for skeletal outline system"""
    
    def __init__(self, integration: SkeletalOutlineIntegration):
        self.integration = integration
    
    async def start_workflow(self, request) -> web.Response:
        """Start skeletal outline generation workflow"""
        try:
            data = await request.json()
            case_id = data.get('case_id')
            session_id = data.get('session_id')
            document_type = data.get('document_type', 'complaint')
            
            if not case_id or not session_id:
                return web.json_response(
                    {'error': 'case_id and session_id are required'}, 
                    status=400
                )
            
            workflow_id = await self.integration.start_skeletal_outline_workflow(
                case_id, session_id, document_type
            )
            
            return web.json_response({
                'success': True,
                'workflow_id': workflow_id,
                'message': 'Skeletal outline generation started'
            })
            
        except Exception as e:
            logger.error(f"Failed to start workflow: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_workflow_status(self, request) -> web.Response:
        """Get workflow status and progress"""
        try:
            workflow_id = request.match_info.get('workflow_id')
            
            status = self.integration.get_workflow_status(workflow_id)
            if not status:
                return web.json_response(
                    {'error': 'Workflow not found'}, 
                    status=404
                )
            
            return web.json_response(status)
            
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_generated_document(self, request) -> web.Response:
        """Get final generated document"""
        try:
            workflow_id = request.match_info.get('workflow_id')
            
            document = self.integration.get_generated_document(workflow_id)
            if not document:
                return web.json_response(
                    {'error': 'Document not found or not ready'}, 
                    status=404
                )
            
            return web.json_response({
                'workflow_id': workflow_id,
                'document': document,
                'word_count': len(document.split())
            })
            
        except Exception as e:
            logger.error(f"Failed to get generated document: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_section_content(self, request) -> web.Response:
        """Get content for specific section"""
        try:
            workflow_id = request.match_info.get('workflow_id')
            section_id = request.match_info.get('section_id')
            
            content = self.integration.get_section_content(workflow_id, section_id)
            if not content:
                return web.json_response(
                    {'error': 'Section not found'}, 
                    status=404
                )
            
            return web.json_response({
                'workflow_id': workflow_id,
                'section_id': section_id,
                'content': content,
                'word_count': len(content.split())
            })
            
        except Exception as e:
            logger.error(f"Failed to get section content: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def list_workflows(self, request) -> web.Response:
        """List all active workflows"""
        try:
            workflows = self.integration.list_active_workflows()
            return web.json_response({
                'workflows': workflows,
                'total_count': len(workflows)
            })
            
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def regenerate_section(self, request) -> web.Response:
        """Regenerate specific section"""
        try:
            workflow_id = request.match_info.get('workflow_id')
            section_id = request.match_info.get('section_id')
            
            data = await request.json()
            custom_prompt = data.get('custom_prompt')
            
            success = await self.integration.regenerate_section(
                workflow_id, section_id, custom_prompt
            )
            
            if success:
                return web.json_response({
                    'success': True,
                    'message': f'Section {section_id} regenerated successfully'
                })
            else:
                return web.json_response(
                    {'error': 'Failed to regenerate section'}, 
                    status=400
                )
            
        except Exception as e:
            logger.error(f"Failed to regenerate section: {e}")
            return web.json_response({'error': str(e)}, status=500)


def setup_skeletal_outline_routes(app, api_instance: SkeletalOutlineAPI):
    """Setup API routes for skeletal outline system"""
    if not AIOHTTP_AVAILABLE:
        logger.warning("aiohttp not available - API routes not configured")
        return
    
    # Workflow management routes
    app.router.add_post('/api/skeletal-outline/start', api_instance.start_workflow)
    app.router.add_get('/api/skeletal-outline/workflows', api_instance.list_workflows)
    app.router.add_get('/api/skeletal-outline/workflow/{workflow_id}/status', api_instance.get_workflow_status)
    
    # Document retrieval routes
    app.router.add_get('/api/skeletal-outline/workflow/{workflow_id}/document', api_instance.get_generated_document)
    app.router.add_get('/api/skeletal-outline/workflow/{workflow_id}/section/{section_id}', api_instance.get_section_content)
    
    # Section management routes
    app.router.add_post('/api/skeletal-outline/workflow/{workflow_id}/section/{section_id}/regenerate', api_instance.regenerate_section)
    
    logger.info("Skeletal outline API routes configured")


def create_skeletal_outline_system(enhanced_kg: EnhancedKnowledgeGraph,
                                 claims_matrix: ComprehensiveClaimsMatrixIntegration,
                                 evidence_api: EvidenceAPI,
                                 llm_service=None) -> SkeletalOutlineIntegration:
    """Factory function to create complete skeletal outline system"""
    return SkeletalOutlineIntegration(
        enhanced_kg, claims_matrix, evidence_api, llm_service
    )


async def test_skeletal_outline_integration():
    """Test the complete skeletal outline integration"""
    try:
        from enhanced_knowledge_graph import EnhancedKnowledgeGraph

        from maestro.evidence_api import EvidenceAPI
        from src.claims_matrix.comprehensive_claims_matrix_integration import \
            ComprehensiveClaimsMatrixIntegration

        # Initialize components
        kg = EnhancedKnowledgeGraph()
        claims_matrix = ComprehensiveClaimsMatrixIntegration(kg)
        evidence_api = EvidenceAPI()
        
        # Create integration
        integration = create_skeletal_outline_system(kg, claims_matrix, evidence_api)
        
        # Test workflow
        workflow_id = await integration.start_skeletal_outline_workflow(
            "test_case_001", "test_session_001"
        )
        
        print(f"Started workflow: {workflow_id}")
        
        # Wait a bit for async processing
        await asyncio.sleep(2)
        
        # Check status
        status = integration.get_workflow_status(workflow_id)
        print(f"Workflow status: {status}")
        
        # Get document if completed
        if status and status.get('status') == 'completed':
            document = integration.get_generated_document(workflow_id)
            if document:
                print(f"Generated document ({len(document.split())} words):")
                print(document[:500] + "..." if len(document) > 500 else document)
        
        return integration
        
    except Exception as e:
        print(f"Test failed: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(test_skeletal_outline_integration())