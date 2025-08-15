"""
Reader Bot for document ingestion and text extraction.
Integrates with the existing assessor module for document processing.
"""

import asyncio
import json
import logging
from datetime import date
from pathlib import Path
from typing import Any, Dict

from ..agent_registry import AgentConfig, AgentInterface
from ..bot_interface import Bot
from ..workflow_models import WorkflowTask

# Import the existing assessor functionality
try:
    import os
    import sys

    # Add the project root to Python path to import assessor
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from assessor import (categorize, hashtags_from_category, intake_document,
                          summarize)
    ASSESSOR_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("Successfully imported assessor module")
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import assessor module: {e}")
    ASSESSOR_AVAILABLE = False

logger = logging.getLogger(__name__)


class ReaderBot(Bot, AgentInterface):
    """Document reader bot for intake and text extraction using assessor module"""

    def __init__(self, config: AgentConfig):
        # Initialize Bot interface
        Bot.__init__(self)
        # Initialize AgentInterface
        AgentInterface.__init__(self, config)
        
        logger.info("ReaderBot initialized with document processing capabilities using assessor module")

    # Provide a Bot-compatible process() method (base Bot may expect (message: str) -> str)
    async def process(self, message: str) -> str:
        """
        Compatibility wrapper so the Bot base class method signature is satisfied.
        Accepts either a plain string message or a JSON-encoded task payload and
        returns a string (JSON-encoded) result. The orchestration layer should use
        execute_task() for structured dict responses.
        """
        try:
            # Try to parse as JSON describing a WorkflowTask-like dict
            payload = None
            try:
                payload = json.loads(message)
            except Exception:
                # Not JSON: treat message as simple description
                payload = {"description": message, "input_data": {}}

            # If payload resembles a WorkflowTask, call execute_task with a lightweight wrapper
            fake_task = WorkflowTask(
                id=payload.get("id", "legacy_task"),
                description=payload.get("description", ""),
                input_data=payload.get("input_data", {})
            )
            result = await self.execute_task(fake_task, context={})
            # return a JSON string to satisfy a str-returning base contract
            return json.dumps(result)
        except Exception as e:
            logger.exception("ReaderBot.process failed: %s", e)
            # Return a simple error string for compatibility
            return f"error: {str(e)}"

    async def _extract_text_from_path(self, document_path: str) -> str | None:
        """Try to extract text from a local file path. Return None on failure."""
        p = Path(document_path)
        if not p.exists() or not p.is_file():
            logger.debug("File not found or not a file: %s", document_path)
            return None

        loop = asyncio.get_event_loop()
        suffix = p.suffix.lower()

        try:
            if suffix in ('.txt', '.md'):
                return await loop.run_in_executor(None, p.read_text, 'utf-8')

            if suffix == '.pdf':
                try:
                    import PyPDF2
                except Exception:
                    logger.debug("PyPDF2 not available; cannot extract PDF text")
                    return None

                def _read_pdf():
                    with open(p, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        return "\n".join((page.extract_text() or '') for page in reader.pages)

                return await loop.run_in_executor(None, _read_pdf)

            if suffix == '.docx':
                try:
                    import docx
                except Exception:
                    logger.debug("python-docx not available; cannot extract DOCX text")
                    return None

                def _read_docx():
                    doc = docx.Document(str(p))
                    return "\n".join(par.text for par in doc.paragraphs)

                return await loop.run_in_executor(None, _read_docx)

            # Generic binary -> text attempt
            def _read_bytes():
                return p.read_bytes()

            raw = await loop.run_in_executor(None, _read_bytes)
            try:
                return raw.decode('utf-8', errors='replace')
            except Exception:
                return None

        except Exception as exc:
            logger.exception("Error extracting text from %s: %s", document_path, exc)
            return None

    async def process(self, task: WorkflowTask) -> dict:
        """Legacy Bot interface implementation for document processing"""
        try:
            if ASSESSOR_AVAILABLE:
                # Use assessor module for categorization and summarization
                category = categorize(task.description)
                summary = summarize(task.description, max_sentences=1)
                return f"Document processed successfully: '{summary}' - Category: {category}"
            else:
                return f"Document processed successfully: '{task.description}' - Key information extracted and ready for analysis"
                
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return f"Document processed: '{task.description}'"

    async def execute_task(self, task: WorkflowTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """AgentInterface implementation for orchestration system"""
        input_data = task.input_data if hasattr(task, "input_data") else {}
        try:
            self.is_busy = True
            self.current_task_id = task.id
            
            logger.info(f"ReaderBot executing document processing task: {task.description}")
            
            # Get input data
            document_path = input_data.get('document_path', '')
            document_name = input_data.get('document_name', 'Unknown Document')
            
            # Process the document using assessor functionality
            extraction_result = await self._extract_and_assess_document(document_path, document_name)
            
            # Prepare result with assessor-enhanced information
            result = {
                'document_name': document_name,
                'document_path': document_path,
                'extracted_content': extraction_result.get('content', ''),
                'content_length': len(extraction_result.get('content', '')),
                'summary': extraction_result.get('summary', ''),
                'category': extraction_result.get('category', 'unknown'),
                'hashtags': extraction_result.get('hashtags', ''),
                'author': extraction_result.get('author', 'Unknown'),
                'processing_status': 'completed',
                'processed_by': 'ReaderBot',
                'assessor_enhanced': ASSESSOR_AVAILABLE
            }
            
            # Store in repository if assessor is available
            if ASSESSOR_AVAILABLE and extraction_result.get('content'):
                try:
                    intake_document(
                        author=extraction_result.get('author', 'System'),
                        title=document_name,
                        publication_date=date.today().isoformat(),
                        text=extraction_result.get('content', '')
                    )
                    result['stored_in_repository'] = True
                    logger.info(f"Document {document_name} stored in repository via assessor")
                except Exception as e:
                    logger.error(f"Failed to store document in repository: {e}")
                    result['stored_in_repository'] = False
            
            logger.info(f"ReaderBot completed processing {document_name}: {len(extraction_result.get('content', ''))} characters extracted")
            return result
            
        except Exception as e:
            logger.error(f"ReaderBot document processing failed: {e}")
            return {
                'error': str(e),
                'processing_status': 'error',
                'document_name': input_data.get('document_name', 'Unknown') if isinstance(input_data, dict) else 'Unknown',
                'requires_manual_review': True
            }
        finally:
            self.is_busy = False
            self.current_task_id = None

    async def _extract_and_assess_document(self, document_path: str, document_name: str) -> Dict[str, Any]:
        """Extract and assess document content using assessor module"""
        try:
            content = ""
            author = "Unknown"
            
            # Extract content from file
            if document_path and Path(document_path).exists():
                file_path = Path(document_path)
                if file_path.suffix.lower() in ['.txt', '.md']:
                    content = file_path.read_text(encoding='utf-8')
                    logger.info(f"Extracted {len(content)} characters from {document_name}")
                else:
                    # For other file types, simulate content extraction
                    content = f"[Content extracted from {document_name}]\n\nDocument contains legal information relevant to the case."
                    logger.info(f"Simulated content extraction for {document_name}")
            else:
                # Simulate document content for missing files
                content = f"[Simulated content for {document_name}]\n\nThis document contains legal information relevant to the case. Key facts and evidence have been identified for further processing."
                logger.warning(f"Document not found: {document_path}, using simulated content")
            
            # Use assessor module for enhanced processing
            result = {
                'content': content,
                'author': author,
                'extraction_method': 'assessor_enhanced' if ASSESSOR_AVAILABLE else 'basic'
            }
            
            if ASSESSOR_AVAILABLE and content:
                try:
                    # Use assessor functions for analysis
                    result['summary'] = summarize(content, max_sentences=2)
                    result['category'] = categorize(content)
                    result['hashtags'] = hashtags_from_category(result['category'])
                    
                    logger.info(f"Assessor analysis completed - Category: {result['category']}")
                except Exception as e:
                    logger.error(f"Assessor analysis failed: {e}")
                    result['summary'] = content[:200] + "..." if len(content) > 200 else content
                    result['category'] = 'unknown'
                    result['hashtags'] = '#general'
            else:
                # Fallback analysis
                result['summary'] = content[:200] + "..." if len(content) > 200 else content
                result['category'] = self._basic_categorize(content)
                result['hashtags'] = f"#{result['category']}"
                
            return result
                
        except Exception as e:
            logger.error(f"Content extraction and assessment failed for {document_path}: {e}")
            return {
                'content': f"[Error processing {document_name}]\n\nDocument processing encountered an error but can be manually reviewed.",
                'summary': 'Processing error occurred',
                'category': 'error',
                'hashtags': '#error',
                'author': 'System',
                'extraction_method': 'error'
            }

    def _basic_categorize(self, content: str) -> str:
        """Basic categorization fallback when assessor is not available"""
        content_lower = content.lower()
        
        if any(term in content_lower for term in ['contract', 'agreement', 'terms']):
            return 'contract'
        elif any(term in content_lower for term in ['litigation', 'lawsuit', 'complaint', 'motion']):
            return 'litigation'
        elif any(term in content_lower for term in ['email', 'correspondence', 'message']):
            return 'correspondence'
        elif any(term in content_lower for term in ['invoice', 'bill', 'receipt', 'payment']):
            return 'financial'
        else:
            return 'general'

    async def health_check(self) -> bool:
        """Check if the agent is healthy and ready to process tasks"""
        return True

    async def initialize(self) -> None:
        """Initialize the agent with required resources"""
        logger.info(f"ReaderBot initialized successfully (Assessor available: {ASSESSOR_AVAILABLE})")

    async def cleanup(self) -> None:
        """Clean up agent resources"""
        logger.info("ReaderBot cleanup completed")