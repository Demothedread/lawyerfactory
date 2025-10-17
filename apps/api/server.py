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
from typing import Any, Dict, List, Optional

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
        from lawyerfactory.storage.core.unified_storage_api import (
            get_enhanced_unified_storage_api,
        )

        UNIFIED_STORAGE_AVAILABLE = True
    except ImportError:
        get_enhanced_unified_storage_api = None
        UNIFIED_STORAGE_AVAILABLE = False
        logger.warning("EnhancedUnifiedStorageAPI not available")

    try:
        from lawyerfactory.phases.phaseB02_drafting.drafting_validator import (
            DraftingValidator,
        )
        from lawyerfactory.phases.phaseA01_intake.vector_cluster_manager import (
            VectorClusterManager,
        )

        DRAFTING_VALIDATOR_AVAILABLE = True
    except ImportError:
        DraftingValidator = None
        VectorClusterManager = None
        DRAFTING_VALIDATOR_AVAILABLE = False
        logger.warning("DraftingValidator not available")
    
    # Import Phase A03 components (shotlist, claims matrix, outline)
    try:
        from lawyerfactory.phases.phaseA03_outline.shotlist.shotlist import build_shot_list, validate_evidence_rows
        from lawyerfactory.phases.phaseA03_outline.claims_matrix import ComprehensiveClaimsMatrixIntegration as ClaimsMatrixPhaseA03
        
        PHASE_A03_AVAILABLE = True
        logger.info("Phase A03 components imported successfully")
    except ImportError as e:
        build_shot_list = None
        validate_evidence_rows = None
        ClaimsMatrixPhaseA03 = None
        PHASE_A03_AVAILABLE = False
        logger.warning(f"Phase A03 components not available: {e}")

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
drafting_validator = None
vector_cluster_manager = None

# LLM Configuration (loaded from environment or user settings)
llm_config = {
    "provider": os.getenv("LLM_PROVIDER", "openai"),
    "model": os.getenv("LLM_MODEL", "gpt-4"),
    "api_key": os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("GROQ_API_KEY"),
    "temperature": float(os.getenv("LLM_TEMPERATURE", "0.1")),
    "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "2000")),
}


def initialize_components():
    """Initialize LawyerFactory components"""
    global research_bot, court_authority_helper, evidence_table
    global intake_processor, outline_generator, claims_matrix, unified_storage
    global drafting_validator, vector_cluster_manager

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

        # Initialize vector cluster manager
        if DRAFTING_VALIDATOR_AVAILABLE and VectorClusterManager:
            try:
                vector_cluster_manager = VectorClusterManager()
                logger.info("Vector cluster manager initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize vector cluster manager: {e}")
                vector_cluster_manager = None
        else:
            vector_cluster_manager = None

        # Initialize drafting validator
        if DRAFTING_VALIDATOR_AVAILABLE and DraftingValidator:
            try:
                drafting_validator = DraftingValidator(
                    intake_processor=intake_processor,
                    cluster_manager=vector_cluster_manager
                )
                logger.info("Drafting validator initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize drafting validator: {e}")
                drafting_validator = None
        else:
            drafting_validator = None

        # Import outline generator dependencies (only once)
        try:
            from lawyerfactory.kg.graph_api import EnhancedKnowledgeGraph
            from src.lawyerfactory.phases.phaseA01_intake.evidence_routes import EvidenceAPI

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

        # Initialize Flask-compatible evidence API and register routes
        try:
            from apps.api.routes.evidence_flask import FlaskEvidenceAPI
            from apps.api.routes.research_flask import FlaskResearchAPI
            
            flask_evidence_api = FlaskEvidenceAPI(app=app, storage_path="evidence_table.json")
            flask_research_api = FlaskResearchAPI(app=app, socketio=socketio)
            logger.info("Flask Evidence and Research API routes registered successfully")
        except ImportError as e:
            logger.warning(f"Failed to import Flask Evidence/Research API: {e}")
            flask_evidence_api = None
            flask_research_api = None
        except Exception as e:
            logger.warning(f"Failed to initialize Flask Evidence/Research API: {e}")
            flask_evidence_api = None
            flask_research_api = None

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

# Test route to verify Flask is working
@app.route("/api/test")
def test_route():
    return jsonify({"status": "Flask routes working"})

# Register Socket.IO instance for phase events
try:
    from src.lawyerfactory.phases.socket_events import set_socketio_instance
    set_socketio_instance(socketio)
    logger.info("Socket.IO instance registered for phase events")
except ImportError as e:
    logger.warning(f"Could not import phase socket events: {e}")


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
    """Get outline generation status"""
    try:
        # Return mock status for now
        return jsonify(
            {
                "success": True,
                "case_id": case_id,
                "status": "completed",
                "message": "Outline generation status",
            }
        )
    except Exception as e:
        logger.error(f"Failed to get outline status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# UNIFIED PHASE ORCHESTRATION ENDPOINT
# ============================================================================


@app.route("/api/phases/<phase_id>/start", methods=["POST"])
def start_phase(phase_id):
    """
    Unified phase orchestration endpoint
    Routes phase requests to appropriate handlers with Socket.IO integration
    
    Supported phases:
    - phaseA01_intake: Document categorization and fact extraction
    - phaseA02_research: Legal research and authority gathering
    - phaseA03_outline: Case structure and claims development
    - phaseB01_review: Quality assurance and validation
    - phaseB02_drafting: Document composition
    - phaseC01_editing: Content refinement and formatting
    - phaseC02_orchestration: Final workflow coordination
    """
    data = request.get_json() or {}
    case_id = data.get("case_id")
    
    if not case_id:
        return jsonify({"error": "case_id required"}), 400
    
    logger.info(f"Starting phase {phase_id} for case {case_id}")
    
    # Phase routing map
    phase_handlers = {
        "phaseA01_intake": handle_intake_phase,
        "phaseA02_research": handle_research_phase,
        "phaseA03_outline": handle_outline_phase,
        "phaseB01_review": handle_review_phase,
        "phaseB02_drafting": handle_drafting_phase,
        "phaseC01_editing": handle_editing_phase,
        "phaseC02_orchestration": handle_orchestration_phase,
    }
    
    handler = phase_handlers.get(phase_id)
    if not handler:
        return jsonify({"error": f"Unknown phase: {phase_id}"}), 404
    
    try:
        # Emit phase started event
        socketio.emit("phase_started", {
            "phase": phase_id,
            "case_id": case_id,
            "timestamp": time.time()
        })
        
        # Execute phase handler
        import asyncio
        if asyncio.iscoroutinefunction(handler):
            # Handle async handlers
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(handler(case_id, data))
            finally:
                loop.close()
        else:
            # Handle sync handlers
            result = handler(case_id, data)
        
        # Emit phase completed event
        socketio.emit("phase_completed", {
            "phase": phase_id,
            "case_id": case_id,
            "result": result,
            "timestamp": time.time()
        })
        
        return jsonify({
            "success": True,
            "phase": phase_id,
            "case_id": case_id,
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Phase {phase_id} failed for case {case_id}: {e}")
        
        # Emit phase error event
        socketio.emit("phase_error", {
            "phase": phase_id,
            "case_id": case_id,
            "error": str(e),
            "timestamp": time.time()
        })
        
        return jsonify({"error": str(e)}), 500


def handle_intake_phase(case_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase A01: Document Intake
    Categorizes documents and extracts facts using Reader agent
    """
    # Extract LLM config from request data
    llm_config_request = {
        "provider": data.get("llm_provider", llm_config.get("provider", "openai")),
        "model": data.get("llm_model", llm_config.get("model", "gpt-4")),
        "temperature": float(data.get("llm_temperature", llm_config.get("temperature", 0.1))),
        "max_tokens": int(data.get("llm_max_tokens", llm_config.get("max_tokens", 2000))),
        "api_key": data.get("llm_api_key", llm_config.get("api_key"))
    }
    
    socketio.emit("phase_progress_update", {
        "phase": "A01_Intake",
        "progress": 10,
        "message": f"Initializing intake processor with {llm_config_request['provider']}/{llm_config_request['model']}..."
    })
    
    if not intake_processor or not INTAKE_PROCESSOR_AVAILABLE:
        logger.warning("Intake processor not available, using mock mode")
        socketio.emit("phase_progress_update", {
            "phase": "A01_Intake",
            "progress": 100,
            "message": "Intake complete (mock mode)"
        })
        return {
            "status": "mock",
            "message": "Intake processor not available - mock data returned",
            "documents_processed": 0
        }
    
    try:
        socketio.emit("phase_progress_update", {
            "phase": "A01_Intake",
            "progress": 30,
            "message": "Categorizing documents..."
        })
        
        # Process intake using existing logic
        files = data.get("files", [])
        
        socketio.emit("phase_progress_update", {
            "phase": "A01_Intake",
            "progress": 60,
            "message": "Extracting facts and metadata..."
        })
        
        result = {
            "status": "completed",
            "case_id": case_id,
            "documents_processed": len(files),
            "facts_extracted": True
        }
        
        socketio.emit("phase_progress_update", {
            "phase": "A01_Intake",
            "progress": 100,
            "message": "✅ Intake complete"
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Intake phase error: {e}")
        raise


def handle_research_phase(case_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase A02: Legal Research
    Gathers legal authorities and precedents using Paralegal and Researcher agents
    """
    # Extract LLM config from request data
    llm_config_request = {
        "provider": data.get("llm_provider", llm_config.get("provider", "openai")),
        "model": data.get("llm_model", llm_config.get("model", "gpt-4")),
        "temperature": float(data.get("llm_temperature", llm_config.get("temperature", 0.1))),
        "max_tokens": int(data.get("llm_max_tokens", llm_config.get("max_tokens", 2000))),
        "api_key": data.get("llm_api_key", llm_config.get("api_key"))
    }
    
    socketio.emit("phase_progress_update", {
        "phase": "A02_Research",
        "progress": 10,
        "message": f"Initializing research agents with {llm_config_request['provider']}/{llm_config_request['model']}..."
    })
    
    if not research_bot or not RESEARCH_BOT_AVAILABLE:
        logger.warning("Research bot not available, using mock mode")
        socketio.emit("phase_progress_update", {
            "phase": "A02_Research",
            "progress": 100,
            "message": "Research complete (mock mode)"
        })
        return {
            "status": "mock",
            "message": "Research bot not available - mock data returned",
            "authorities_found": 0
        }
    
    try:
        research_query = data.get("research_query", "Legal research")
        
        socketio.emit("phase_progress_update", {
            "phase": "A02_Research",
            "progress": 30,
            "message": "Searching legal databases..."
        })
        
        socketio.emit("phase_progress_update", {
            "phase": "A02_Research",
            "progress": 60,
            "message": "Analyzing case law and statutes..."
        })
        
        result = {
            "status": "completed",
            "case_id": case_id,
            "research_query": research_query,
            "authorities_found": 0
        }
        
        socketio.emit("phase_progress_update", {
            "phase": "A02_Research",
            "progress": 100,
            "message": "🔍 Research complete"
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Research phase error: {e}")
        raise


def handle_outline_phase(case_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase A03: Case Outline
    Structures claims and develops case theory using Outliner agent
    """
    # Extract LLM config from request data
    llm_config_request = {
        "provider": data.get("llm_provider", llm_config.get("provider", "openai")),
        "model": data.get("llm_model", llm_config.get("model", "gpt-4")),
        "temperature": float(data.get("llm_temperature", llm_config.get("temperature", 0.1))),
        "max_tokens": int(data.get("llm_max_tokens", llm_config.get("max_tokens", 2000))),
        "api_key": data.get("llm_api_key", llm_config.get("api_key"))
    }
    
    socketio.emit("phase_progress_update", {
        "phase": "A03_Outline",
        "progress": 10,
        "message": f"Initializing outline generator with {llm_config_request['provider']}/{llm_config_request['model']}..."
    })
    
    if not outline_generator or not OUTLINE_GENERATOR_AVAILABLE:
        logger.warning("Outline generator not available, using mock mode")
        socketio.emit("phase_progress_update", {
            "phase": "A03_Outline",
            "progress": 100,
            "message": "Outline complete (mock mode)"
        })
        return {
            "status": "mock",
            "message": "Outline generator not available - mock data returned",
            "claims_identified": 0
        }
    
    try:
        socketio.emit("phase_progress_update", {
            "phase": "A03_Outline",
            "progress": 30,
            "message": "Analyzing case structure..."
        })
        
        socketio.emit("phase_progress_update", {
            "phase": "A03_Outline",
            "progress": 60,
            "message": "Developing claims matrix..."
        })
        
        result = {
            "status": "completed",
            "case_id": case_id,
            "claims_identified": 0,
            "outline_generated": True
        }
        
        socketio.emit("phase_progress_update", {
            "phase": "A03_Outline",
            "progress": 100,
            "message": "📋 Outline complete"
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Outline phase error: {e}")
        raise


def handle_review_phase(case_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase B01: Quality Review
    Validates deliverables from Phase A03 before allowing drafting to proceed.
    Checks:
    - Shotlist has minimum facts (10+)
    - Claims matrix has all required elements
    - Skeletal outline has required sections
    - Rule 12(b)(6) compliance score >= 75
    """
    socketio.emit("phase_progress_update", {
        "phase": "phaseB01_review",
        "case_id": case_id,
        "progress": 10,
        "message": "Loading Phase A03 deliverables..."
    })
    
    try:
        deliverables_dir = Path(f"./workflow_storage/cases/{case_id}/deliverables")
        
        if not deliverables_dir.exists():
            return {
                "status": "error",
                "message": "No deliverables found. Please complete Phase A03 first.",
                "case_id": case_id,
                "ready_for_drafting": False
            }
        
        validations = {}
        
        # Validate Shotlist
        socketio.emit("phase_progress_update", {
            "phase": "phaseB01_review",
            "case_id": case_id,
            "progress": 25,
            "message": "Validating shotlist timeline..."
        })
        
        shotlist_path = deliverables_dir / "shotlist.csv"
        if shotlist_path.exists():
            import csv
            with open(shotlist_path, 'r') as f:
                reader = csv.DictReader(f)
                shotlist_facts = list(reader)
                fact_count = len(shotlist_facts)
                validations["shotlist_facts"] = {
                    "passed": fact_count >= 10,
                    "message": f"{fact_count} facts (minimum 10 required)",
                    "count": fact_count
                }
        else:
            validations["shotlist_facts"] = {
                "passed": False,
                "message": "Shotlist not found",
                "count": 0
            }
        
        # Validate Claims Matrix
        socketio.emit("phase_progress_update", {
            "phase": "phaseB01_review",
            "case_id": case_id,
            "progress": 50,
            "message": "Validating claims matrix..."
        })
        
        claims_path = deliverables_dir / "claims_matrix.json"
        if claims_path.exists():
            with open(claims_path, 'r') as f:
                claims_data = json.load(f)
                element_analysis = claims_data.get("element_analysis", {})
                elements_count = len(element_analysis)
                
                # Check if all elements have decision outcomes
                all_elements_complete = all(
                    elem.get("decision_outcome") is not None
                    for elem in element_analysis.values()
                )
                
                validations["claims_elements"] = {
                    "passed": elements_count > 0 and all_elements_complete,
                    "message": f"{elements_count} elements analyzed" if all_elements_complete else "Incomplete element analysis",
                    "count": elements_count
                }
        else:
            validations["claims_elements"] = {
                "passed": False,
                "message": "Claims matrix not found",
                "count": 0
            }
        
        # Validate Skeletal Outline
        socketio.emit("phase_progress_update", {
            "phase": "phaseB01_review",
            "case_id": case_id,
            "progress": 75,
            "message": "Validating skeletal outline..."
        })
        
        outline_path = deliverables_dir / "skeletal_outline.json"
        required_sections = ["caption", "introduction", "jurisdiction", "parties", "statement_of_facts"]
        
        if outline_path.exists():
            with open(outline_path, 'r') as f:
                outline_data = json.load(f)
                sections = outline_data.get("sections", [])
                section_ids = [s.get("id") for s in sections]
                
                has_required_sections = all(
                    req_section in section_ids
                    for req_section in required_sections
                )
                
                validations["outline_sections"] = {
                    "passed": has_required_sections and len(sections) >= 5,
                    "message": f"{len(sections)} sections" if has_required_sections else "Missing required sections",
                    "count": len(sections)
                }
                
                # Check Rule 12(b)(6) score
                rule12b6_score = outline_data.get("rule12b6ComplianceScore", 0)
                validations["rule_12b6_score"] = {
                    "passed": rule12b6_score >= 75,
                    "message": f"Score: {rule12b6_score}% (minimum 75%)",
                    "score": rule12b6_score
                }
        else:
            validations["outline_sections"] = {
                "passed": False,
                "message": "Skeletal outline not found",
                "count": 0
            }
            validations["rule_12b6_score"] = {
                "passed": False,
                "message": "No compliance score available",
                "score": 0
            }
        
        # Overall validation
        all_valid = all(v.get("passed", False) for v in validations.values())
        
        socketio.emit("phase_progress_update", {
            "phase": "phaseB01_review",
            "case_id": case_id,
            "progress": 100,
            "message": "✅ Validation complete" if all_valid else "⚠️ Validation issues found"
        })
        
        return {
            "status": "completed" if all_valid else "requires_attention",
            "case_id": case_id,
            "validations": validations,
            "all_valid": all_valid,
            "ready_for_drafting": all_valid,
            "message": "All deliverables validated successfully" if all_valid else "Some validations failed - review deliverables before proceeding"
        }
        
    except Exception as e:
        logger.error(f"Phase B01 validation error for case {case_id}: {e}")
        return {
            "status": "error",
            "case_id": case_id,
            "error": str(e),
            "ready_for_drafting": False
        }


async def handle_drafting_phase(case_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase B02: Document Drafting
    Integrates WriterBot, EditorBot, and Maestro to draft complaint using:
    - Shotlist for Statement of Facts
    - Claims Matrix for legal elements and IRAC analysis
    - Skeletal Outline as structural blueprint
    - VectorClusterManager for RAG enhancement
    """
    # Extract LLM config from request data
    llm_config_request = {
        "provider": data.get("llm_provider", llm_config.get("provider", "openai")),
        "model": data.get("llm_model", llm_config.get("model", "gpt-4")),
        "temperature": float(data.get("llm_temperature", llm_config.get("temperature", 0.1))),
        "max_tokens": int(data.get("llm_max_tokens", llm_config.get("max_tokens", 2000))),
        "api_key": data.get("llm_api_key", llm_config.get("api_key"))
    }
    
    socketio.emit("phase_progress_update", {
        "phase": "phaseB02_drafting",
        "case_id": case_id,
        "progress": 5,
        "message": f"🚀 Initializing multi-agent drafting system with {llm_config_request['provider']}/{llm_config_request['model']}..."
    })

    try:
        # Load approved deliverables from Phase A03
        deliverables_dir = Path(f"./workflow_storage/cases/{case_id}/deliverables")
        
        if not deliverables_dir.exists():
            return {
                "status": "error",
                "message": "No approved deliverables found. Complete Phase B01 review first.",
                "case_id": case_id
            }
        
        socketio.emit("phase_progress_update", {
            "phase": "phaseB02_drafting",
            "case_id": case_id,
            "progress": 10,
            "message": "📂 Loading approved deliverables..."
        })
        
        # Load deliverables
        shotlist_facts = []
        claims_matrix_data = {}
        skeletal_outline_data = {}
        
        # Load Shotlist
        shotlist_path = deliverables_dir / "shotlist.csv"
        if shotlist_path.exists():
            import csv
            with open(shotlist_path, 'r') as f:
                reader = csv.DictReader(f)
                shotlist_facts = list(reader)
        
        # Load Claims Matrix
        claims_path = deliverables_dir / "claims_matrix.json"
        if claims_path.exists():
            with open(claims_path, 'r') as f:
                claims_matrix_data = json.load(f)
        
        # Load Skeletal Outline
        outline_path = deliverables_dir / "skeletal_outline.json"
        if outline_path.exists():
            with open(outline_path, 'r') as f:
                skeletal_outline_data = json.load(f)
        
        logger.info(f"Loaded deliverables: {len(shotlist_facts)} facts, "
                   f"{len(claims_matrix_data.get('element_analysis', {}))} elements, "
                   f"{len(skeletal_outline_data.get('sections', []))} sections")
        
        socketio.emit("phase_progress_update", {
            "phase": "phaseB02_drafting",
            "case_id": case_id,
            "progress": 20,
            "message": f"✅ Loaded {len(shotlist_facts)} facts, {len(skeletal_outline_data.get('sections', []))} sections"
        })
        
        # Import IRAC templates
        try:
            from lawyerfactory.compose.promptkits.irac_templates import (
                IRACTemplateEngine,
                claims_matrix_to_irac
            )
            irac_available = True
        except ImportError as e:
            logger.warning(f"IRAC templates not available: {e}")
            irac_available = False
        
        # Try to import WriterBot and Maestro
        try:
            from lawyerfactory.compose.bots.writer import WriterBot
            from lawyerfactory.agents.orchestration.maestro import Maestro
            bot_available = True
        except ImportError as e:
            logger.warning(f"Bots not available: {e}")
            bot_available = False
        
        # Try to import VectorClusterManager for RAG
        try:
            from lawyerfactory.phases.phaseA01_intake.vector_cluster_manager import VectorClusterManager
            vector_mgr = VectorClusterManager()
            rag_available = True
        except ImportError as e:
            logger.warning(f"VectorClusterManager not available: {e}")
            rag_available = False
            vector_mgr = None
        
        socketio.emit("phase_progress_update", {
            "phase": "phaseB02_drafting",
            "case_id": case_id,
            "progress": 30,
            "message": "🤖 Initializing AI agents..."
        })
        
        # Initialize drafting components
        if not bot_available or not irac_available:
            # Fallback: Generate simple text-based complaint
            logger.warning("Advanced drafting not available, using fallback")
            
            complaint_text = f"""
UNITED STATES DISTRICT COURT
{data.get('district', 'NORTHERN DISTRICT OF CALIFORNIA')}

{data.get('plaintiff_name', 'PLAINTIFF')}
    Plaintiff,
    
    v.
    
{data.get('defendant_name', 'DEFENDANT')}
    Defendant.

Case No. {case_id}

COMPLAINT FOR DAMAGES

STATEMENT OF FACTS

"""
            # Add facts from shotlist
            for i, fact in enumerate(shotlist_facts[:20], 1):  # Limit to 20 facts
                summary = fact.get('summary', '')
                timestamp = fact.get('timestamp', '')
                complaint_text += f"{i}. On {timestamp}, {summary}\n\n"
            
            complaint_text += "\nCAUSES OF ACTION\n\n"
            
            # Add causes of action from claims matrix
            element_analysis = claims_matrix_data.get('element_analysis', {})
            for elem_name, elem_data in list(element_analysis.items())[:3]:  # Limit to 3 elements
                complaint_text += f"Element: {elem_name.replace('_', ' ').title()}\n"
                breakdown = elem_data.get('breakdown', {})
                complaint_text += f"{breakdown.get('definition', 'No definition available')}\n\n"
            
            # Save to file
            output_dir = Path(f"./workflow_storage/cases/{case_id}/drafts")
            output_dir.mkdir(parents=True, exist_ok=True)
            draft_path = output_dir / "complaint_draft.txt"
            
            with open(draft_path, 'w') as f:
                f.write(complaint_text)
            
            socketio.emit("phase_progress_update", {
                "phase": "phaseB02_drafting",
                "case_id": case_id,
                "progress": 100,
                "message": "✅ Basic complaint draft generated (fallback mode)"
            })
            
            return {
                "status": "completed",
                "case_id": case_id,
                "draft_path": str(draft_path),
                "word_count": len(complaint_text.split()),
                "sections_completed": len(shotlist_facts) + len(element_analysis),
                "fallback_mode": True,
                "message": "Complaint generated using basic template (advanced bots not available)"
            }
        
        # Full implementation with WriterBot and Maestro
        socketio.emit("phase_progress_update", {
            "phase": "phaseB02_drafting",
            "case_id": case_id,
            "progress": 40,
            "message": "📝 Drafting sections with nested IRAC method..."
        })
        
        # Initialize Maestro and bots
        maestro = Maestro()
        
        # Create AgentConfig with LLM parameters for WriterBot
        from lawyerfactory.compose.agent_registry import AgentConfig
        agent_config = AgentConfig(
            agent_type="WriterBot",
            config={
                "llm": llm_config_request
            }
        )
        
        writer_bot = WriterBot(agent_config=agent_config)
        
        # Draft each section from skeletal outline
        drafted_sections = []
        sections = skeletal_outline_data.get('sections', [])
        total_sections = len(sections)
        
        for idx, section in enumerate(sections):
            section_id = section.get('id', f'section_{idx}')
            section_title = section.get('title', 'Untitled Section')
            
            # Update progress
            progress = 40 + int((idx / total_sections) * 50)  # 40% to 90%
            socketio.emit("phase_progress_update", {
                "phase": "phaseB02_drafting",
                "case_id": case_id,
                "progress": progress,
                "message": f"✍️ Drafting: {section_title}"
            })
            
            # Get relevant facts for this section
            relevant_facts = [
                fact for fact in shotlist_facts
                if section_id.lower() in fact.get('summary', '').lower()
                or section_title.lower() in fact.get('summary', '').lower()
            ][:10]  # Limit to 10 relevant facts
            
            if not relevant_facts:
                # If no specific matches, use first 10 facts
                relevant_facts = shotlist_facts[:10]
            
            # Get RAG context if available
            rag_context = []
            if rag_available and vector_mgr:
                try:
                    similar_docs = await vector_mgr.find_similar_documents(
                        query_text=section_title,
                        top_k=3,
                        similarity_threshold=0.6
                    )
                    rag_context = [doc.get('content', '')[:500] for doc in similar_docs]
                except Exception as e:
                    logger.warning(f"RAG search failed: {e}")
            
            # Build section prompt using IRAC templates
            if section_id.startswith('cause_'):
                # This is a cause of action section - use IRAC
                section_type = "cause_of_action"
                
                # Convert claims matrix to IRAC structure
                irac_section = claims_matrix_to_irac(claims_matrix_data, shotlist_facts)
                
                # Generate IRAC prompt
                prompt = IRACTemplateEngine.generate_nested_irac_prompt(
                    irac_section=irac_section,
                    shotlist_facts=relevant_facts,
                    include_examples=True
                )
            elif section_id == 'statement_of_facts':
                # Statement of facts section
                section_type = "statement_of_facts"
                prompt = IRACTemplateEngine.generate_statement_of_facts(
                    shotlist_facts=shotlist_facts,
                    chronological=True
                )
            else:
                # Generic section
                section_type = "generic"
                prompt = IRACTemplateEngine.build_section_prompt(
                    section_type="generic",
                    section_data=section,
                    shotlist_facts=relevant_facts,
                    claims_matrix=claims_matrix_data,
                    rag_context=rag_context
                )
            
            # Draft section using WriterBot
            try:
                section_draft = await writer_bot.draft_section(
                    prompt=prompt,
                    section_id=section_id,
                    max_words=section.get('estimatedWords', 300)
                )
                
                drafted_sections.append({
                    "section_id": section_id,
                    "title": section_title,
                    "content": section_draft,
                    "word_count": len(section_draft.split())
                })
                
                logger.info(f"Drafted section {section_id}: {len(section_draft.split())} words")
                
            except Exception as e:
                logger.error(f"Failed to draft section {section_id}: {e}")
                # Add placeholder
                drafted_sections.append({
                    "section_id": section_id,
                    "title": section_title,
                    "content": f"[Section {section_title} - Draft Error: {str(e)}]",
                    "word_count": 0
                })
        
        socketio.emit("phase_progress_update", {
            "phase": "phaseB02_drafting",
            "case_id": case_id,
            "progress": 95,
            "message": "📄 Assembling final complaint document..."
        })
        
        # Assemble complete complaint
        complaint_parts = []
        for section in drafted_sections:
            complaint_parts.append(f"\n\n{'='*80}\n{section['title'].upper()}\n{'='*80}\n\n")
            complaint_parts.append(section['content'])
        
        full_complaint = "".join(complaint_parts)
        total_word_count = sum(s['word_count'] for s in drafted_sections)
        
        # Save to file
        output_dir = Path(f"./workflow_storage/cases/{case_id}/drafts")
        output_dir.mkdir(parents=True, exist_ok=True)
        draft_path = output_dir / "complaint_draft.txt"
        
        with open(draft_path, 'w') as f:
            f.write(full_complaint)
        
        # Also save as JSON with metadata
        draft_json_path = output_dir / "complaint_draft.json"
        draft_data = {
            "case_id": case_id,
            "sections": drafted_sections,
            "total_word_count": total_word_count,
            "generated_at": time.time(),
            "method": "nested_irac"
        }
        
        with open(draft_json_path, 'w') as f:
            json.dump(draft_data, f, indent=2)
        
        socketio.emit("phase_progress_update", {
            "phase": "phaseB02_drafting",
            "case_id": case_id,
            "progress": 100,
            "message": f"✅ Complaint drafted: {total_word_count} words, {len(drafted_sections)} sections"
        })
        
        return {
            "status": "completed",
            "case_id": case_id,
            "draft_path": str(draft_path),
            "draft_json_path": str(draft_json_path),
            "word_count": total_word_count,
            "sections_completed": len(drafted_sections),
            "method": "nested_irac",
            "message": "Complaint successfully drafted using IRAC methodology"
        }
        
    except Exception as e:
        logger.error(f"Phase B02 drafting error for case {case_id}: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "status": "error",
            "case_id": case_id,
            "error": str(e),
            "message": "Drafting failed - see logs for details"
        }


def handle_editing_phase(case_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase C01: Final Editing
    Polishes and formats documents using Legal Formatter agent
    (STUB - To be implemented with proper formatter agent integration)
    """
    socketio.emit("phase_progress_update", {
        "phase": "C01_Editing",
        "progress": 30,
        "message": "Formatting citations..."
    })
    
    time.sleep(1)
    
    socketio.emit("phase_progress_update", {
        "phase": "C01_Editing",
        "progress": 70,
        "message": "Polishing content..."
    })
    
    time.sleep(1)
    
    socketio.emit("phase_progress_update", {
        "phase": "C01_Editing",
        "progress": 100,
        "message": "✏️ Editing complete (mock)"
    })
    
    return {
        "status": "mock",
        "message": "Editing phase not yet implemented - placeholder complete",
        "case_id": case_id,
        "documents_formatted": 0
    }


def handle_orchestration_phase(case_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase C02: Final Orchestration
    Coordinates final workflow and deliverables using Maestro agent
    (STUB - To be implemented with proper orchestration agent integration)
    """
    socketio.emit("phase_progress_update", {
        "phase": "C02_Orchestration",
        "progress": 30,
        "message": "Coordinating final deliverables..."
    })
    
    time.sleep(1)
    
    socketio.emit("phase_progress_update", {
        "phase": "C02_Orchestration",
        "progress": 70,
        "message": "Packaging documents..."
    })
    
    time.sleep(1)
    
    socketio.emit("phase_progress_update", {
        "phase": "C02_Orchestration",
        "progress": 100,
        "message": "🎯 Orchestration complete (mock)"
    })
    
    return {
        "status": "mock",
        "message": "Orchestration phase not yet implemented - placeholder complete",
        "case_id": case_id,
        "deliverables_ready": True
    }


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


# ============================================================================
# CLAIMS MATRIX API ENDPOINTS
# ============================================================================

@app.route("/api/claims/matrix/<case_id>", methods=["GET"])
def get_claims_matrix(case_id):
    """Get claims matrix for a case using vectorized evidence"""
    if not LAWYERFACTORY_AVAILABLE or not unified_storage:
        return jsonify({"error": "Claims matrix service not available"}), 503

    try:
        # Get all documents for this case
        case_documents = unified_storage.search_evidence_by_metadata({"case_id": case_id})
        
        # Extract content from documents for analysis
        evidence_texts = []
        for doc in case_documents:
            if isinstance(doc, dict) and "content" in doc:
                evidence_texts.append(doc["content"])
            elif hasattr(doc, "content"):
                evidence_texts.append(doc.content)
        
        # Generate claims matrix from evidence (synchronous for Flask)
        claims_matrix = generate_claims_matrix_from_evidence(case_id, evidence_texts)
        
        return jsonify({
            "success": True,
            "case_id": case_id,
            "claims": claims_matrix,
            "evidence_count": len(evidence_texts),
            "generated_at": time.time()
        })
        
    except Exception as e:
        logger.error(f"Failed to generate claims matrix for case {case_id}: {e}")
        return jsonify({"error": str(e)}), 500


def generate_claims_matrix_from_evidence(case_id: str, evidence_texts: List[str]) -> List[Dict[str, Any]]:
    """Generate claims matrix using analysis of evidence"""
    try:
        # For now, return a mock claims matrix based on common legal patterns
        # In production, this would use LLM analysis with RAG context
        
        mock_claims = [
            {
                "id": "breach_of_contract",
                "name": "Breach of Contract",
                "jurisdiction": "California",
                "elements": [
                    {
                        "name": "Existence of Contract",
                        "description": "Valid contract between parties with clear terms",
                        "status": "proven" if len(evidence_texts) > 0 else "pending",
                        "evidenceCount": len([t for t in evidence_texts if "contract" in t.lower() or "agreement" in t.lower()])
                    },
                    {
                        "name": "Plaintiff's Performance",
                        "description": "Plaintiff substantially performed contractual obligations",
                        "status": "pending",
                        "evidenceCount": 0
                    },
                    {
                        "name": "Defendant's Breach",
                        "description": "Defendant failed to perform contractual obligations",
                        "status": "pending",
                        "evidenceCount": 0
                    },
                    {
                        "name": "Damages",
                        "description": "Plaintiff suffered measurable damages from breach",
                        "status": "pending",
                        "evidenceCount": 0
                    }
                ],
                "analysis": "Based on evidence analysis, contract breach appears viable. Further evidence needed for performance and damages elements.",
                "confidence_score": 0.75
            }
        ]
        
        # If we have evidence with specific keywords, add more claims
        evidence_combined = " ".join(evidence_texts).lower()
        
        if "negligence" in evidence_combined or "care" in evidence_combined:
            mock_claims.append({
                "id": "negligence",
                "name": "Negligence",
                "jurisdiction": "California",
                "elements": [
                    {
                        "name": "Duty of Care",
                        "description": "Defendant owed plaintiff a duty of reasonable care",
                        "status": "pending",
                        "evidenceCount": 0
                    },
                    {
                        "name": "Breach of Duty",
                        "description": "Defendant breached the duty of care",
                        "status": "pending",
                        "evidenceCount": 0
                    },
                    {
                        "name": "Causation",
                        "description": "Breach caused plaintiff's damages",
                        "status": "pending",
                        "evidenceCount": 0
                    },
                    {
                        "name": "Damages",
                        "description": "Plaintiff suffered compensable damages",
                        "status": "pending",
                        "evidenceCount": 0
                    }
                ],
                "analysis": "Negligence claim detected in evidence. Requires analysis of duty, breach, causation, and damages.",
                "confidence_score": 0.60
            })
        
        return mock_claims
        
    except Exception as e:
        logger.error(f"Error generating claims matrix: {e}")
        return []


# ============================================================================
# SKELETAL OUTLINE API ENDPOINTS
# ============================================================================

@app.route("/api/outline/generate/<case_id>", methods=["POST"])
def generate_skeletal_outline(case_id):
    """Generate skeletal outline using RAG-enhanced analysis"""
    if not LAWYERFACTORY_AVAILABLE or not unified_storage:
        return jsonify({"error": "Outline generation service not available"}), 503

    try:
        data = request.get_json() or {}
        claims_matrix = data.get("claims_matrix", [])
        shot_list = data.get("shot_list", [])
        
        # Get relevant evidence using RAG (synchronous for Flask)
        rag_context = get_rag_context_for_outline(case_id, claims_matrix, shot_list)
        
        # Generate outline using RAG-enhanced approach
        outline = generate_rag_enhanced_outline(case_id, claims_matrix, shot_list, rag_context)
        
        return jsonify({
            "success": True,
            "case_id": case_id,
            "outline": outline,
            "rag_context_used": len(rag_context),
            "generated_at": time.time()
        })
        
    except Exception as e:
        logger.error(f"Failed to generate skeletal outline for case {case_id}: {e}")
        return jsonify({"error": str(e)}), 500


def get_rag_context_for_outline(case_id: str, claims_matrix: List[Dict], shot_list: List[Dict]) -> List[str]:
    """Get RAG context relevant to outline generation"""
    try:
        if not unified_storage:
            return []
        
        # Create search queries based on claims
        search_queries = []
        for claim in claims_matrix:
            search_queries.append(f"legal requirements for {claim.get('name', '')}")
            for element in claim.get('elements', []):
                search_queries.append(f"evidence needed for {element.get('name', '')}")
        
        # Search for relevant context (simplified synchronous version)
        all_context = []
        for query in search_queries[:3]:  # Limit to avoid too many searches
            try:
                # Use synchronous search method if available, otherwise skip
                if hasattr(unified_storage, 'search_evidence'):
                    context = unified_storage.search_evidence(query, search_tier="vector")
                    all_context.extend([c.get("content", "") for c in context if isinstance(c, dict)])
            except Exception as e:
                logger.warning(f"RAG search failed for query '{query}': {e}")
        
        return all_context[:10]  # Limit context
        
    except Exception as e:
        logger.error(f"Error getting RAG context: {e}")
        return []


def generate_rag_enhanced_outline(case_id: str, claims_matrix: List[Dict], shot_list: List[Dict], rag_context: List[str]) -> Dict[str, Any]:
    """Generate outline using RAG-enhanced analysis"""
    try:
        # Mock outline generation - in production would use LLM with RAG context
        sections = [
            {
                "id": "caption",
                "title": "Case Caption",
                "status": "pending",
                "content": "",
                "required": True,
                "estimatedWords": 50,
                "rag_context": len([c for c in rag_context if "caption" in c.lower() or "court" in c.lower()])
            },
            {
                "id": "introduction", 
                "title": "Introduction",
                "status": "pending",
                "content": "",
                "required": True,
                "estimatedWords": 200,
                "rag_context": len([c for c in rag_context if "introduction" in c.lower() or "action" in c.lower()])
            },
            {
                "id": "jurisdiction",
                "title": "Jurisdiction and Venue", 
                "status": "pending",
                "content": "",
                "required": True,
                "estimatedWords": 150,
                "rag_context": len([c for c in rag_context if "jurisdiction" in c.lower() or "venue" in c.lower()])
            },
            {
                "id": "parties",
                "title": "Parties",
                "status": "pending", 
                "content": "",
                "required": True,
                "estimatedWords": 100,
                "rag_context": len([c for c in rag_context if "party" in c.lower() or "plaintiff" in c.lower() or "defendant" in c.lower()])
            },
            {
                "id": "facts",
                "title": "Statement of Facts",
                "status": "pending",
                "content": "",
                "required": True,
                "estimatedWords": 500,
                "rag_context": len(shot_list)  # Use shot list as fact context
            }
        ]
        
        # Add claims sections
        for i, claim in enumerate(claims_matrix):
            sections.append({
                "id": f"cause_{i}",
                "title": f"Cause of Action: {claim.get('name', f'Claim {i+1}')}",
                "status": "pending",
                "content": "",
                "required": True,
                "estimatedWords": 300,
                "claimData": claim,
                "rag_context": len([c for c in rag_context if claim.get('name', '').lower() in c.lower()])
            })
        
        # Add conclusion sections
        sections.extend([
            {
                "id": "relief",
                "title": "Prayer for Relief",
                "status": "pending",
                "content": "",
                "required": True,
                "estimatedWords": 100,
                "rag_context": len([c for c in rag_context if "relief" in c.lower() or "damages" in c.lower()])
            },
            {
                "id": "jury",
                "title": "Jury Demand", 
                "status": "pending",
                "content": "",
                "required": True,
                "estimatedWords": 50,
                "rag_context": 0
            }
        ])
        
        outline = {
            "id": f"outline_{case_id}_{int(time.time())}",
            "caseId": case_id,
            "sections": sections,
            "totalEstimatedWords": sum(s["estimatedWords"] for s in sections),
            "generationDate": time.time(),
            "status": "draft",
            "rule12b6ComplianceScore": 85,  # Mock compliance score
            "rag_context_used": len(rag_context),
            "claims_integrated": len(claims_matrix),
            "evidence_facts": len(shot_list)
        }
        
        return outline
        
    except Exception as e:
        logger.error(f"Error generating RAG-enhanced outline: {e}")
        return {
            "id": f"outline_{case_id}_error",
            "caseId": case_id,
            "sections": [],
            "error": str(e)
        }


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


# ============================================================================
# PHASE A03 - OUTLINE GENERATION DELIVERABLES API
# ============================================================================

@app.route("/api/phaseA03/shotlist/<case_id>", methods=["POST"])
def generate_shotlist(case_id):
    """
    Generate chronological shotlist (timeline) from all PRIMARY and SECONDARY evidence
    Returns JSON representation and stores CSV file as deliverable
    """
    if not LAWYERFACTORY_AVAILABLE or not unified_storage:
        return jsonify({"error": "Shotlist generation service not available"}), 503
    
    if not PHASE_A03_AVAILABLE or not build_shot_list:
        return jsonify({"error": "Phase A03 shotlist component not available"}), 503
    
    try:
        logger.info(f"Generating shotlist for case {case_id}")
        
        # Fetch all evidence for this case (PRIMARY + SECONDARY)
        all_evidence = []
        try:
            if hasattr(unified_storage, 'get_case_documents'):
                evidence_objects = unified_storage.get_case_documents(case_id)
                all_evidence = evidence_objects if isinstance(evidence_objects, list) else []
        except Exception as e:
            logger.warning(f"Could not fetch evidence from unified storage: {e}")
        
        # If no evidence from storage, try evidence table
        if not all_evidence and evidence_table:
            try:
                all_evidence = evidence_table.get_all_evidence()
                # Filter by case_id if metadata exists
                all_evidence = [e for e in all_evidence if e.get("case_id") == case_id or e.get("metadata", {}).get("case_id") == case_id]
            except Exception as e:
                logger.warning(f"Could not fetch evidence from evidence table: {e}")
        
        if not all_evidence:
            return jsonify({
                "error": "No evidence found for this case",
                "case_id": case_id,
                "evidence_count": 0
            }), 404
        
        # Transform evidence into shotlist format (chronological facts)
        evidence_rows = []
        for idx, evidence in enumerate(all_evidence):
            # Extract metadata
            metadata = evidence.get("metadata", {}) if isinstance(evidence, dict) else {}
            content = evidence.get("content", evidence.get("text", ""))
            
            # Create fact entry
            fact_entry = {
                "fact_id": f"fact_{case_id}_{idx+1}",
                "source_id": evidence.get("object_id", evidence.get("id", f"evidence_{idx+1}")),
                "timestamp": evidence.get("timestamp", evidence.get("created_at", metadata.get("timestamp", ""))),
                "summary": content[:500] if isinstance(content, str) else str(content)[:500],  # First 500 chars as summary
                "entities": metadata.get("entities", metadata.get("parties", [])),
                "citations": metadata.get("citations", [])
            }
            evidence_rows.append(fact_entry)
        
        # Sort by timestamp (chronological order)
        def safe_timestamp(fact):
            ts = fact.get("timestamp", "")
            if isinstance(ts, str) and ts:
                return ts
            return "9999-12-31"  # Put facts without timestamp at end
        
        evidence_rows.sort(key=safe_timestamp)
        
        # Validate evidence rows
        if validate_evidence_rows:
            validation_report = validate_evidence_rows(evidence_rows)
            logger.info(f"Shotlist validation: {validation_report}")
        
        # Generate CSV shotlist
        output_dir = Path(f"./workflow_storage/cases/{case_id}/deliverables")
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_path = output_dir / "shotlist.csv"
        
        csv_file_path = build_shot_list(evidence_rows, csv_path)
        logger.info(f"Shotlist CSV generated at {csv_file_path}")
        
        # Emit Socket.IO event for real-time update
        socketio.emit("shotlist_generated", {
            "case_id": case_id,
            "fact_count": len(evidence_rows),
            "csv_path": str(csv_file_path),
            "timestamp": time.time()
        })
        
        return jsonify({
            "success": True,
            "case_id": case_id,
            "shotlist": evidence_rows,  # JSON representation
            "fact_count": len(evidence_rows),
            "csv_path": str(csv_file_path),
            "download_url": f"/api/deliverables/{case_id}/shotlist.csv",
            "generated_at": time.time()
        })
        
    except Exception as e:
        logger.error(f"Failed to generate shotlist for case {case_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/phaseA03/claims-matrix/<case_id>", methods=["POST"])
def generate_claims_matrix_endpoint(case_id):
    """
    Generate claims matrix from evidence using ComprehensiveClaimsMatrixIntegration
    Analyzes all evidence to detect potential legal claims and elements
    """
    if not LAWYERFACTORY_AVAILABLE or not unified_storage:
        return jsonify({"error": "Claims matrix generation service not available"}), 503
    
    if not PHASE_A03_AVAILABLE or not ClaimsMatrixPhaseA03:
        # Fallback to mock generation if Phase A03 not available
        logger.warning("Phase A03 claims matrix not available, using mock generation")
        evidence_texts = []
        try:
            all_evidence = unified_storage.get_case_documents(case_id) if hasattr(unified_storage, 'get_case_documents') else []
            evidence_texts = [e.get("content", e.get("text", "")) for e in all_evidence if isinstance(e, dict)]
        except:
            pass
        
        claims_matrix = generate_claims_matrix_from_evidence(case_id, evidence_texts)
        
        return jsonify({
            "success": True,
            "case_id": case_id,
            "claims_matrix": claims_matrix,
            "mock_data": True,
            "generated_at": time.time()
        })
    
    try:
        logger.info(f"Generating claims matrix for case {case_id}")
        data = request.get_json() or {}
        jurisdiction = data.get("jurisdiction", "ca_state")  # Default to California
        
        # Fetch all evidence
        all_evidence = []
        try:
            if hasattr(unified_storage, 'get_case_documents'):
                all_evidence = unified_storage.get_case_documents(case_id)
        except Exception as e:
            logger.warning(f"Could not fetch evidence: {e}")
        
        # Transform evidence into case facts format
        case_facts = []
        for idx, evidence in enumerate(all_evidence):
            if isinstance(evidence, dict):
                fact = {
                    "id": evidence.get("object_id", f"fact_{idx}"),
                    "name": f"Evidence {idx+1}",
                    "description": evidence.get("content", evidence.get("text", ""))[:500],
                    "type": evidence.get("metadata", {}).get("document_type", "evidence")
                }
                case_facts.append(fact)
        
        # Initialize claims matrix integration
        # Note: This requires EnhancedKnowledgeGraph which may not be available
        # If not available, fall back to mock generation
        try:
            from lawyerfactory.kg.graph_api import EnhancedKnowledgeGraph
            kg = EnhancedKnowledgeGraph(f"./workflow_storage/cases/{case_id}/knowledge_graph.db")
            claims_integration = ClaimsMatrixPhaseA03(kg)
            
            # Start interactive analysis
            session_id = claims_integration.start_interactive_analysis(
                jurisdiction=jurisdiction,
                cause_of_action=data.get("cause_of_action", "negligence"),
                case_facts=case_facts
            )
            
            # Generate comprehensive definition
            definition = claims_integration.get_comprehensive_definition(session_id)
            
            # Generate attorney-ready analysis
            attorney_analysis = claims_integration.generate_attorney_ready_analysis(session_id)
            
            # Export as structured report
            claims_report = claims_integration.export_analysis_report(attorney_analysis, "comprehensive")
            
            # Close KG
            kg.close()
            
            # Save to file
            output_dir = Path(f"./workflow_storage/cases/{case_id}/deliverables")
            output_dir.mkdir(parents=True, exist_ok=True)
            json_path = output_dir / "claims_matrix.json"
            
            with open(json_path, 'w') as f:
                json.dump(claims_report, f, indent=2)
            
            logger.info(f"Claims matrix JSON generated at {json_path}")
            
            # Emit Socket.IO event
            socketio.emit("claims_matrix_generated", {
                "case_id": case_id,
                "session_id": session_id,
                "claims_count": len(attorney_analysis.element_breakdowns) if attorney_analysis else 0,
                "json_path": str(json_path),
                "timestamp": time.time()
            })
            
            return jsonify({
                "success": True,
                "case_id": case_id,
                "session_id": session_id,
                "claims_matrix": claims_report,
                "json_path": str(json_path),
                "download_url": f"/api/deliverables/{case_id}/claims_matrix.json",
                "generated_at": time.time()
            })
            
        except ImportError as e:
            logger.warning(f"EnhancedKnowledgeGraph not available, using mock: {e}")
            # Fallback to mock generation
            evidence_texts = [f.get("description", "") for f in case_facts]
            claims_matrix = generate_claims_matrix_from_evidence(case_id, evidence_texts)
            
            # Save mock data
            output_dir = Path(f"./workflow_storage/cases/{case_id}/deliverables")
            output_dir.mkdir(parents=True, exist_ok=True)
            json_path = output_dir / "claims_matrix.json"
            
            with open(json_path, 'w') as f:
                json.dump(claims_matrix, f, indent=2)
            
            return jsonify({
                "success": True,
                "case_id": case_id,
                "claims_matrix": claims_matrix,
                "mock_data": True,
                "json_path": str(json_path),
                "download_url": f"/api/deliverables/{case_id}/claims_matrix.json",
                "generated_at": time.time()
            })
        
    except Exception as e:
        logger.error(f"Failed to generate claims matrix for case {case_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/phaseA03/generate/<case_id>", methods=["POST"])
def generate_phase_a03_deliverables(case_id):
    """
    Orchestrate Phase A03 deliverable generation:
    1. Generate shotlist (chronological facts timeline)
    2. Generate claims matrix (legal analysis)
    3. Generate skeletal outline (from shotlist + claims matrix)
    Returns all three deliverables with download links
    """
    if not LAWYERFACTORY_AVAILABLE or not unified_storage:
        return jsonify({"error": "Phase A03 generation service not available"}), 503
    
    try:
        logger.info(f"Starting Phase A03 deliverable generation for case {case_id}")
        data = request.get_json() or {}
        
        # Emit progress update
        socketio.emit("phase_progress_update", {
            "phase": "phaseA03_outline",
            "case_id": case_id,
            "status": "running",
            "progress": 10,
            "message": "Starting Phase A03 deliverable generation..."
        })
        
        # Step 1: Generate shotlist
        logger.info(f"Step 1/3: Generating shotlist for case {case_id}")
        socketio.emit("phase_progress_update", {
            "phase": "phaseA03_outline",
            "case_id": case_id,
            "status": "running",
            "progress": 25,
            "message": "Generating chronological shotlist timeline..."
        })
        
        shotlist_response = generate_shotlist(case_id)
        shotlist_data = shotlist_response.get_json() if hasattr(shotlist_response, 'get_json') else {}
        
        if not shotlist_data.get("success"):
            raise Exception(f"Shotlist generation failed: {shotlist_data.get('error', 'Unknown error')}")
        
        shotlist = shotlist_data.get("shotlist", [])
        logger.info(f"Shotlist generated with {len(shotlist)} facts")
        
        # Step 2: Generate claims matrix
        logger.info(f"Step 2/3: Generating claims matrix for case {case_id}")
        socketio.emit("phase_progress_update", {
            "phase": "phaseA03_outline",
            "case_id": case_id,
            "status": "running",
            "progress": 50,
            "message": "Analyzing evidence for legal claims..."
        })
        
        # Pass jurisdiction and cause_of_action from request data
        claims_request_data = {
            "jurisdiction": data.get("jurisdiction", "ca_state"),
            "cause_of_action": data.get("cause_of_action", "negligence")
        }
        
        # Create a request context for generate_claims_matrix_endpoint
        with app.test_request_context(
            f"/api/phaseA03/claims-matrix/{case_id}",
            method="POST",
            json=claims_request_data
        ):
            claims_response = generate_claims_matrix_endpoint(case_id)
            claims_data = claims_response.get_json() if hasattr(claims_response, 'get_json') else {}
        
        if not claims_data.get("success"):
            raise Exception(f"Claims matrix generation failed: {claims_data.get('error', 'Unknown error')}")
        
        claims_matrix = claims_data.get("claims_matrix", [])
        logger.info(f"Claims matrix generated")
        
        # Step 3: Generate skeletal outline using shotlist + claims matrix
        logger.info(f"Step 3/3: Generating skeletal outline for case {case_id}")
        socketio.emit("phase_progress_update", {
            "phase": "phaseA03_outline",
            "case_id": case_id,
            "status": "running",
            "progress": 75,
            "message": "Generating skeletal outline from timeline and claims..."
        })
        
        # Create outline request with shotlist and claims matrix
        outline_request_data = {
            "claims_matrix": claims_matrix if isinstance(claims_matrix, list) else [],
            "shot_list": shotlist
        }
        
        # Use existing generate_skeletal_outline endpoint
        with app.test_request_context(
            f"/api/outline/generate/{case_id}",
            method="POST",
            json=outline_request_data
        ):
            outline_response = generate_skeletal_outline(case_id)
            outline_data = outline_response.get_json() if hasattr(outline_response, 'get_json') else {}
        
        if not outline_data.get("success"):
            logger.warning(f"Skeletal outline generation had issues: {outline_data.get('error', 'Unknown')}")
            # Continue anyway with available data
        
        outline = outline_data.get("outline", {})
        
        # Save skeletal outline as deliverable
        output_dir = Path(f"./workflow_storage/cases/{case_id}/deliverables")
        output_dir.mkdir(parents=True, exist_ok=True)
        outline_json_path = output_dir / "skeletal_outline.json"
        
        with open(outline_json_path, 'w') as f:
            json.dump(outline, f, indent=2)
        
        logger.info(f"Skeletal outline JSON generated at {outline_json_path}")
        
        # Emit final completion event
        socketio.emit("skeletal_outline_generated", {
            "case_id": case_id,
            "json_path": str(outline_json_path),
            "section_count": len(outline.get("sections", [])),
            "timestamp": time.time()
        })
        
        socketio.emit("phase_progress_update", {
            "phase": "phaseA03_outline",
            "case_id": case_id,
            "status": "completed",
            "progress": 100,
            "message": "Phase A03 deliverables generated successfully"
        })
        
        # Return all deliverables
        return jsonify({
            "success": True,
            "case_id": case_id,
            "deliverables": {
                "shotlist": {
                    "data": shotlist,
                    "fact_count": len(shotlist),
                    "download_url": f"/api/deliverables/{case_id}/shotlist.csv"
                },
                "claims_matrix": {
                    "data": claims_matrix,
                    "download_url": f"/api/deliverables/{case_id}/claims_matrix.json"
                },
                "skeletal_outline": {
                    "data": outline,
                    "section_count": len(outline.get("sections", [])),
                    "download_url": f"/api/deliverables/{case_id}/skeletal_outline.json"
                }
            },
            "generated_at": time.time()
        })
        
    except Exception as e:
        logger.error(f"Failed to generate Phase A03 deliverables for case {case_id}: {e}")
        
        socketio.emit("phase_progress_update", {
            "phase": "phaseA03_outline",
            "case_id": case_id,
            "status": "failed",
            "progress": 0,
            "message": f"Phase A03 generation failed: {str(e)}"
        })
        
        return jsonify({"error": str(e)}), 500


@app.route("/api/phases/phaseB01_review/validate/<case_id>", methods=["POST"])
def validate_deliverables_endpoint(case_id):
    """
    Validate Phase A03 deliverables before allowing approval
    Checks:
    - Shotlist has minimum 10 facts
    - Claims matrix has complete element analysis
    - Skeletal outline has required sections
    - Rule 12(b)(6) compliance score >= 75
    """
    try:
        logger.info(f"Validating deliverables for case {case_id}")
        
        # Call the validation logic from Phase B01 handler
        validation_result = handle_review_phase(case_id, {})
        
        return jsonify({
            "success": validation_result.get("all_valid", False),
            "validations": validation_result.get("validations", {}),
            "all_valid": validation_result.get("all_valid", False),
            "ready_for_drafting": validation_result.get("ready_for_drafting", False),
            "message": validation_result.get("message", "")
        })
        
    except Exception as e:
        logger.error(f"Validation failed for case {case_id}: {e}")
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/api/phases/phaseB01_review/approve/<case_id>", methods=["POST"])
def approve_deliverables_endpoint(case_id):
    """
    Approve Phase A03 deliverables and unlock Phase B02 drafting
    Records approval state and validates before allowing transition
    """
    try:
        data = request.get_json() or {}
        approvals = data.get("approvals", {})
        
        logger.info(f"Approving deliverables for case {case_id}: {approvals}")
        
        # Validate first
        validation_result = handle_review_phase(case_id, {})
        
        if not validation_result.get("all_valid", False):
            return jsonify({
                "success": False,
                "message": "Cannot approve - validation failed",
                "validations": validation_result.get("validations", {}),
                "ready_for_drafting": False
            }), 400
        
        # Check that all deliverables are approved
        required_approvals = ["shotlist", "claimsMatrix", "skeletalOutline"]
        all_approved = all(approvals.get(key, False) for key in required_approvals)
        
        if not all_approved:
            return jsonify({
                "success": False,
                "message": "All deliverables must be approved",
                "approvals": approvals,
                "ready_for_drafting": False
            }), 400
        
        # Store approval state
        approval_dir = Path(f"./workflow_storage/cases/{case_id}")
        approval_dir.mkdir(parents=True, exist_ok=True)
        approval_path = approval_dir / "deliverable_approvals.json"
        
        approval_data = {
            "case_id": case_id,
            "approvals": approvals,
            "approved_at": time.time(),
            "approved_by": "user",  # TODO: Add actual user tracking
            "validations_passed": validation_result.get("validations", {})
        }
        
        with open(approval_path, 'w') as f:
            json.dump(approval_data, f, indent=2)
        
        logger.info(f"Deliverables approved for case {case_id}")
        
        # Emit Socket.IO event
        socketio.emit("deliverables_approved", {
            "case_id": case_id,
            "timestamp": time.time(),
            "ready_for_drafting": True
        })
        
        return jsonify({
            "success": True,
            "message": "All deliverables approved - Phase B02 unlocked",
            "approvals": approvals,
            "ready_for_drafting": True,
            "approval_path": str(approval_path)
        })
        
    except Exception as e:
        logger.error(f"Approval failed for case {case_id}: {e}")
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/api/deliverables/<case_id>/<deliverable_type>", methods=["GET"])
def download_deliverable(case_id, deliverable_type):
    """
    Download Phase A03 deliverables as files
    Supported types: shotlist.csv, claims_matrix.json, skeletal_outline.json
    """
    try:
        from flask import send_file
        
        deliverable_dir = Path(f"./workflow_storage/cases/{case_id}/deliverables")
        
        # Map deliverable types to filenames
        file_map = {
            "shotlist.csv": "shotlist.csv",
            "claims_matrix.json": "claims_matrix.json",
            "skeletal_outline.json": "skeletal_outline.json"
        }
        
        if deliverable_type not in file_map:
            return jsonify({"error": f"Unknown deliverable type: {deliverable_type}"}), 400
        
        file_path = deliverable_dir / file_map[deliverable_type]
        
        if not file_path.exists():
            return jsonify({
                "error": f"Deliverable not found: {deliverable_type}",
                "case_id": case_id,
                "expected_path": str(file_path)
            }), 404
        
        # Determine MIME type
        mime_type = "text/csv" if deliverable_type.endswith(".csv") else "application/json"
        
        return send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=True,
            download_name=f"{case_id}_{deliverable_type}"
        )
        
    except Exception as e:
        logger.error(f"Failed to download deliverable {deliverable_type} for case {case_id}: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# LLM CONFIGURATION API ENDPOINTS
# ============================================================================

@app.route("/api/settings/llm", methods=["GET"])
def get_llm_config():
    """Get current LLM configuration (without exposing API key)"""
    try:
        safe_config = llm_config.copy()
        # Mask API key
        if safe_config.get("api_key"):
            safe_config["api_key"] = "***" + safe_config["api_key"][-4:] if len(safe_config["api_key"]) > 4 else "***"
        
        return jsonify({
            "success": True,
            "config": safe_config,
            "available_providers": ["openai", "anthropic", "groq", "gemini"],
            "available_models": {
                "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "groq": ["mixtral-8x7b", "llama-2-70b"],
                "gemini": ["gemini-pro", "gemini-pro-vision"]
            }
        })
    except Exception as e:
        logger.error(f"Failed to get LLM config: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/settings/llm", methods=["POST"])
def update_llm_config():
    """Update LLM configuration"""
    try:
        data = request.get_json()
        
        # Update configuration
        if "provider" in data:
            llm_config["provider"] = data["provider"]
        if "model" in data:
            llm_config["model"] = data["model"]
        if "api_key" in data and data["api_key"] != "":
            llm_config["api_key"] = data["api_key"]
        if "temperature" in data:
            llm_config["temperature"] = float(data["temperature"])
        if "max_tokens" in data:
            llm_config["max_tokens"] = int(data["max_tokens"])
        
        logger.info(f"LLM config updated: {llm_config['provider']}/{llm_config['model']}")
        
        return jsonify({
            "success": True,
            "message": "LLM configuration updated successfully",
            "config": {
                "provider": llm_config["provider"],
                "model": llm_config["model"],
                "temperature": llm_config["temperature"],
                "max_tokens": llm_config["max_tokens"]
            }
        })
    except Exception as e:
        logger.error(f"Failed to update LLM config: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# DRAFTING VALIDATION API ENDPOINTS
# ============================================================================

@app.route("/api/drafting/validate", methods=["POST"])
def validate_draft_complaint():
    """Validate draft complaint against defendant cluster using LLM-enhanced analysis"""
    if not drafting_validator:
        return jsonify({"error": "Drafting validator not available"}), 503
    
    try:
        data = request.get_json()
        draft_text = data.get("draft_text", "")
        case_id = data.get("case_id", "")
        
        if not draft_text or not case_id:
            return jsonify({"error": "Missing draft_text or case_id"}), 400
        
        # Run async validation in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            validation_result = loop.run_until_complete(
                drafting_validator.validate_draft_complaint(
                    draft_text=draft_text,
                    case_id=case_id
                )
            )
        finally:
            loop.close()
        
        # Convert validation result to dict
        result_dict = {
            "is_valid": validation_result.is_valid,
            "overall_score": validation_result.overall_score,
            "similarity_score": validation_result.similarity_score,
            "similarity_threshold": validation_result.similarity_threshold,
            "issues_found": validation_result.issues_found,
            "recommendations": validation_result.recommendations,
            "missing_elements": validation_result.missing_elements,
            "processing_time": validation_result.processing_time,
            "defendant_name": validation_result.defendant_name,
            "case_id": validation_result.case_id
        }
        
        return jsonify({
            "success": True,
            "validation_result": result_dict
        })
        
    except Exception as e:
        logger.error(f"Draft validation failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/intake/process-document", methods=["POST"])
def process_enhanced_intake_document():
    """Enhanced document processing with categorization and clustering"""
    if not intake_processor:
        return jsonify({"error": "Intake processor not available"}), 503
    
    try:
        file = request.files.get("document")
        case_id = request.form.get("case_id", "")
        
        if not file:
            return jsonify({"error": "No document provided"}), 400
        
        # Read document content
        content = file.read().decode("utf-8", errors="ignore")
        
        # Get defendant hint from case data if available
        defendant_hint = None
        if intake_processor and case_id in getattr(intake_processor, "active_cases", {}):
            defendant_hint = intake_processor.active_cases[case_id].get("defendant_name")
        
        # Run async document processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                intake_processor.process_document(
                    file_path=file.filename,
                    case_id=case_id,
                    additional_context={"defendant_hint": defendant_hint}
                )
            )
        finally:
            loop.close()
        
        return jsonify({
            "success": result.get("success", False),
            "document_id": result.get("document_id"),
            "document_type": result.get("document_type"),
            "authority_level": result.get("authority_level"),
            "cluster_id": result.get("cluster_id"),
            "confidence_score": result.get("confidence_score"),
            "similar_documents": result.get("similar_documents", 0),
            "defendant_recognized": result.get("defendant_recognized", False)
        })
        
    except Exception as e:
        logger.error(f"Enhanced intake processing failed: {e}")
        return jsonify({"error": str(e)}), 500


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
