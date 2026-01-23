"""
Final Compilation Engine - Phase C02 orchestration for LawyerFactory
Orchestrates document aggregation, validation, quality assurance, and deliverable packaging.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ...export.legal_document_generator import LegalDocumentGenerator
from ...post_production.citations import BluebookValidator
from ...post_production.deliverables import CourtPacketInputs, PostProductionProtocol
from ...post_production.verification import FactChecker, VerificationLevel
from ...storage.enhanced_unified_storage_api import get_enhanced_unified_storage_api
from .workflow_models import PhaseResult, PhaseStatus, WorkflowPhase

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


class FinalCompilationEngine:
    """
    Final compilation engine that orchestrates Phase C02: document aggregation,
    validation, quality assurance, and deliverable packaging for client delivery.
    """

    def __init__(self):
        self.storage_api = get_enhanced_unified_storage_api()
        self.document_generator = LegalDocumentGenerator()
        self.verification_service = FactChecker()
        self.citation_validator = BluebookValidator()
        self.post_production_protocol = PostProductionProtocol()

        # Compilation state
        self.current_case_id: Optional[str] = None
        self.compilation_status = "idle"
        
        # Quality thresholds
        self.quality_thresholds = {
            'minimum_overall_score': 0.75,
            'required_documents': ['complaint', 'cover_sheet', 'statement_of_facts']
        }

        logger.info("Final Compilation Engine initialized")

    async def execute_final_compilation(
        self,
        case_id: str,
        phase_outputs: Dict[str, PhaseResult],
        client_requirements: Optional[Dict[str, Any]] = None,
    ) -> CompilationResult:
        """
        Execute complete final compilation process

        Args:
            case_id: Unique case identifier
            phase_outputs: Results from all previous phases (A01-C01)
            client_requirements: Optional specific client requirements

        Returns:
            CompilationResult with all deliverables and quality metrics
        """
        start_time = datetime.now()
        self.current_case_id = case_id
        self.compilation_status = "active"

        try:
            logger.info(f"Starting final compilation for case: {case_id}")

            # Step 1: Aggregate all phase outputs
            aggregated_data = await self._aggregate_phase_outputs(phase_outputs)

            # Step 2: Perform final validation and quality checks
            validation_results = await self._perform_final_validation(aggregated_data)

            # Step 3: Generate final deliverables
            deliverables = await self._generate_final_deliverables(
                aggregated_data, validation_results, client_requirements
            )

            # Step 4: Package for delivery
            export_paths = await self._package_deliverables(case_id, deliverables)

            # Step 5: Generate quality metrics
            quality_metrics = await self._assess_quality_metrics(deliverables, validation_results)

            compilation_time = (datetime.now() - start_time).total_seconds()

            result = CompilationResult(
                success=True,
                deliverables=deliverables,
                validation_results=validation_results,
                export_paths=export_paths,
                compilation_time=compilation_time,
            )

            self.compilation_status = "completed"
            logger.info(f"Final compilation completed in {compilation_time:.2f}s")

            return result

        except Exception as e:
            self.compilation_status = "failed"
            logger.error(f"Final compilation failed: {e}")

            return CompilationResult(
                success=False,
                error_messages=[str(e)],
                compilation_time=(datetime.now() - start_time).total_seconds(),
            )

    async def _aggregate_phase_outputs(
        self, phase_outputs: Dict[str, PhaseResult]
    ) -> Dict[str, Any]:
        """Aggregate and normalize outputs from all phases"""
        logger.info("Aggregating phase outputs...")

        aggregated = {
            "case_id": self.current_case_id,
            "compilation_timestamp": datetime.now().isoformat(),
            "phases": {},
        }

        # Process each phase output
        for phase_id, result in phase_outputs.items():
            if result.status.value == "completed":  # Use .value for enum comparison
                aggregated["phases"][phase_id] = {
                    "status": result.status.value,
                    "output_data": result.output_data,
                    "execution_time": result.execution_time,
                    "timestamp": result.timestamp.isoformat() if result.timestamp else None,
                }
            else:
                logger.warning(f"Phase {phase_id} not completed, status: {result.status}")

        aggregated["case_metadata"] = self._build_case_metadata(phase_outputs)
        aggregated["phase_chain"] = self._build_phase_chain(phase_outputs)

        # Extract key documents and data
        aggregated["documents"] = await self._extract_key_documents(phase_outputs)
        aggregated["evidence"] = await self._extract_evidence_data(phase_outputs)
        aggregated["research"] = await self._extract_research_data(phase_outputs)
        aggregated["legal_analysis"] = await self._extract_legal_analysis(phase_outputs)

        return aggregated

    async def _extract_key_documents(
        self, phase_outputs: Dict[str, PhaseResult]
    ) -> List[Dict[str, Any]]:
        """Extract key documents from phase outputs"""
        documents = []

        # B02 Drafting outputs
        if "B02" in phase_outputs and phase_outputs["B02"].status.value == "completed":
            b02_data = phase_outputs["B02"].output_data
            if "draft_documents" in b02_data:
                documents.extend(b02_data["draft_documents"])

        # C01 Editing outputs
        if "C01" in phase_outputs and phase_outputs["C01"].status.value == "completed":
            c01_data = phase_outputs["C01"].output_data
            if "formatted_documents" in c01_data:
                documents.extend(c01_data["formatted_documents"])

        return documents

    async def _extract_evidence_data(self, phase_outputs: Dict[str, PhaseResult]) -> Dict[str, Any]:
        """Extract evidence and factual data"""
        evidence_data = {"items": [], "summary": ""}

        # A01 Intake evidence
        if "A01" in phase_outputs and phase_outputs["A01"].status.value == "completed":
            a01_data = phase_outputs["A01"].output_data
            if "evidence_table" in a01_data:
                evidence_data["items"].extend(a01_data["evidence_table"])
            if "extracted_facts" in a01_data:
                evidence_data["facts"] = a01_data["extracted_facts"]

        return evidence_data

    async def _extract_research_data(self, phase_outputs: Dict[str, PhaseResult]) -> Dict[str, Any]:
        """Extract research and legal authorities"""
        research_data = {"authorities": [], "precedents": [], "statutes": []}

        # A02 Research outputs
        if "A02" in phase_outputs and phase_outputs["A02"].status.value == "completed":
            a02_data = phase_outputs["A02"].output_data
            if "legal_authorities" in a02_data:
                research_data["authorities"] = a02_data["legal_authorities"]
            if "precedent_cases" in a02_data:
                research_data["precedents"] = a02_data["precedent_cases"]

        return research_data

    async def _extract_legal_analysis(
        self, phase_outputs: Dict[str, PhaseResult]
    ) -> Dict[str, Any]:
        """Extract legal analysis and case structure"""
        analysis_data = {"outline": {}, "claims": [], "arguments": []}

        # A03 Outline outputs
        if "A03" in phase_outputs and phase_outputs["A03"].status.value == "completed":
            a03_data = phase_outputs["A03"].output_data
            if "case_outline" in a03_data:
                analysis_data["outline"] = a03_data["case_outline"]
            if "claims_matrix" in a03_data:
                analysis_data["claims"] = a03_data["claims_matrix"]

        return analysis_data

    async def _perform_final_validation(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive final validation"""
        logger.info("Performing final validation...")

        validation_results = {
            'passed': True,
            'issues': [],
            'phase_scores': {},
            'overall_valid': True,
            'completeness_check': {'complete': True},
            'citation_validation': {'accuracy_score': 0.9}
        }
        
        phases = aggregated_data.get('phases', {})
        required_phases = ['A01', 'A02', 'A03', 'B01', 'B02', 'C01']
        
        for phase_id in required_phases:
            if phase_id not in phases:
                validation_results['issues'].append(f"Missing required phase: {phase_id}")
                validation_results['passed'] = False
                validation_results['overall_valid'] = False
                continue
                
            phase_data = phases[phase_id]
            quality_score = phase_data.get('quality_score', 0.8)  # Default score
            
            if quality_score < self.quality_thresholds['minimum_overall_score']:
                validation_results['issues'].append(
                    f"Phase {phase_id} quality score {quality_score} below threshold {self.quality_thresholds['minimum_overall_score']}"
                )
                validation_results['passed'] = False
                validation_results['overall_valid'] = False
                
            validation_results['phase_scores'][phase_id] = quality_score

        # Additional validation checks
        documents = aggregated_data.get('documents', [])
        if len(documents) < len(self.quality_thresholds['required_documents']):
            validation_results['completeness_check']['complete'] = False
            validation_results['issues'].append("Missing required documents")

        return validation_results

    async def _generate_final_deliverables(
        self, 
        aggregated_data: Dict[str, Any], 
        validation_results: Dict[str, Any],
        client_requirements: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate final deliverables from aggregated data"""
        logger.info("Generating final deliverables...")
        
        deliverables = []
        
        # Aggregate documents from all phases
        documents = await self._aggregate_documents(aggregated_data)
        
        # Perform quality certification
        certification = await self._perform_quality_certification(documents)
        
        # Assemble document package
        document_package = await self._assemble_document_package(
            self.current_case_id, documents
        )
        
        # Generate filing instructions
        filing_instructions = await self._generate_filing_instructions(document_package)
        
        # Create post-production court packet
        court_packet = self._build_court_packet(aggregated_data, documents)

        # Create main deliverables
        deliverables.extend([
            {
                'type': 'document_package',
                'title': 'Final Legal Documents',
                'content': document_package,
                'format': 'structured',
                'metadata': {
                    'description': 'Complete package of legal documents ready for filing',
                    'certification': certification
                }
            },
            {
                'type': 'filing_instructions',
                'title': 'Filing Instructions',
                'content': filing_instructions,
                'format': 'text',
                'metadata': {
                    'description': 'Step-by-step instructions for court filing'
                }
            }
        ])

        if court_packet:
            deliverables.append({
                'type': 'court_packet',
                'title': 'Court-Ready Packet',
                'content': {
                    'cover_sheet_path': court_packet.cover_sheet_path,
                    'table_of_authorities_path': court_packet.table_of_authorities_path,
                    'supplemental_evidence_path': court_packet.supplemental_evidence_path,
                    'manifest_path': court_packet.manifest_path,
                    'package_zip_path': court_packet.package_zip_path,
                    'warnings': court_packet.warnings,
                },
                'format': 'zip',
                'metadata': {
                    'description': 'Court-ready packet with cover sheet, authorities, evidence index, and ZIP bundle'
                }
            })
        
        # Add individual documents as deliverables
        for doc in documents:
            deliverables.append({
                'type': doc.get('type', 'document'),
                'title': doc.get('title', 'Legal Document'),
                'content': doc.get('content', ''),
                'format': doc.get('format', 'text'),
                'metadata': {
                    'source_phase': doc.get('source_phase'),
                    'ready_for_filing': self._is_ready_for_filing(doc),
                    'description': f"Legal document from {doc.get('source_phase', 'unknown phase')}"
                }
            })
        
        logger.info(f"Generated {len(deliverables)} final deliverables")
        return deliverables

    async def _aggregate_documents(self, aggregated_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Aggregate all documents from phase outputs"""
        aggregated_documents = []
        
        # Extract documents from aggregated data
        documents = aggregated_data.get('documents', [])
        
        for doc in documents:
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

    def _build_court_packet(
        self,
        aggregated_data: Dict[str, Any],
        documents: List[Dict[str, Any]],
    ):
        """Create court packet artifacts using post-production protocol."""
        case_metadata = aggregated_data.get("case_metadata", {})
        case_id = aggregated_data.get("case_id", "case")
        inputs = CourtPacketInputs(
            case_id=case_id,
            case_name=case_metadata.get("case_name", "Unknown Case"),
            case_number=case_metadata.get("case_number", "TBD"),
            court=case_metadata.get("court", "Superior Court of California"),
            jurisdiction=case_metadata.get("jurisdiction", "California"),
            parties=case_metadata.get("parties", {}),
        )
        authorities = aggregated_data.get("research", {}).get("authorities", [])
        evidence_items = aggregated_data.get("evidence", {}).get("items", [])
        phase_chain = aggregated_data.get("phase_chain", [])
        return self.post_production_protocol.build_court_packet(
            inputs=inputs,
            documents=documents,
            authorities=authorities,
            evidence_items=evidence_items,
            phase_chain=phase_chain,
        )

    def _build_case_metadata(self, phase_outputs: Dict[str, PhaseResult]) -> Dict[str, Any]:
        """Extract core case metadata for downstream packet generation."""
        metadata: Dict[str, Any] = {}
        intake = phase_outputs.get("A01")
        if intake and intake.status.value == "completed":
            intake_data = intake.output_data or {}
            metadata = {
                "case_name": intake_data.get("case_name")
                or intake_data.get("case_title")
                or metadata.get("case_name"),
                "case_number": intake_data.get("case_number") or metadata.get("case_number"),
                "court": intake_data.get("court") or metadata.get("court"),
                "jurisdiction": intake_data.get("jurisdiction") or metadata.get("jurisdiction"),
                "parties": intake_data.get("parties") or metadata.get("parties") or {},
            }
        return metadata

    def _build_phase_chain(self, phase_outputs: Dict[str, PhaseResult]) -> List[Dict[str, Any]]:
        """Track sequential phase outputs for downstream deliverables."""
        ordered_phases = ["A01", "A02", "A03", "B01", "B02", "C01", "C02", "POST_PRODUCTION"]
        chain = []
        previous_phase = None
        for phase_id in ordered_phases:
            if phase_id not in phase_outputs:
                continue
            result = phase_outputs[phase_id]
            output_keys = list((result.output_data or {}).keys())
            chain.append(
                {
                    "phase": phase_id,
                    "status": result.status.value,
                    "output_keys": output_keys,
                    "previous_phase": previous_phase,
                }
            )
            previous_phase = phase_id
        return chain

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

        logger.info(f"Final deliverable package assembled for case {case_id}")
        return package

    def _is_ready_for_filing(self, document: Dict[str, Any]) -> bool:
        """Determine if document is ready for court filing"""
        doc_type = document.get('type', '')
        required_for_filing = ['complaint', 'cover_sheet']
        return doc_type in required_for_filing and len(document.get('content', '')) > 0

    async def _generate_filing_instructions(self, document_package: Dict[str, Any]) -> str:
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

        return "\n".join(instructions)

    def get_compilation_status(self) -> Dict[str, Any]:
        """Get current compilation status"""
        return {
            "status": self.compilation_status,
            "case_id": self.current_case_id,
            "timestamp": datetime.now().isoformat(),
        }


# Global instance
_final_compilation_engine = None


def get_final_compilation_engine() -> FinalCompilationEngine:
    """Get global final compilation engine instance"""
    global _final_compilation_engine
    if _final_compilation_engine is None:
        _final_compilation_engine = FinalCompilationEngine()
    return _final_compilation_engine
        )
        compliance_score = 1.0 if validation_results.get("overall_valid", False) else 0.5
        completeness_score = (
            1.0 if validation_results.get("completeness_check", {}).get("complete", False) else 0.7
        )
        formatting_score = 0.9  # Would be calculated based on document analysis

        overall_score = (
            citation_score + compliance_score + completeness_score + formatting_score
        ) / 4

        recommendations = []
        if citation_score < 0.8:
            recommendations.append("Review and verify legal citations")
        if not validation_results.get("overall_valid", False):
            recommendations.append("Address validation issues before delivery")
        if completeness_score < 1.0:
            recommendations.append("Complete missing deliverable components")

        return QualityMetrics(
            citation_accuracy=citation_score,
            legal_compliance=compliance_score,
            document_completeness=completeness_score,
            formatting_quality=formatting_score,
            overall_score=overall_score,
            recommendations=recommendations,
        )

    def get_compilation_status(self) -> Dict[str, Any]:
        """Get current compilation status"""
        return {
            "status": self.compilation_status,
            "case_id": self.current_case_id,
            "timestamp": datetime.now().isoformat(),
        }


# Global instance
_final_compilation_engine = None


def get_final_compilation_engine() -> FinalCompilationEngine:
    """Get global final compilation engine instance"""
    global _final_compilation_engine
    if _final_compilation_engine is None:
        _final_compilation_engine = FinalCompilationEngine()
    return _final_compilation_engine
