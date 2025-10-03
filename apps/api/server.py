"""
LawyerFactory API Server with proper Flask-SocketIO configuration
Handles real-time communication for the legal document automation system
"""

import eventlet

# Monkey patch must be first for eventlet
eventlet.monkey_patch()

import os
from pathlib import Path
import sys

# Add src to path for lawyerfactory imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import argparse
import logging

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

"""
LawyerFactory API Server
Flask-based REST API with Socket.IO for real-time communication
"""

import asyncio
import json
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = "lawyerfactory-secret-key"
CORS(app, origins=["*"])

# Create Socket.IO server with eventlet for async support
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# Import LawyerFactory components (optional)
LAWYERFACTORY_AVAILABLE = False
try:
    # Add src to path for imports
    src_path = Path(__file__).parent.parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    # Import with fallbacks for missing dependencies
    try:
        from lawyerfactory.agents.research.court_authority_helper import (
            CourtAuthorityHelper,
            JurisdictionContext,
            LegalQuestionType,
        )

        COURT_AUTHORITY_AVAILABLE = True
    except ImportError:
        CourtAuthorityHelper = None
        COURT_AUTHORITY_AVAILABLE = False
        logger.warning("CourtAuthorityHelper not available")

    try:
        from lawyerfactory.agents.research.research import ResearchBot

        RESEARCH_BOT_AVAILABLE = True
    except ImportError:
        ResearchBot = None
        RESEARCH_BOT_AVAILABLE = False
        logger.warning("ResearchBot not available")

    try:
        from lawyerfactory.evidence.table import EnhancedEvidenceTable

        EVIDENCE_TABLE_AVAILABLE = True
    except ImportError:
        EnhancedEvidenceTable = None
        EVIDENCE_TABLE_AVAILABLE = False
        logger.warning("EnhancedEvidenceTable not available")

    try:
        from lawyerfactory.phases.phaseA01_intake.enhanced_document_categorizer import (
            DocumentMetadata,
            DocumentType,
            EnhancedDocumentCategorizer,
        )

        DOCUMENT_CATEGORIZER_AVAILABLE = True
    except ImportError:
        EnhancedDocumentCategorizer = None
        DOCUMENT_CATEGORIZER_AVAILABLE = False
        logger.warning("EnhancedDocumentCategorizer not available")

    try:
        from lawyerfactory.phases.phaseA01_intake.intake_processor import EnhancedIntakeProcessor

        INTAKE_PROCESSOR_AVAILABLE = True
    except ImportError:
        EnhancedIntakeProcessor = None
        INTAKE_PROCESSOR_AVAILABLE = False
        logger.warning("EnhancedIntakeProcessor not available")

    try:
        from lawyerfactory.outline.enhanced_generator import EnhancedSkeletalOutlineGenerator

        OUTLINE_GENERATOR_AVAILABLE = True
    except ImportError:
        EnhancedSkeletalOutlineGenerator = None
        OUTLINE_GENERATOR_AVAILABLE = False
        logger.warning("EnhancedSkeletalOutlineGenerator not available")

    try:
        from lawyerfactory.claims.matrix import ComprehensiveClaimsMatrixIntegration

        CLAIMS_MATRIX_AVAILABLE = True
    except ImportError:
        ComprehensiveClaimsMatrixIntegration = None
        CLAIMS_MATRIX_AVAILABLE = False
        logger.warning("ComprehensiveClaimsMatrixIntegration not available")

    try:
        from lawyerfactory.storage.enhanced_unified_storage_api import (
            get_enhanced_unified_storage_api,
        )

        UNIFIED_STORAGE_AVAILABLE = True
    except ImportError:
        get_enhanced_unified_storage_api = None
        UNIFIED_STORAGE_AVAILABLE = False
        logger.warning("EnhancedUnifiedStorageAPI not available")

    LAWYERFACTORY_AVAILABLE = True
    logger.info("LawyerFactory components imported successfully")
except ImportError as e:
    logger.warning(f"LawyerFactory components not available: {e}")
    LAWYERFACTORY_AVAILABLE = False

# Global instances
research_bot = None
court_authority_helper = None
evidence_table = None
intake_processor = None
outline_generator = None
claims_matrix = None
unified_storage = None


def initialize_components():
    """Initialize LawyerFactory components"""
    global research_bot, court_authority_helper, evidence_table
    global intake_processor, outline_generator, claims_matrix, unified_storage

    if not LAWYERFACTORY_AVAILABLE:
        return

    try:
        # Initialize unified storage first (required by other components)
        if UNIFIED_STORAGE_AVAILABLE and get_enhanced_unified_storage_api:
            unified_storage = get_enhanced_unified_storage_api()
            logger.info("Unified storage initialized")
        else:
            unified_storage = None
            logger.warning("Unified storage not available")

        # Initialize research components
        if RESEARCH_BOT_AVAILABLE and ResearchBot:
            try:
                research_bot = ResearchBot(knowledge_graph=None)
                logger.info("Research bot initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize research bot: {e}")
                research_bot = None
        else:
            research_bot = None

        if COURT_AUTHORITY_AVAILABLE and CourtAuthorityHelper:
            try:
                court_authority_helper = CourtAuthorityHelper()
                logger.info("Court authority helper initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize court authority helper: {e}")
                court_authority_helper = None
        else:
            court_authority_helper = None

        # Initialize evidence table
        if EVIDENCE_TABLE_AVAILABLE and EnhancedEvidenceTable:
            try:
                evidence_table = EnhancedEvidenceTable()
                logger.info("Evidence table initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize evidence table: {e}")
                evidence_table = None
        else:
            evidence_table = None

        # Initialize intake processor
        if INTAKE_PROCESSOR_AVAILABLE and EnhancedIntakeProcessor:
            try:
                intake_processor = EnhancedIntakeProcessor()
                logger.info("Intake processor initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize intake processor: {e}")
                intake_processor = None
        else:
            intake_processor = None

        # Import outline generator dependencies (only once)
        try:
            from lawyerfactory.kg.enhanced_graph import EnhancedKnowledgeGraph
            from lawyerfactory.phases.phaseA01_intake.evidence_routes import EvidenceAPI

            # Initialize outline generator with proper dependencies
            if (
                OUTLINE_GENERATOR_AVAILABLE
                and EnhancedSkeletalOutlineGenerator
                and CLAIMS_MATRIX_AVAILABLE
                and ComprehensiveClaimsMatrixIntegration
            ):
                try:
                    kg = EnhancedKnowledgeGraph()
                    evidence_api = EvidenceAPI()

                    # Initialize claims matrix with unified storage if available
                    if unified_storage:
                        claims_matrix = ComprehensiveClaimsMatrixIntegration(unified_storage)
                    else:
                        claims_matrix = ComprehensiveClaimsMatrixIntegration(kg)

                    outline_generator = EnhancedSkeletalOutlineGenerator(
                        kg, claims_matrix, evidence_api
                    )
                    logger.info("Outline generator and claims matrix initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize outline generator: {e}")
                    outline_generator = None
                    claims_matrix = None
            else:
                outline_generator = None
                claims_matrix = None

        except ImportError as e:
            logger.warning(f"Failed to import outline generator dependencies: {e}")
            outline_generator = None
            claims_matrix = None

        logger.info("Component initialization completed")

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        # Set all components to None on initialization failure
        research_bot = None
        court_authority_helper = None
        evidence_table = None
        intake_processor = None
        outline_generator = None
        claims_matrix = None
        unified_storage = None


# Initialize components on startup
initialize_components()


# Socket.IO event handlers
@socketio.on("connect")
def handle_connect():
    logger.info("Client connected")
    emit("status", {"message": "Connected to LawyerFactory API"})


@socketio.on("disconnect")
def handle_disconnect():
    logger.info("Client disconnected")


# API Routes


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "lawyerfactory_available": LAWYERFACTORY_AVAILABLE,
            "components": {
                "research_bot": research_bot is not None,
                "court_authority_helper": court_authority_helper is not None,
                "evidence_table": evidence_table is not None,
                "intake_processor": intake_processor is not None,
                "outline_generator": outline_generator is not None,
                "claims_matrix": claims_matrix is not None,
            },
        }
    )


@app.route("/api/intake", methods=["POST"])
def process_intake():
    """Process legal intake form and create case"""
    if not LAWYERFACTORY_AVAILABLE or not intake_processor:
        return jsonify({"error": "Intake processor not available"}), 503

    try:
        data = request.get_json()

        # Process intake data
        intake_result = intake_processor.process_intake_form(data)

        # Create case in storage
        case_id = f"case_{int(time.time())}"

        # Emit progress update
        socketio.emit(
            "phase_progress_update",
            {
                "phase": "A01_Intake",
                "progress": 100,
                "message": f"Case {case_id} created successfully",
            },
        )

        return jsonify({"success": True, "case": intake_result, "case_id": case_id})

    except Exception as e:
        logger.error(f"Intake processing failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/cases/<case_id>/documents", methods=["POST"])
def upload_case_documents(case_id):
    """Upload documents for a specific case"""
    if not LAWYERFACTORY_AVAILABLE or not intake_processor:
        return jsonify({"error": "Document processor not available"}), 503

    try:
        files = request.files.getlist("files")

        # Process documents
        processed_docs = []
        for file in files:
            # Save file temporarily
            temp_path = f"/tmp/{file.filename}"
            file.save(temp_path)

            # Process document
            doc_result = intake_processor.process_document(temp_path, case_id)
            processed_docs.append(doc_result)

            # Clean up temp file
            os.remove(temp_path)

        # Emit progress update
        socketio.emit(
            "phase_progress_update",
            {
                "phase": "A01_Intake",
                "progress": 75,
                "message": f"Processed {len(processed_docs)} documents for case {case_id}",
            },
        )

        return jsonify(
            {"success": True, "uploaded_files": processed_docs, "total": len(processed_docs)}
        )

    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        return jsonify({"error": str(e)}), 500


# Global storage for workflow states (temporary - in production use database)
research_status_store = {}
research_results_store = {}
outline_status_store = {}
outline_results_store = {}


@app.route("/api/research/start", methods=["POST"])
def start_research():
    """Start research for a case"""
    if not LAWYERFACTORY_AVAILABLE or not research_bot:
        return jsonify({"error": "Research bot not available"}), 503

    try:
        data = request.get_json()
        case_id = data.get("case_id")
        research_query = data.get("query", "")

        if not case_id:
            return jsonify({"error": "Case ID required"}), 400

        # Start research asynchronously
        socketio.start_background_task(run_research, case_id, research_query)

        return jsonify({"success": True, "message": "Research started", "case_id": case_id})

    except Exception as e:
        logger.error(f"Research start failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/research/status/<case_id>", methods=["GET"])
def get_research_status(case_id):
    """Get research status for a case"""
    if not LAWYERFACTORY_AVAILABLE or not research_bot:
        return jsonify({"error": "Research bot not available"}), 503

    try:
        # Get research status from temporary store
        status = research_status_store.get(
            case_id, {"status": "not_started", "progress": 0, "message": "Research not yet started"}
        )

        return jsonify(
            {
                "case_id": case_id,
                "status": status.get("status", "unknown"),
                "progress": status.get("progress", 0),
                "message": status.get("message", ""),
            }
        )

    except Exception as e:
        logger.error(f"Research status check failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/research/results/<case_id>", methods=["GET"])
def get_research_results(case_id):
    """Get research results for a case"""
    if not LAWYERFACTORY_AVAILABLE or not research_bot:
        return jsonify({"error": "Research bot not available"}), 503

    try:
        # Get research results from temporary store
        results = research_results_store.get(
            case_id,
            {
                "sources": [],
                "legal_principles": [],
                "gaps": [],
                "recommendations": [],
                "confidence_score": 0.0,
            },
        )

        return jsonify(
            {
                "case_id": case_id,
                "results": results,
                "total_sources": len(results.get("sources", [])),
            }
        )

    except Exception as e:
        logger.error(f"Research results retrieval failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/outline/generate", methods=["POST"])
def generate_outline():
    """Generate document outline for a case"""
    if not LAWYERFACTORY_AVAILABLE or not outline_generator:
        return jsonify({"error": "Outline generator not available"}), 503

    try:
        data = request.get_json()
        case_id = data.get("case_id")

        if not case_id:
            return jsonify({"error": "Case ID required"}), 400

        # Generate outline asynchronously
        socketio.start_background_task(run_outline_generation, case_id)

        return jsonify(
            {"success": True, "message": "Outline generation started", "case_id": case_id}
        )

    except Exception as e:
        logger.error(f"Outline generation start failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/outline/status/<case_id>", methods=["GET"])
def get_outline_status(case_id):
    """Get outline generation status for a case"""
    if not LAWYERFACTORY_AVAILABLE or not outline_generator:
        return jsonify({"error": "Outline generator not available"}), 503

    try:
        # Get outline status from temporary store
        status = outline_status_store.get(
            case_id,
            {
                "status": "not_started",
                "progress": 0,
                "message": "Outline generation not yet started",
            },
        )

        return jsonify(
            {
                "case_id": case_id,
                "status": status.get("status", "unknown"),
                "progress": status.get("progress", 0),
                "message": status.get("message", ""),
            }
        )

    except Exception as e:
        logger.error(f"Outline status check failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/storage/documents", methods=["POST"])
def upload_documents_unified():
    """Upload documents using unified storage API"""
    if not unified_storage:
        return jsonify({"error": "Unified storage not available"}), 503

    try:
        files = request.files.getlist("files")
        case_id = request.form.get("case_id", "default")
        phase = request.form.get("phase", "phaseA01_intake")

        if not files:
            return jsonify({"error": "No files provided"}), 400

        results = []

        for file in files:
            if file.filename == "":
                continue

            # Read file content
            file_content = file.read()

            # Create metadata for evidence storage
            metadata = {
                "case_id": case_id,
                "filename": file.filename,
                "content_type": file.content_type or "application/octet-stream",
                "uploaded_at": time.time(),
                "phase": phase,
                "source": "frontend_upload",
            }

            # Store using unified storage API
            result = unified_storage.store_evidence(
                file_content=file_content,
                filename=file.filename,
                metadata=metadata,
                source_phase=phase,
            )

            if result.success:
                results.append(
                    {
                        "filename": file.filename,
                        "object_id": result.object_id,
                        "evidence_id": result.evidence_id,
                        "s3_url": result.s3_url,
                        "size": len(file_content),
                        "processing_time": result.processing_time,
                    }
                )
            else:
                logger.error(f"Failed to store {file.filename}: {result.error}")
                return jsonify({"error": f"Failed to store {file.filename}: {result.error}"}), 500

        # Emit progress update
        socketio.emit(
            "phase_progress_update",
            {
                "phase": phase,
                "progress": 100,
                "message": f"Stored {len(results)} documents in unified storage",
                "case_id": case_id,
                "object_ids": [r["object_id"] for r in results],
            },
        )

        logger.info(
            f"Successfully stored {len(results)} documents via unified storage for case {case_id}"
        )

        return jsonify(
            {
                "success": True,
                "case_id": case_id,
                "stored_documents": results,
                "total": len(results),
                "message": f"Successfully stored {len(results)} documents",
            }
        )

    except Exception as e:
        logger.error(f"Unified document storage failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/storage/documents/<object_id>", methods=["GET"])
def get_document_by_object_id(object_id):
    """Retrieve document from unified storage by ObjectID"""
    if not unified_storage:
        return jsonify({"error": "Unified storage not available"}), 503

    try:
        # Retrieve document using unified storage API
        document_data = unified_storage.retrieve_evidence_by_id(object_id)

        if document_data:
            return jsonify(
                {
                    "success": True,
                    "object_id": object_id,
                    "document": document_data,
                    "retrieved_at": time.time(),
                }
            )
        else:
            return jsonify({"error": "Document not found"}), 404

    except Exception as e:
        logger.error(f"Failed to retrieve document {object_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/storage/cases/<case_id>/documents", methods=["GET"])
def get_case_documents(case_id):
    """Retrieve all documents for a case from unified storage"""
    if not unified_storage:
        return jsonify({"error": "Unified storage not available"}), 503

    try:
        # Search for documents by case_id in metadata
        documents = unified_storage.search_evidence_by_metadata({"case_id": case_id})

        return jsonify(
            {
                "success": True,
                "case_id": case_id,
                "documents": documents,
                "total": len(documents),
                "retrieved_at": time.time(),
            }
        )

    except Exception as e:
        logger.error(f"Failed to retrieve documents for case {case_id}: {e}")
        return jsonify({"error": str(e)}), 500


# Background task functions
def run_research(case_id: str, research_query: str):
    """Run research in background"""
    try:
        # Update status to running
        research_status_store[case_id] = {
            "status": "running",
            "progress": 10,
            "message": "Initializing research...",
        }

        # Emit progress update
        socketio.emit(
            "phase_progress_update",
            {"phase": "A02_Research", "progress": 10, "message": "Research initialized"},
        )

        # Run research
        results = research_bot.research_case(case_id, research_query)

        # Update status to completed
        research_status_store[case_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Research completed",
        }
        research_results_store[case_id] = results

        # Emit completion update
        socketio.emit(
            "phase_progress_update",
            {
                "phase": "A02_Research",
                "progress": 100,
                "message": f'Research completed with {len(results.get("sources", []))} sources found',
            },
        )

        # Trigger evidence feedback loop if new sources found
        if len(results.get("sources", [])) > 0:
            socketio.start_background_task(process_research_feedback, case_id, results)

    except Exception as e:
        logger.error(f"Research failed: {e}")
        research_status_store[case_id] = {"status": "failed", "progress": 0, "message": str(e)}

        socketio.emit(
            "phase_progress_update",
            {"phase": "A02_Research", "progress": 0, "message": f"Research failed: {str(e)}"},
        )


def run_outline_generation(case_id: str):
    """Run outline generation in background"""
    try:
        # Update status to running
        outline_status_store[case_id] = {
            "status": "running",
            "progress": 10,
            "message": "Initializing outline generation...",
        }

        # Emit progress update
        socketio.emit(
            "phase_progress_update",
            {"phase": "A03_Outline", "progress": 10, "message": "Outline generation initialized"},
        )

        # Generate outline
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            outline = loop.run_until_complete(
                outline_generator.generate_enhanced_outline(case_id, f"session_{case_id}")
            )
        finally:
            loop.close()

        # Update status to completed
        outline_status_store[case_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Outline generation completed",
        }
        outline_results_store[case_id] = outline

        # Emit completion update
        socketio.emit(
            "phase_progress_update",
            {
                "phase": "A03_Outline",
                "progress": 100,
                "message": f'Outline generated with {len(outline.get("sections", []))} sections',
            },
        )

    except Exception as e:
        logger.error(f"Outline generation failed: {e}")
        outline_status_store[case_id] = {"status": "failed", "progress": 0, "message": str(e)}

        socketio.emit(
            "phase_progress_update",
            {
                "phase": "A03_Outline",
                "progress": 0,
                "message": f"Outline generation failed: {str(e)}",
            },
        )


def process_research_feedback(case_id: str, research_results: Dict[str, Any]):
    """Process research results back through evidence intake"""
    try:
        new_sources_count = 0
        max_sources = 10  # Stop after finding 10 new sources

        for source in research_results.get("sources", []):
            if new_sources_count >= max_sources:
                break

            # Check if source already exists in evidence
            if not evidence_table.source_exists(source.get("citation", "")):
                # Add new source to evidence table
                evidence_entry = {
                    "source_document": source.get("title", ""),
                    "content": source.get("summary", ""),
                    "evidence_type": "secondary_authority",
                    "relevance_score": source.get("relevance_score", 0.5),
                    "bluebook_citation": source.get("citation", ""),
                    "key_terms": source.get("key_terms", []),
                    "notes": f"Found via research for case {case_id}",
                }

                evidence_table.add_evidence(evidence_entry)
                new_sources_count += 1

        if new_sources_count > 0:
            socketio.emit(
                "phase_progress_update",
                {
                    "phase": "A02_Research",
                    "progress": 100,
                    "message": f"Added {new_sources_count} new sources to evidence table",
                },
            )

    except Exception as e:
        logger.error(f"Research feedback processing failed: {e}")


def main():
    """Main server entry point with proper error handling."""
    parser = argparse.ArgumentParser(description="LawyerFactory API Server")
    parser.add_argument("--port", type=int, default=5000, help="Port to run server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to run server on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    try:
        # Use the globally configured Flask app and SocketIO instance
        # All routes are already registered on the global `app` and `socketio` instances
        
        print(f"🚀 Starting LawyerFactory API server...")
        print(f"🌐 Server: http://{args.host}:{args.port}")
        print(f"📡 SocketIO async mode: {socketio.async_mode}")
        print(f"✅ Health endpoint: http://{args.host}:{args.port}/api/health")

        # Run with eventlet using the global app and socketio instances
        socketio.run(
            app,
            host=args.host,
            port=args.port,
            debug=args.debug,
            use_reloader=False,  # Disable reloader with eventlet
        )

    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        logging.exception("Server startup error")
        sys.exit(1)


if __name__ == "__main__":
    main()
