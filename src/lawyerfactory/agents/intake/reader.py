"""
Reader Agent for LawyerFactory - Document intake and fact extraction
Canonical agent location following copilot-instructions.md structure
"""

import logging
from typing import Any, Dict, Optional

try:
    from ...compose.bots.reader import ReaderBot as ComposeReaderBot
except ImportError:
    ComposeReaderBot = None

from ...storage.enhanced_unified_storage_api import get_enhanced_unified_storage_api

logger = logging.getLogger(__name__)


class ReaderBot:
    """
    Document reader agent for intake and fact extraction.
    Processes client documents, extracts key facts and evidence.
    Integrates with unified storage system for comprehensive document management.

    Features:
    - Document intake and text extraction
    - Fact extraction and categorization
    - Integration with existing assessor module
    - Unified storage integration
    """

    def __init__(self, storage_api: Optional[Any] = None):
        self.storage_api = storage_api or get_enhanced_unified_storage_api()

        # Initialize with existing ReaderBot implementation
        if ComposeReaderBot:
            try:
                config = {
                    "assessor_llm": "gpt-4o-mini",
                    "reader_llm": "gpt-4o-mini",
                    "file_selector_llm": "gpt-4o-mini",
                    "agent_registry_file_path": "agent_registry.json",
                    "vector_store_path": "./vectorstore",
                    "openai_api_key": None,  # Will use environment
                    "anthropic_api_key": None,  # Will use environment
                    "max_context_window": 4000,
                    "chunk_size": 1000,
                    "chunk_overlap": 200,
                }

                self.compose_reader = ComposeReaderBot(config)
            except Exception as e:
                logger.warning(f"Failed to initialize compose reader: {e}")
                self.compose_reader = None
        else:
            self.compose_reader = None

        logger.info("ReaderBot agent initialized with unified storage integration")

    async def process_document(
        self, document_path: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a document through the intake pipeline

        Args:
            document_path: Path to the document to process
            metadata: Additional metadata for the document

        Returns:
            Processing results including extracted facts and categorization
        """
        try:
            if self.compose_reader:
                # Use existing compose reader implementation
                # Create a simple task dict instead of using WorkflowTask class
                task_data = {
                    "id": "document_intake",
                    "description": f"Process document: {document_path}",
                    "input_data": {"document_path": document_path, "metadata": metadata or {}},
                }

                # Call the compose reader's process method
                result = await self.compose_reader.process(str(task_data))

                # Parse result if it's a JSON string
                if isinstance(result, str):
                    try:
                        import json

                        result = json.loads(result)
                    except:
                        result = {"extracted_content": result, "processing_status": "completed"}

                # Store results through unified storage if successful
                if result.get("processing_status") == "completed":
                    content = result.get("extracted_content", "")

                    if content:
                        storage_result = await self.storage_api.store_evidence(
                            file_content=content.encode("utf-8"),
                            filename=result.get("document_name", "unknown_document.txt"),
                            metadata={
                                "extraction_method": result.get("extraction_method", "unknown"),
                                "category": result.get("category", "general"),
                                "summary": result.get("summary", ""),
                                "author": result.get("author", "Unknown"),
                                "content_length": result.get("content_length", 0),
                                **(metadata or {}),
                            },
                            source_phase="intake",
                        )

                        if storage_result.success:
                            result["storage_object_id"] = storage_result.object_id
                            result["unified_storage_integrated"] = True
                            logger.info(
                                f"Document stored with ObjectID: {storage_result.object_id}"
                            )

                return result
            else:
                # Fallback implementation
                return await self._fallback_document_processing(document_path, metadata)

        except Exception as e:
            logger.error(f"Failed to process document {document_path}: {e}")
            return {
                "error": str(e),
                "processing_status": "error",
                "document_path": document_path,
                "requires_manual_review": True,
            }

    async def extract_facts(self, content: str, document_name: str = "unknown") -> Dict[str, Any]:
        """
        Extract key facts from document content

        Args:
            content: Document content text
            document_name: Name of the source document

        Returns:
            Extracted facts and categorization
        """
        try:
            # Use compose reader for fact extraction if available
            if self.compose_reader:
                # Create a simple task dict for fact extraction
                task_data = {
                    "id": "fact_extraction",
                    "description": f"Extract facts from: {document_name}",
                    "input_data": {"content": content, "document_name": document_name},
                }

                result = await self.compose_reader.process(str(task_data))

                # Parse result if it's a JSON string
                if isinstance(result, str):
                    try:
                        import json

                        result = json.loads(result)
                    except:
                        result = {"extracted_facts": [result], "document_name": document_name}

                return result
            else:
                # Fallback fact extraction
                return self._fallback_fact_extraction(content, document_name)

        except Exception as e:
            logger.error(f"Failed to extract facts from {document_name}: {e}")
            return {"error": str(e), "document_name": document_name, "extracted_facts": []}

    async def categorize_document(self, content: str, filename: str) -> Dict[str, Any]:
        """
        Categorize document based on content analysis

        Args:
            content: Document content
            filename: Original filename

        Returns:
            Document categorization results
        """
        try:
            # Use existing categorization logic from compose reader
            if self.compose_reader and hasattr(self.compose_reader, "_basic_categorize"):
                category = self.compose_reader._basic_categorize(content)

                return {
                    "category": category,
                    "confidence": 0.8,  # Default confidence
                    "filename": filename,
                    "content_length": len(content),
                }
            else:
                # Fallback categorization
                return self._fallback_categorization(content, filename)

        except Exception as e:
            logger.error(f"Failed to categorize document {filename}: {e}")
            return {"error": str(e), "category": "unknown", "filename": filename}

    async def search_processed_documents(self, query: str) -> Dict[str, Any]:
        """
        Search through processed documents using unified storage

        Args:
            query: Search query

        Returns:
            Search results from processed documents
        """
        try:
            # Search through unified storage
            results = await self.storage_api.search_evidence(query, "all")

            # Filter for documents processed by this agent
            reader_results = []
            for result in results:
                metadata = result.get("metadata", {})
                if (
                    metadata.get("source_phase") == "intake"
                    or "reader" in metadata.get("created_by", "").lower()
                ):
                    reader_results.append(result)

            return {
                "query": query,
                "total_results": len(reader_results),
                "results": reader_results,
                "search_successful": True,
            }

        except Exception as e:
            logger.error(f"Failed to search processed documents: {e}")
            return {"error": str(e), "query": query, "search_successful": False}

    # Fallback implementations

    async def _fallback_document_processing(
        self, document_path: str, metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fallback document processing when compose reader is not available"""
        try:
            from pathlib import Path

            # Basic file reading
            file_path = Path(document_path)
            if not file_path.exists():
                return {
                    "error": "File not found",
                    "processing_status": "error",
                    "document_path": document_path,
                }

            # Read content based on file type
            if file_path.suffix.lower() in [".txt", ".md"]:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            else:
                content = f"[Binary file: {file_path.name}]"

            # Basic categorization
            category = self._fallback_categorization(content, file_path.name)["category"]

            # Store through unified storage
            storage_result = await self.storage_api.store_evidence(
                file_content=content.encode("utf-8"),
                filename=file_path.name,
                metadata={
                    "category": category,
                    "extraction_method": "fallback",
                    "content_length": len(content),
                    **(metadata or {}),
                },
                source_phase="intake",
            )

            result = {
                "document_name": file_path.name,
                "document_path": document_path,
                "extracted_content": content,
                "content_length": len(content),
                "category": category,
                "processing_status": "completed",
                "extraction_method": "fallback",
            }

            if storage_result.success:
                result["storage_object_id"] = storage_result.object_id
                result["unified_storage_integrated"] = True

            return result

        except Exception as e:
            logger.error(f"Fallback processing failed for {document_path}: {e}")
            return {"error": str(e), "processing_status": "error", "document_path": document_path}

    def _fallback_fact_extraction(self, content: str, document_name: str) -> Dict[str, Any]:
        """Fallback fact extraction implementation"""
        try:
            # Simple sentence-based fact extraction
            sentences = [s.strip() for s in content.split(".") if s.strip() and len(s.strip()) > 20]

            # Take first few sentences as potential facts
            facts = []
            for sentence in sentences[:5]:
                if any(
                    indicator in sentence.lower()
                    for indicator in [
                        "states",
                        "indicates",
                        "shows",
                        "demonstrates",
                        "according to",
                    ]
                ):
                    facts.append(sentence.strip())

            return {
                "document_name": document_name,
                "extracted_facts": facts,
                "fact_count": len(facts),
                "extraction_method": "fallback",
                "content_length": len(content),
            }

        except Exception as e:
            logger.error(f"Fallback fact extraction failed: {e}")
            return {"error": str(e), "document_name": document_name, "extracted_facts": []}

    def _fallback_categorization(self, content: str, filename: str) -> Dict[str, Any]:
        """Fallback categorization implementation"""
        content_lower = content.lower()
        filename_lower = filename.lower()

        if any(term in content_lower for term in ["contract", "agreement", "terms"]):
            category = "contract"
        elif any(term in content_lower for term in ["lawsuit", "complaint", "litigation"]):
            category = "litigation"
        elif any(term in content_lower for term in ["email", "correspondence", "message"]):
            category = "correspondence"
        elif any(term in content_lower for term in ["invoice", "bill", "receipt"]):
            category = "financial"
        else:
            category = "general"

        return {
            "category": category,
            "confidence": 0.6,  # Lower confidence for fallback
            "filename": filename,
            "method": "fallback",
        }
