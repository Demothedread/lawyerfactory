"""
# Script Name: ai_document_agent.py
# Description: AI Document Agent for automated legal document generation. Integrates with the AIDocumentGenerator to provide intelligent form selection, field mapping, and PDF generation capabilities.
# Relationships:
#   - Entity Type: Agent
#   - Directory Group: Ingestion
#   - Group Tags: null
AI Document Agent for automated legal document generation.
Integrates with the AIDocumentGenerator to provide intelligent form selection,
field mapping, and PDF generation capabilities.
"""

import asyncio
from datetime import datetime
import logging
from typing import Any, Dict

from lawyerfactory.document_generator.ai_document_generator import AIDocumentGenerator

from ..agent_registry import AgentCapability, AgentConfig, AgentInterface
from ..workflow_models import WorkflowPhase, WorkflowTask

logger = logging.getLogger(__name__)


class AIDocumentAgent(AgentInterface):
    """
    AI-powered document generation agent that integrates with the LawyerFactory
    orchestration system to provide intelligent legal document creation.
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)

        # Initialize AI Document Generator
        forms_directory = (
            config.config.get("forms_directory", "docs/Court_files")
            if config.config
            else "docs/Court_files"
        )
        output_directory = (
            config.config.get("output_directory", "output")
            if config.config
            else "output"
        )

        self.ai_generator = AIDocumentGenerator(
            forms_directory=forms_directory, output_directory=output_directory
        )

        # Agent configuration
        self.max_retries = config.config.get("max_retries", 3) if config.config else 3
        self.processing_timeout = (
            config.config.get("processing_timeout", 300) if config.config else 300
        )  # 5 minutes

        logger.info(f"AI Document Agent initialized: {self.agent_type}")

    async def execute_task(
        self, task: WorkflowTask, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute AI document generation task based on workflow phase and context.

        Args:
            task: The workflow task to execute
            context: Workflow context including case data and previous results

        Returns:
            Dictionary containing generation results and metadata
        """
        logger.info(
            f"AI Document Agent executing task {task.id} in phase {task.phase.value}"
        )

        try:
            # Extract case data from context
            case_data = self._extract_case_data(context)
            case_name = context.get(
                "case_name", f"Case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # Determine task type based on phase and description
            if task.phase == WorkflowPhase.DRAFTING:
                return await self._handle_drafting_task(
                    task, case_data, case_name, context
                )
            elif "ai_case_classification" in task.description.lower():
                return await self._handle_classification_task(case_data, context)
            elif "pdf_form_processing" in task.description.lower():
                return await self._handle_form_processing_task(
                    case_data, case_name, context
                )
            elif "automated_field_mapping" in task.description.lower():
                return await self._handle_field_mapping_task(case_data, context)
            elif "court_form_generation" in task.description.lower():
                return await self._handle_form_generation_task(
                    case_data, case_name, context
                )
            else:
                # Default to full document generation
                return await self._handle_full_generation_task(
                    case_data, case_name, context
                )

        except Exception as e:
            logger.error(f"AI Document Agent task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": task.id,
                "agent_type": self.agent_type,
                "timestamp": datetime.now().isoformat(),
            }

    async def _handle_drafting_task(
        self,
        task: WorkflowTask,
        case_data: Dict[str, Any],
        case_name: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle AI-assisted drafting during the DRAFTING phase."""
        logger.info("Executing AI document generation for DRAFTING phase")

        # Check if traditional document generation is already in progress
        existing_drafts = context.get("drafting_results", {})

        # Generate AI documents in parallel to traditional drafting
        generation_options = {
            "parallel_execution": True,
            "complement_traditional": True,
            "focus_areas": ["forms", "templates", "compliance_checks"],
        }

        # Execute AI document generation
        result = await asyncio.wait_for(
            self._run_ai_generation(case_data, case_name, generation_options),
            timeout=self.processing_timeout,
        )

        return {
            "success": result.success,
            "ai_documents_generated": result.forms_generated,
            "fields_filled": result.fields_filled,
            "completion_percentage": result.completion_percentage,
            "ready_for_filing": result.ready_for_filing,
            "case_classification": (
                result.case_classification.primary_type.value
                if result.case_classification
                else None
            ),
            "form_types": (
                [mapping.form_name for mapping in result.form_mappings]
                if result.form_mappings
                else []
            ),
            "output_files": [
                str(filling.output_path)
                for filling in result.filling_results
                if filling.success
            ],
            "processing_time": result.total_processing_time,
            "warnings": result.warnings,
            "errors": result.errors,
            "task_id": task.id,
            "agent_type": self.agent_type,
            "timestamp": datetime.now().isoformat(),
            "integration_type": "drafting_parallel",
        }

    async def _handle_classification_task(
        self, case_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle AI case classification task."""
        logger.info("Executing AI case classification")

        classification = self.ai_generator._classify_case(case_data)

        return {
            "success": True,
            "classification": {
                "primary_type": classification.primary_type.value,
                "confidence": classification.confidence,
                "secondary_types": [
                    (t[0].value, t[1]) for t in classification.secondary_types
                ],
                "key_indicators": classification.key_indicators,
                "reasoning": classification.reasoning,
                "urgency_level": classification.urgency_level,
            },
            "agent_type": self.agent_type,
            "timestamp": datetime.now().isoformat(),
        }

    async def _handle_form_processing_task(
        self, case_data: Dict[str, Any], case_name: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle PDF form processing task."""
        logger.info("Executing PDF form processing")

        # First classify the case to determine appropriate forms
        classification = self.ai_generator._classify_case(case_data)
        form_selection = self.ai_generator._select_forms(classification, {})

        return {
            "success": True,
            "forms_identified": len(form_selection.primary_forms),
            "primary_forms": [form.form_name for form in form_selection.primary_forms],
            "optional_forms": [
                form.form_name for form in form_selection.optional_forms
            ],
            "total_forms": form_selection.total_forms,
            "selection_reasoning": form_selection.selection_reasoning,
            "warnings": form_selection.warnings,
            "agent_type": self.agent_type,
            "timestamp": datetime.now().isoformat(),
        }

    async def _handle_field_mapping_task(
        self, case_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle automated field mapping task."""
        logger.info("Executing automated field mapping")

        # Get previously selected forms from context or classify case
        form_selection = context.get("form_selection")
        if not form_selection:
            classification = self.ai_generator._classify_case(case_data)
            form_selection = self.ai_generator._select_forms(classification, {})
        else:
            classification = self.ai_generator._classify_case(case_data)

        # Perform field mapping
        mappings = self.ai_generator._map_fields(
            form_selection, case_data, classification
        )

        total_mappings = sum(len(mapping.mappings) for mapping in mappings)
        successful_mappings = sum(
            len([m for m in mapping.mappings if m.confidence > 0.5])
            for mapping in mappings
        )

        return {
            "success": True,
            "mappings_created": total_mappings,
            "high_confidence_mappings": successful_mappings,
            "mapping_details": [
                {
                    "form": mapping.form_name,
                    "total_fields": len(mapping.mappings),
                    "mapped_fields": len(
                        [m for m in mapping.mappings if m.confidence > 0.3]
                    ),
                    "confidence": mapping.mapping_confidence,
                }
                for mapping in mappings
            ],
            "agent_type": self.agent_type,
            "timestamp": datetime.now().isoformat(),
        }

    async def _handle_form_generation_task(
        self, case_data: Dict[str, Any], case_name: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle court form generation task."""
        logger.info("Executing court form generation")

        # Execute full AI generation pipeline
        result = await self._run_ai_generation(case_data, case_name, {})

        return {
            "success": result.success,
            "forms_generated": result.forms_generated,
            "output_files": [
                str(filling.output_path)
                for filling in result.filling_results
                if filling.success
            ],
            "completion_percentage": result.completion_percentage,
            "ready_for_filing": result.ready_for_filing,
            "processing_time": result.total_processing_time,
            "agent_type": self.agent_type,
            "timestamp": datetime.now().isoformat(),
        }

    async def _handle_full_generation_task(
        self, case_data: Dict[str, Any], case_name: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle full AI document generation task."""
        logger.info("Executing full AI document generation")

        result = await self._run_ai_generation(case_data, case_name, {})

        return {
            "success": result.success,
            "case_classification": (
                result.case_classification.primary_type.value
                if result.case_classification
                else None
            ),
            "forms_generated": result.forms_generated,
            "fields_filled": result.fields_filled,
            "completion_percentage": result.completion_percentage,
            "ready_for_filing": result.ready_for_filing,
            "output_files": [
                str(filling.output_path)
                for filling in result.filling_results
                if filling.success
            ],
            "processing_time": result.total_processing_time,
            "warnings": result.warnings,
            "errors": result.errors,
            "package_info": result.package_info,
            "agent_type": self.agent_type,
            "timestamp": datetime.now().isoformat(),
        }

    async def _run_ai_generation(
        self, case_data: Dict[str, Any], case_name: str, options: Dict[str, Any]
    ):
        """Run AI document generation in async context."""
        # Since the AI generator is synchronous, run it in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.ai_generator.generate_documents, case_data, case_name, options
        )

    def _extract_case_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and format case data from workflow context."""
        case_data = context.get("case_data", {})

        # If case_data is empty, try to construct from other context fields
        if not case_data:
            case_data = {
                "case_name": context.get("case_name", "Unknown Case"),
                "case_description": context.get("case_description", ""),
                "input_documents": context.get("input_documents", []),
                "global_context": context.get("global_context", {}),
                # Extract any entity data from knowledge graph results
                "entities": context.get("entities_extracted", []),
                "legal_issues": context.get("legal_issues", []),
                "parties": context.get("parties", []),
            }

        return case_data

    async def health_check(self) -> bool:
        """Check if the AI Document Agent is healthy and ready."""
        try:
            # Check if AI generator components are available
            status = self.ai_generator.get_system_status()
            return status.get("overall_status", {}).get("ready", False)
        except Exception as e:
            logger.error(f"AI Document Agent health check failed: {e}")
            return False

    async def initialize(self) -> None:
        """Initialize the AI Document Agent."""
        logger.info(f"Initializing AI Document Agent: {self.agent_type}")

        # Verify forms directory exists
        if not self.ai_generator.forms_directory.exists():
            logger.warning(
                f"Forms directory not found: {self.ai_generator.forms_directory}"
            )

        # Verify output directory exists or create it
        self.ai_generator.output_directory.mkdir(exist_ok=True)

        logger.info("AI Document Agent initialization complete")

    async def cleanup(self) -> None:
        """Clean up AI Document Agent resources."""
        logger.info(f"Cleaning up AI Document Agent: {self.agent_type}")
        # Add any cleanup logic if needed
        pass


# Agent configuration for registration
AI_DOCUMENT_AGENT_CONFIG = AgentConfig(
    agent_type="AIDocumentAgent",
    max_concurrent=2,  # Allow up to 2 concurrent AI generation tasks
    timeout_seconds=600,  # 10 minutes timeout for complex documents
    retry_attempts=2,
    capabilities=[
        AgentCapability.AI_CASE_CLASSIFICATION,
        AgentCapability.PDF_FORM_PROCESSING,
        AgentCapability.AUTOMATED_FIELD_MAPPING,
        AgentCapability.COURT_FORM_GENERATION,
        AgentCapability.LEGAL_WRITING,  # Can assist with drafting
    ],
    config={
        "forms_directory": "docs/Court_files",
        "output_directory": "output",
        "max_retries": 3,
        "processing_timeout": 300,
    },
)
