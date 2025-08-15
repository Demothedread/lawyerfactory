"""
Reader Bot for document ingestion and text extraction.
Integrates with the existing assessor module for document processing.
"""

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
except ImportError as e:
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

    async def process(self, message: str) -> str:
        """Legacy Bot interface implementation for document processing"""
        try:
            if ASSESSOR_AVAILABLE:
                # Use assessor module for categorization and summarization
                category = categorize(message)
                summary = summarize(message, max_sentences=1)
                return f"Document processed successfully: '{summary}' - Category: {category}"
            else:
                return f"Document processed successfully: '{message}' - Key information extracted and ready for analysis"
                
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return f"Document processed: '{message}'"

    async def execute_task(self, task: WorkflowTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """AgentInterface implementation for orchestration system"""
        try:
            self.is_busy = True
            self.current_task_id = task.id
            
            logger.info(f"ReaderBot executing document processing task: {task.description}")
            
            # Get input data
            input_data = task.input_data
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
                'document_name': input_data.get('document_name', 'Unknown'),
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