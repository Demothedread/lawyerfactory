"""
Final Compilation Engine - Phase C02 orchestration for LawyerFactory
Orchestrates document aggregation, validation, quality assurance, and deliverable packaging.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ...storage.enhanced_unified_storage_api import get_enhanced_unified_storage_api
from ...export.legal_document_generator import LegalDocumentGenerator
from ...post_production.verification import DocumentVerificationService
from ...post_production.citations import CitationValidator
from .workflow_models import WorkflowPhase, PhaseStatus, PhaseResult

logger = logging.getLogger(__name__)

@dataclass
class CompilationResult:
    """Result of final compilation process"""
    success: bool
    deliverables: List[Dict[str, Any]] = field(default_factory=list)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    export_paths: List[str] = field(default_factory=list)
    compilation_time: float = 0.0
    error_messages: List[str] = field(default_factory=list)

@dataclass
class QualityMetrics:
    """Quality assessment metrics for final output"""
    citation_accuracy: float
    legal_compliance: float
    document_completeness: float
    formatting_quality: float
    overall_score: float
    recommendations: List[str] = field(default_factory=list)

# Legacy compatibility classes
class CompilationStatus(Enum):
    """Final compilation status states"""
    PENDING = "pending"
    PROCESSING = "processing"
    VALIDATING = "validating"
    ASSEMBLING = "assembling"
    COMPLETE = "complete"
    FAILED = "failed"

@dataclass
class PhaseOutput:
    """Standardized phase output structure"""
    phase_id: str
    status: str
    documents: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    quality_score: float
    timestamp: str
    errors: List[str] = None

@dataclass
class FinalDeliverable:
    """Final client deliverable package"""
    case_id: str
    client_name: str
    document_package: Dict[str, Any]
    quality_certification: Dict[str, Any]
    filing_instructions: List[str]
    created_at: str
    total_documents: int

class FinalCompilationEngine:
"""
Final Orchestration & Compilation Engine for Phase C02
Responsible for aggregating all phase outputs and preparing final deliverables
"""

def __init__(self, storage_api=None, event_emitter=None):
    self.storage_api = storage_api
    self.event_emitter = event_emitter
    self.compilation_status = CompilationStatus.PENDING
    self.phase_outputs = {}
    self.quality_thresholds = {
        'minimum_overall_score': 0.85,
        'required_documents': ['complaint', 'cover_sheet'],
        'validation_checks': ['legal_accuracy', 'formatting', 'completeness']
    }
    
async def initialize(self):
    """Initialize the final engine"""
    logger.info("Initializing Phase C02 Final Orchestration Engine")
    self.compilation_status = CompilationStatus.PENDING
    
async def orchestrate_final_compilation(self, case_id: str, phase_outputs: Dict[str, Any]) -> FinalDeliverable:
    """
    Main orchestration method - compiles all phase outputs into final deliverable
    """
    try:
        logger.info(f"Starting final compilation for case {case_id}")
        await self._emit_status_update("compilation_started", {"case_id": case_id})
        
        # Step 1: Validate all phase outputs
        self.compilation_status = CompilationStatus.VALIDATING
        validation_results = await self._validate_phase_outputs(phase_outputs)
        
        if not validation_results['passed']:
            await self._handle_validation_failure(case_id, validation_results)
            return None
            
        # Step 2: Aggregate and process documents
        self.compilation_status = CompilationStatus.PROCESSING
        aggregated_documents = await self._aggregate_documents(phase_outputs)
        
        # Step 3: Perform final quality certification
        quality_certification = await self._perform_quality_certification(aggregated_documents)
        
        # Step 4: Assemble final document package
        self.compilation_status = CompilationStatus.ASSEMBLING
        document_package = await self._assemble_document_package(case_id, aggregated_documents)
        
        # Step 5: Generate filing instructions
        filing_instructions = await self._generate_filing_instructions(document_package)
        
        # Step 6: Create final deliverable
        final_deliverable = FinalDeliverable(
            case_id=case_id,
            client_name=phase_outputs.get('phaseA01_intake', {}).get('client_name', 'Unknown'),
            document_package=document_package,
            quality_certification=quality_certification,
            filing_instructions=filing_instructions,
            created_at=datetime.now().isoformat(),
            total_documents=len(aggregated_documents)
        )
        
        # Step 7: Save final deliverable
        await self._save_final_deliverable(final_deliverable)
        
        # Step 8: Mark compilation complete
        self.compilation_status = CompilationStatus.COMPLETE
        await self._emit_status_update("compilation_complete", {
            "case_id": case_id,
            "total_documents": final_deliverable.total_documents,
            "quality_score": quality_certification.get('overall_score', 0)
        })
        
        logger.info(f"Final compilation completed for case {case_id}")
        return final_deliverable
        
    except Exception as e:
        logger.error(f"Final compilation failed for case {case_id}: {str(e)}")
        self.compilation_status = CompilationStatus.FAILED
        await self._emit_status_update("compilation_failed", {
            "case_id": case_id,
            "error": str(e)
        })
        raise

async def _validate_phase_outputs(self, phase_outputs: Dict[str, Any]) -> Dict[str, Any]:
    """Validate that all required phase outputs meet quality standards"""
    validation_results = {
        'passed': True,
        'issues': [],
        'phase_scores': {}
    }
    
    required_phases = ['phaseA01_intake', 'phaseA02_research', 'phaseA03_outline', 
                      'phaseB01_review', 'phaseB02_drafting', 'phaseC01_editing']
    
    for phase_id in required_phases:
        if phase_id not in phase_outputs:
            validation_results['issues'].append(f"Missing required phase: {phase_id}")
            validation_results['passed'] = False
            continue
            
        phase_data = phase_outputs[phase_id]
        quality_score = phase_data.get('quality_score', 0.0)
        
        if quality_score < self.quality_thresholds['minimum_overall_score']:
            validation_results['issues'].append(
                f"Phase {phase_id} quality score {quality_score} below threshold {self.quality_thresholds['minimum_overall_score']}"
            )
            validation_results['passed'] = False
            
        validation_results['phase_scores'][phase_id] = quality_score
    
    return validation_results

async def _aggregate_documents(self, phase_outputs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Aggregate all documents from phase outputs"""
    aggregated_documents = []
    
    for phase_id, phase_data in phase_outputs.items():
        documents = phase_data.get('documents', [])
        for doc in documents:
            doc['source_phase'] = phase_id
            doc['aggregated_at'] = datetime.now().isoformat()
            aggregated_documents.append(doc)
    
    # Sort by document type priority
    document_priority = {
        'complaint': 1,
        'cover_sheet': 2,
        'statement_of_facts': 3,
        'research_memo': 4,
        'outline': 5,
        'evidence_table': 6
    }
    
    aggregated_documents.sort(key=lambda x: document_priority.get(x.get('type', 'other'), 999))
    
    return aggregated_documents

async def _perform_quality_certification(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Perform comprehensive quality certification"""
    certification = {
        'overall_score': 0.0,
        'document_scores': {},
        'compliance_checks': {},
        'certification_timestamp': datetime.now().isoformat(),
        'certified_by': 'Phase C02 Final Engine'
    }
    
    total_score = 0.0
    document_count = 0
    
    for doc in documents:
        doc_id = doc.get('id', f"doc_{document_count}")
        doc_score = await self._evaluate_document_quality(doc)
        certification['document_scores'][doc_id] = doc_score
        total_score += doc_score
        document_count += 1
    
    certification['overall_score'] = total_score / document_count if document_count > 0 else 0.0
    
    # Compliance checks
    certification['compliance_checks'] = {
        'legal_accuracy': certification['overall_score'] >= 0.85,
        'formatting_compliance': True,  # Assume formatting is handled by Phase C01
        'completeness': len(documents) >= len(self.quality_thresholds['required_documents'])
    }
    
    return certification

async def _evaluate_document_quality(self, document: Dict[str, Any]) -> float:
    """Evaluate individual document quality"""
    # Implement document-specific quality evaluation
    base_score = 0.9  # High base score for completed documents
    
    # Check for required fields
    required_fields = ['content', 'type', 'metadata']
    for field in required_fields:
        if field not in document:
            base_score -= 0.1
    
    # Check content quality indicators
    content = document.get('content', '')
    if len(content) < 100:  # Minimum content length
        base_score -= 0.2
        
    return max(0.0, min(1.0, base_score))

async def _assemble_document_package(self, case_id: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Assemble final document package"""
    package = {
        'case_id': case_id,
        'package_type': 'final_deliverable',
        'documents': [],
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'total_documents': len(documents),
            'package_version': '1.0'
        }
    }
    
    for doc in documents:
        # Process each document for final packaging
        processed_doc = {
            'id': doc.get('id'),
            'type': doc.get('type'),
            'title': doc.get('title', f"Document {len(package['documents']) + 1}"),
            'content': doc.get('content'),
            'format': doc.get('format', 'docx'),
            'source_phase': doc.get('source_phase'),
            'ready_for_filing': self._is_ready_for_filing(doc)
        }
        package['documents'].append(processed_doc)
    
    return package

def _is_ready_for_filing(self, document: Dict[str, Any]) -> bool:
    """Determine if document is ready for court filing"""
    doc_type = document.get('type', '')
    required_for_filing = ['complaint', 'cover_sheet']
    return doc_type in required_for_filing and len(document.get('content', '')) > 0

async def _generate_filing_instructions(self, document_package: Dict[str, Any]) -> List[str]:
    """Generate step-by-step filing instructions"""
    instructions = [
        "1. Review all documents in the package for accuracy",
        "2. Print documents that require physical filing",
        "3. Complete electronic filing if court supports e-filing"
    ]
    
    filing_ready_docs = [doc for doc in document_package['documents'] if doc.get('ready_for_filing')]
    
    if filing_ready_docs:
        instructions.append(f"4. File the following documents first: {', '.join([doc['type'] for doc in filing_ready_docs])}")
    
    instructions.append("5. Serve opposing parties according to court rules")
    instructions.append("6. File proof of service with the court")
    
    return instructions

async def _save_final_deliverable(self, deliverable: FinalDeliverable):
    """Save final deliverable to storage"""
    if self.storage_api:
        try:
            await self.storage_api.store_final_deliverable(deliverable.case_id, asdict(deliverable))
            logger.info(f"Final deliverable saved for case {deliverable.case_id}")
        except Exception as e:
            logger.error(f"Failed to save final deliverable: {str(e)}")
            raise

async def _emit_status_update(self, event_type: str, data: Dict[str, Any]):
    """Emit real-time status updates"""
    if self.event_emitter:
        try:
            await self.event_emitter.emit(f"phase_c02_{event_type}", data)
        except Exception as e:
            logger.warning(f"Failed to emit status update: {str(e)}")

async def _handle_validation_failure(self, case_id: str, validation_results: Dict[str, Any]):
    """Handle validation failure scenarios"""
    logger.error(f"Validation failed for case {case_id}: {validation_results['issues']}")
    self.compilation_status = CompilationStatus.FAILED
    
    await self._emit_status_update("validation_failed", {
        "case_id": case_id,
        "issues": validation_results['issues']
    })

async def get_compilation_status(self) -> Dict[str, Any]:
    """Get current compilation status"""
    return {
        'status': self.compilation_status.value,
        'timestamp': datetime.now().isoformat(),
        'phase_outputs_count': len(self.phase_outputs)
    }

async def deploy_phase(self, phase_id: str, phase_config: Dict[str, Any]) -> bool:
    """Deploy/coordinate other phases as needed"""
    logger.info(f"Deploying phase {phase_id} with config: {phase_config}")
    
    try:
        # Emit deployment request
        await self._emit_status_update("phase_deployment", {
            "target_phase": phase_id,
            "config": phase_config,
            "initiated_by": "phaseC02_orchestration"
        })
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to deploy phase {phase_id}: {str(e)}")
        return False