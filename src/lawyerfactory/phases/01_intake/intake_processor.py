"""
Enhanced Intake Processor for LawyerFactory
Integrates advanced document categorization with intake form data.
Creates defendant-specific clusters and manages document workflow.
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .enhanced_document_categorizer import (
    DocumentMetadata,
    DocumentType,
    EnhancedDocumentCategorizer,
)
from .assessor_consolidated import (
    simple_categorize,
)  # kept for compatibility; may be used elsewhere
from .legal_intake_form import IntakeFormData, LegalIntakeForm
from .vector_cluster_manager import VectorClusterManager

# Evidence pipeline is optional; guard the import
try:
    from ...vectors.evidence_ingestion import EvidenceIngestionPipeline  # type: ignore
except Exception:
    EvidenceIngestionPipeline = None  # type: ignore

logger = logging.getLogger(__name__)


class EnhancedIntakeProcessor:
    """
    Enhanced intake processor that integrates document categorization
    with intake form data to create defendant-specific clusters.
    """

    def __init__(self, knowledge_graph=None, storage_path: str = "vector_clusters"):
        self.kg = knowledge_graph
        self.storage_path = Path(storage_path)

        # Initialize core components (single initialization; removed duplicates)
        self.categorizer = EnhancedDocumentCategorizer(knowledge_graph)
        self.cluster_manager = VectorClusterManager(storage_path)
        self.intake_form = LegalIntakeForm()
        self.evidence_pipeline = (
            EvidenceIngestionPipeline() if EvidenceIngestionPipeline else None
        )

        # Track active cases and their defendant clusters
        self.active_cases: Dict[str, Dict[str, Any]] = {}

        # Initialize from existing intake form data
        self._initialize_from_existing_data()

    def _initialize_from_existing_data(self):
        """Initialize processor with existing intake form data"""
        try:
            # Look for existing intake data files
            intake_files = list(Path(".").glob("*intake*.json"))
            for intake_file in intake_files:
                try:
                    with open(intake_file, "r") as f:
                        intake_data = json.load(f)
                    if (
                        isinstance(intake_data, dict)
                        and "defendant_name" in intake_data
                    ):
                        defendant_name = intake_data["defendant_name"]
                        cluster_id = self.cluster_manager.create_defendant_cluster(
                            defendant_name
                        )
                        logger.info(
                            f"Initialized cluster {cluster_id} from existing data"
                        )
                except Exception as e:
                    logger.warning(f"Failed to load intake file {intake_file}: {e}")
        except Exception as e:
            logger.warning(f"Failed to initialize from existing data: {e}")

    async def process_intake_form(self, form_data: IntakeFormData) -> Dict[str, Any]:
        """
        Process intake form data and set up defendant-specific clusters

        Args:
            form_data: Completed intake form data

        Returns:
            Processing results with cluster information
        """
        try:
            logger.info(
                f"Processing intake form for case: {form_data.claim_description[:50]}..."
            )

            # Extract defendant information
            defendant_name = self._extract_defendant_from_form(form_data)
            case_id = self._generate_case_id(form_data)

            # Create defendant-specific cluster
            cluster_id = self.cluster_manager.create_defendant_cluster(defendant_name)

            # Resolve validation threshold safely
            default_threshold = 0.75
            try:
                threshold = self.cluster_manager.validation_thresholds.get(
                    DocumentType.PLAINTIFF_COMPLAINT, default_threshold
                )
            except Exception:
                threshold = default_threshold

            # Store case information
            case_info = {
                "case_id": case_id,
                "defendant_name": defendant_name,
                "plaintiff_name": form_data.user_name,
                "cluster_id": cluster_id,
                "intake_data": form_data.to_dict(),
                "created_at": datetime.now().isoformat(),
                "document_count": 0,
                "validation_threshold": threshold,
            }

            self.active_cases[case_id] = case_info

            # Ingest intake form data into vector stores (if pipeline available)
            if self.evidence_pipeline:
                try:
                    vector_result = await self.evidence_pipeline.process_intake_form(
                        form_data.to_dict()
                    )
                    if vector_result.get("success"):
                        case_info["vector_document_id"] = vector_result.get(
                            "document_id"
                        )
                        logger.info(
                            f"Intake form ingested into vector stores: {vector_result.get('document_id')}"
                        )
                except Exception as e:
                    logger.warning(f"Evidence pipeline unavailable or failed: {e}")

            # Save case information
            await self._save_case_info(case_info)

            logger.info(
                f"Created case {case_id} with cluster {cluster_id} for defendant {defendant_name}"
            )

            return {
                "success": True,
                "case_id": case_id,
                "cluster_id": cluster_id,
                "defendant_name": defendant_name,
                "validation_threshold": case_info["validation_threshold"],
                "message": f"Case setup complete. Ready to process {defendant_name} documents.",
            }

        except Exception as e:
            logger.error(f"Intake form processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process intake form",
            }

    def _extract_defendant_from_form(self, form_data: IntakeFormData) -> str:
        """Extract defendant name from intake form data"""
        defendant_sources = [form_data.other_party_name, form_data.venue]
        for defendant in defendant_sources:
            if defendant and defendant.strip():
                # Clean up common prefixes/suffixes
                clean_name = defendant.strip()
                clean_name = clean_name.replace("Inc.", "").replace("Corp.", "")
                clean_name = clean_name.replace("Company", "").replace(
                    "Corporation", ""
                )
                clean_name = clean_name.replace("LLC", "").replace("Ltd.", "")
                clean_name = " ".join(clean_name.split())  # Normalize whitespace

                if len(clean_name) > 2:  # Must be at least 3 characters
                    return clean_name.title()

        # Fallback to generic name based on case type
        if form_data.case_type:
            return f"{form_data.case_type.title()} Defendant"
        return "Unknown Defendant"

    def _generate_case_id(self, form_data: IntakeFormData) -> str:
        """Generate unique case ID from form data"""
        import hashlib

        # Create hash from key form elements
        key_data = f"{form_data.user_name}_{form_data.other_party_name}_{form_data.claim_description[:50]}"
        case_hash = hashlib.md5(key_data.encode()).hexdigest()[:8]

        # Add timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"case_{timestamp}_{case_hash}"

    async def process_document(
        self,
        file_path: str,
        case_id: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a document and add it to the appropriate cluster

        Args:
            file_path: Path to the document file
            case_id: Associated case ID
            additional_context: Additional processing context

        Returns:
            Processing results
        """
        try:
            if case_id not in self.active_cases:
                return {"success": False, "error": f"Case {case_id} not found"}

            case_info = self.active_cases[case_id]
            defendant_name = case_info["defendant_name"]

            # Read document content
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if not content.strip():
                return {"success": False, "error": "Document is empty or unreadable"}

            # Categorize document with defendant context
            document = self.categorizer.categorize_document(
                text=content,
                filename=Path(file_path).name,
                defendant_hint=defendant_name,
            )

            # Add to vector cluster
            success = await self.cluster_manager.add_document(
                document=document,
                text_content=content,
                cluster_id=case_info["cluster_id"],
            )

            if success:
                # Update case statistics
                case_info["document_count"] += 1
                await self._save_case_info(case_info)

                # Find similar documents
                similar_docs = await self.cluster_manager.find_similar_documents(
                    query_document=document, query_text=content, top_k=5
                )

                return {
                    "success": True,
                    "document_id": document.document_id,
                    "document_type": document.document_type.value,
                    "authority_level": document.authority_level.value,
                    "cluster_id": document.cluster_id,
                    "confidence_score": document.confidence_score,
                    "similar_documents": len(similar_docs),
                    "defendant_recognized": document.defendant_name == defendant_name,
                    "message": f"Document processed and added to {defendant_name} cluster",
                }
            else:
                return {"success": False, "error": "Failed to add document to cluster"}

        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return {"success": False, "error": str(e)}

    async def validate_draft_complaint(
        self,
        draft_text: str,
        case_id: str,
        similarity_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Validate a draft complaint against the defendant's cluster

        Args:
            draft_text: Text of the draft complaint
            case_id: Associated case ID
            similarity_threshold: Custom similarity threshold

        Returns:
            Validation results
        """
        try:
            if case_id not in self.active_cases:
                return {"valid": False, "reason": f"Case {case_id} not found"}

            case_info = self.active_cases[case_id]
            defendant_name = case_info["defendant_name"]

            # Use provided threshold or case default
            threshold = similarity_threshold or case_info["validation_threshold"]

            # Validate against cluster
            validation_result = (
                await self.cluster_manager.validate_draft_against_cluster(
                    draft_text=draft_text,
                    defendant_name=defendant_name,
                    similarity_threshold=threshold,
                )
            )

            # Add case context to results
            validation_result["case_id"] = case_id
            validation_result["defendant_name"] = defendant_name
            validation_result["cluster_size"] = case_info["document_count"]

            return validation_result

        except Exception as e:
            logger.error(f"Draft validation failed: {e}")
            return {"valid": False, "reason": f"Validation error: {str(e)}"}

    async def get_case_analysis(self, case_id: str) -> Dict[str, Any]:
        """Get comprehensive analysis for a case"""
        try:
            if case_id not in self.active_cases:
                return {"error": f"Case {case_id} not found"}

            case_info = self.active_cases[case_id]

            # Get cluster analysis
            cluster_analysis = await self.cluster_manager.get_cluster_analysis(
                case_info["cluster_id"]
            )

            return {
                "case_id": case_id,
                "case_info": case_info,
                "cluster_analysis": cluster_analysis,
                "analysis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Case analysis failed: {e}")
            return {"error": str(e)}

    async def _save_case_info(self, case_info: Dict[str, Any]):
        """Save case information to persistent storage"""
        try:
            case_file = self.storage_path / "cases" / f"{case_info['case_id']}.json"
            case_file.parent.mkdir(parents=True, exist_ok=True)

            with open(case_file, "w", encoding="utf-8") as f:
                json.dump(case_info, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to save case info: {e}")

    async def load_case(self, case_id: str) -> bool:
        """Load case information from storage"""
        try:
            case_file = self.storage_path / "cases" / f"{case_id}.json"

            if not case_file.exists():
                return False

            with open(case_file, "r", encoding="utf-8") as f:
                case_info = json.load(f)

            self.active_cases[case_id] = case_info

            # Load associated cluster
            if "cluster_id" in case_info:
                await self.cluster_manager.load_cluster(case_info["cluster_id"])

            return True

        except Exception as e:
            logger.error(f"Failed to load case {case_id}: {e}")
            return False

    def get_active_cases(self) -> List[Dict[str, Any]]:
        """Get list of all active cases"""
        return list(self.active_cases.values())

    def get_defendant_clusters(self) -> List[str]:
        """Get list of all defendant-specific clusters"""
        return [
            cluster_id
            for cluster_id in self.cluster_manager.clusters.keys()
            if "complaints" in cluster_id and cluster_id != "plaintiff_complaints"
        ]

    async def cleanup_case(self, case_id: str) -> bool:
        """Clean up case data and associated clusters"""
        try:
            if case_id in self.active_cases:
                del self.active_cases[case_id]

            # Remove case file
            case_file = self.storage_path / "cases" / f"{case_id}.json"
            if case_file.exists():
                case_file.unlink()

            return True

        except Exception as e:
            logger.error(f"Failed to cleanup case {case_id}: {e}")
            return False

    async def ingest_evidence_for_case(
        self, case_id: str, file_paths: List[str], extract_binaries: bool = True
    ) -> Dict[str, Any]:
        """
        Helper to ingest multiple evidence files for a case.

        - Extracts text from each provided file (lightweight PDF/DOCX support).
        - Keeps only the first and last ~300 lines to limit indexing size.
        - Categorizes using the EnhancedDocumentCategorizer and adds documents to the defendant cluster.
        - Updates and persists case metadata.

        Args:
            case_id: Case identifier previously created by process_intake_form
            file_paths: List of file system paths to evidence files
            extract_binaries: If True, attempt to extract text from PDFs/DOCX; otherwise only read text files

        Returns:
            Summary dict with counts and per-file details
        """
        results = {
            "success": False,
            "case_id": case_id,
            "processed": 0,
            "added": 0,
            "failed": 0,
            "details": [],
        }

        if case_id not in self.active_cases:
            results["details"].append({"error": f"Case {case_id} not found"})
            return results

        case_info = self.active_cases[case_id]
        cluster_id = case_info.get("cluster_id")
        defendant_name = case_info.get("defendant_name")

        for p in file_paths:
            path = Path(p)
            detail = {"path": str(path), "status": "skipped"}

            if not path.exists():
                detail["status"] = "missing"
                results["failed"] += 1
                results["details"].append(detail)
                continue

            # Attempt to extract text
            text = ""
            suffix = path.suffix.lower()
            try:
                if suffix in (".txt", ".md"):
                    text = path.read_text(encoding="utf-8", errors="replace")
                elif extract_binaries and suffix == ".pdf":
                    try:
                        import PyPDF2

                        with open(path, "rb") as fh:
                            reader = PyPDF2.PdfReader(fh)
                            text = "\n".join(
                                (page.extract_text() or "") for page in reader.pages
                            )
                    except Exception:
                        # fallback: try binary decode
                        raw = path.read_bytes()
                        try:
                            text = raw.decode("utf-8", errors="replace")
                        except Exception:
                            text = ""
                elif extract_binaries and suffix == ".docx":
                    try:
                        import docx

                        doc = docx.Document(str(path))
                        text = "\n".join(par.text for par in doc.paragraphs)
                    except Exception:
                        text = ""
                else:
                    # try a permissive read for other file types
                    try:
                        raw = path.read_bytes()
                        text = raw.decode("utf-8", errors="replace")
                    except Exception:
                        text = ""
            except Exception as e:
                logger.warning(f"Failed to extract text from {path}: {e}")
                text = ""

            if not text or not text.strip():
                detail["status"] = "unreadable"
                results["failed"] += 1
                results["details"].append(detail)
                continue

            # Limit to first+last 300/400 segments based on file size
            lines = [ln for ln in text.splitlines()]
            n_lines = len(lines)

            def build_combined_from_ranges(ranges):
                """Assemble lines from a list of (start, end) ranges, preserving order and avoiding duplicates."""
                seen = set()
                out = []
                for start, end in ranges:
                    # clamp bounds
                    s = max(0, int(start))
                    e = min(n_lines, int(end))
                    for i in range(s, e):
                        if i not in seen:
                            out.append(lines[i])
                            seen.add(i)
                return "\n".join(out)

            if n_lines < 300:
                # fewer than 300 lines -> take all available
                combined = "\n".join(lines)
            elif n_lines < 1200:
                # fewer than 1200 lines -> first 300 + last 300
                ranges = [(0, 300), (max(0, n_lines - 300), n_lines)]
                combined = build_combined_from_ranges(ranges)
            else:
                # n_lines >= 1200: try to take first/middle/last 400 for larger docs.
                first_count = 400
                last_count = 400
                mid_count = 400

                # compute middle window centered
                mid_start = max(0, (n_lines // 2) - (mid_count // 2))
                ranges = [
                    (0, min(first_count, n_lines)),  # first segment
                    (mid_start, min(mid_start + mid_count, n_lines)),  # middle segment
                    (max(0, n_lines - last_count), n_lines),  # last segment
                ]
                combined = build_combined_from_ranges(ranges)

            # Categorize using the EnhancedDocumentCategorizer
            try:
                docmeta = self.categorizer.categorize_document(
                    text=combined, filename=path.name, defendant_hint=defendant_name
                )
            except Exception as e:
                logger.exception(f"Categorization failed for {path}: {e}")
                detail.update({"status": "categorization_failed", "error": str(e)})
                results["failed"] += 1
                results["details"].append(detail)
                continue

            # Add to cluster
            try:
                success = await self.cluster_manager.add_document(
                    document=docmeta, text_content=combined, cluster_id=cluster_id
                )
            except Exception as e:
                logger.exception(f"Failed to add document to cluster for {path}: {e}")
                success = False

            results["processed"] += 1
            if success:
                results["added"] += 1
                case_info["document_count"] = case_info.get("document_count", 0) + 1

                # Safely resolve document_type value (handle None and missing .value)
                doc_type_attr = getattr(docmeta, "document_type", None)
                if doc_type_attr is None:
                    doc_type_value = ""
                else:
                    # If document_type is an Enum-like object use .value, otherwise stringify
                    raw_type = getattr(doc_type_attr, "value", doc_type_attr)
                    doc_type_value = "" if raw_type is None else str(raw_type)

                # Assign keys explicitly to avoid type-checker overload issues with dict.update(...)
                detail["status"] = "added"
                # Ensure document_id is a string for consistent typing
                doc_id_val = getattr(docmeta, "document_id", None)
                detail["document_id"] = "" if doc_id_val is None else str(doc_id_val)
                detail["document_type"] = doc_type_value
                # Ensure confidence is a string (type-checkers expecting Dict[str, str] require str)
                conf_val = getattr(docmeta, "confidence_score", None)
                detail["confidence"] = "" if conf_val is None else str(conf_val)
            else:
                results["failed"] += 1
                detail.update({"status": "add_failed"})

            results["details"].append(detail)

        # persist updated case info
        try:
            await self._save_case_info(case_info)
        except Exception:
            logger.warning(f"Failed to persist case info for {case_id} after ingest")

        results["success"] = True
        results["case_summary"] = {
            "document_count": case_info.get("document_count", 0),
            "cluster_id": cluster_id,
            "defendant_name": defendant_name,
            "details": results["details"],
        }

        return results
