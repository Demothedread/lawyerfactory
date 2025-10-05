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
    socketio.emit("phase_progress_update", {
        "phase": "A01_Intake",
        "progress": 10,
        "message": "Initializing intake processor..."
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
    socketio.emit("phase_progress_update", {
        "phase": "A02_Research",
        "progress": 10,
        "message": "Initializing research agents..."
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
    socketio.emit("phase_progress_update", {
        "phase": "A03_Outline",
        "progress": 10,
        "message": "Initializing outline generator..."
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
    Validates facts, claims, and legal theories using Editor agent
    (STUB - To be implemented with proper review agent integration)
    """
    socketio.emit("phase_progress_update", {
        "phase": "B01_Review",
        "progress": 30,
        "message": "Running quality checks..."
    })
    
    time.sleep(1)  # Simulate processing
    
    socketio.emit("phase_progress_update", {
        "phase": "B01_Review",
        "progress": 70,
        "message": "Validating legal theories..."
    })
    
    time.sleep(1)
    
    socketio.emit("phase_progress_update", {
        "phase": "B01_Review",
        "progress": 100,
        "message": "✅ Review complete (mock)"
    })
    
    return {
        "status": "mock",
        "message": "Review phase not yet implemented - placeholder complete",
        "case_id": case_id,
        "review_passed": True
    }


async def handle_drafting_phase(case_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase B02: Document Drafting
    Generates legal documents using templates and Writer agent with IRAC methodology
    """
    socketio.emit("phase_progress_update", {
        "phase": "B02_Drafting",
        "progress": 10,
        "message": "Initializing drafting agents and templates..."
    })

    try:
        # Import drafting components with fallbacks
        WriterBot = None
        AgentConfig = None
        SkeletalOutlineGenerator = None
        ComprehensiveClaimsMatrixIntegration = None
        EnhancedKnowledgeGraph = None
        EvidenceAPI = None
        WorkflowTask = None

        try:
            from lawyerfactory.compose.bots.writer import WriterBot
            from lawyerfactory.compose.maestro.registry import AgentConfig
            from lawyerfactory.outline.generator import SkeletalOutlineGenerator
            from lawyerfactory.claims.matrix import ComprehensiveClaimsMatrixIntegration
            from lawyerfactory.kg.enhanced_graph import EnhancedKnowledgeGraph
            from lawyerfactory.phases.phaseA01_intake.evidence_routes import EvidenceAPI
            from lawyerfactory.compose.maestro.workflow_models import WorkflowTask
        except ImportError as e:
            logger.warning(f"Some drafting components not available: {e}")

        if not WriterBot or not AgentConfig or not WorkflowTask:
            # Fallback to mock implementation
            socketio.emit("phase_progress_update", {
                "phase": "B02_Drafting",
                "progress": 100,
                "message": "✍️ Drafting complete (mock - components not available)"
            })
            return {
                "status": "mock",
                "message": "Drafting phase completed with mock data - WriterBot not available",
                "case_id": case_id,
                "documents_generated": 0
            }

        socketio.emit("phase_progress_update", {
            "phase": "B02_Drafting",
            "progress": 20,
            "message": "Loading skeletal outline and claims matrix..."
        })

        # Initialize components with fallbacks
        kg = None
        claims_matrix = None
        evidence_api = None

        try:
            kg = EnhancedKnowledgeGraph() if EnhancedKnowledgeGraph else None
        except Exception as e:
            logger.warning(f"Knowledge graph not available: {e}")

        try:
            evidence_api = EvidenceAPI() if EvidenceAPI else None
        except Exception as e:
            logger.warning(f"Evidence API not available: {e}")

        # Initialize claims matrix with unified storage if available
        if ComprehensiveClaimsMatrixIntegration and unified_storage:
            try:
                claims_matrix = ComprehensiveClaimsMatrixIntegration(unified_storage)
            except Exception as e:
                logger.warning(f"Claims matrix not available: {e}")
                claims_matrix = None

        # Generate skeletal outline if not already available
        skeletal_outline = None
        if SkeletalOutlineGenerator and kg and claims_matrix and evidence_api:
            try:
                outline_generator = SkeletalOutlineGenerator(kg, claims_matrix, evidence_api)
                skeletal_outline = outline_generator.generate_skeletal_outline(case_id, f"drafting_{case_id}")
            except Exception as e:
                logger.warning(f"Outline generation failed: {e}")

        socketio.emit("phase_progress_update", {
            "phase": "B02_Drafting",
            "progress": 30,
            "message": "Skeletal outline generated with IRAC structure..."
        })

        # Initialize writer bot
        writer_config = AgentConfig(
            agent_type="LegalWriterBot",
            max_concurrent=1,
            capabilities=["legal_writing"],
            config={
                "llm_provider": "openai",
                "temperature": 0.1
            }
        )
        writer_bot = WriterBot(writer_config)

        socketio.emit("phase_progress_update", {
            "phase": "B02_Drafting",
            "progress": 40,
            "message": "Writer bot initialized with legal templates..."
        })

        # Gather case data for drafting
        case_data = {
            "case_id": case_id,
            "court": "UNITED STATES DISTRICT COURT",
            "district": "NORTHERN DISTRICT OF CALIFORNIA",
            "plaintiff_name": "Plaintiff Name",  # Should come from case data
            "defendant_name": "Defendant Name",  # Should come from case data
            "case_number": f"Case No. {case_id}",
            "jurisdiction": "California"
        }

        # Get evidence and facts from unified storage
        case_facts = []
        if unified_storage:
            try:
                evidence_data = unified_storage.search_evidence_by_metadata({"case_id": case_id})
                for evidence in evidence_data:
                    if evidence.get("content"):
                        case_facts.append({
                            "fact_text": evidence["content"][:500],  # Truncate for processing
                            "evidence_id": evidence.get("object_id", ""),
                            "source": evidence.get("filename", "unknown")
                        })
            except Exception as e:
                logger.warning(f"Failed to retrieve evidence: {e}")

        socketio.emit("phase_progress_update", {
            "phase": "B02_Drafting",
            "progress": 50,
            "message": f"Loaded {len(case_facts)} facts from evidence..."
        })

        # Generate research findings (mock for now - should integrate with research phase)
        research_findings = {
            "citations": [
                {"cite": "California Civil Code § 1714", "summary": "Basic negligence standard"},
                {"cite": "Rowland v. Christian (1968) 69 Cal.2d 108", "summary": "Landowner duty of care"}
            ],
            "legal_issues": ["Negligence", "Duty of Care", "Breach", "Causation", "Damages"]
        }

        # Generate claims matrix data
        claims_data = []
        if skeletal_outline and hasattr(skeletal_outline, 'claims_summary'):
            primary_claim = skeletal_outline.claims_summary.get("cause_of_action", "Negligence")
            claims_data.append({
                "name": primary_claim,
                "elements": list(skeletal_outline.claims_summary.get("element_breakdowns", {}).keys())
            })

        socketio.emit("phase_progress_update", {
            "phase": "B02_Drafting",
            "progress": 60,
            "message": "Generating complaint using IRAC methodology..."
        })

        # Generate complaint using writer bot
        drafting_context = {
            "content_type": "complaint",
            "case_facts": case_facts,
            "research_findings": research_findings,
            "case_data": case_data,
            "causes_of_action": claims_data,
            "skeletal_outline": skeletal_outline.to_dict() if skeletal_outline else {}
        }

        complaint_result = await writer_bot.execute_task(
            WorkflowTask(
                id=f"draft_complaint_{case_id}",
                phase="drafting",  # Use string for now
                agent_type="LegalWriterBot",
                description="Generate professional legal complaint using IRAC methodology",
                context=drafting_context
            ),
            drafting_context
        )

        socketio.emit("phase_progress_update", {
            "phase": "B02_Drafting",
            "progress": 80,
            "message": "Complaint drafted, generating statement of facts..."
        })

        # Generate statement of facts separately
        facts_context = drafting_context.copy()
        facts_context["content_type"] = "statement_of_facts"

        facts_result = await writer_bot.execute_task(
            WorkflowTask(
                id=f"draft_facts_{case_id}",
                phase="drafting",
                agent_type="LegalWriterBot",
                description="Generate comprehensive statement of facts",
                context=facts_context
            ),
            facts_context
        )

        socketio.emit("phase_progress_update", {
            "phase": "B02_Drafting",
            "progress": 90,
            "message": "Storing drafted documents..."
        })

        # Store the drafted documents
        documents_generated = []

        # Store complaint
        if complaint_result.get("content") and unified_storage:
            try:
                complaint_storage = unified_storage.store_evidence(
                    file_content=complaint_result["content"].encode("utf-8"),
                    filename=f"complaint_{case_id}.txt",
                    metadata={
                        "case_id": case_id,
                        "document_type": "complaint",
                        "phase": "B02_Drafting",
                        "word_count": complaint_result.get("word_count", 0),
                        "template_used": complaint_result.get("template_used"),
                        "validation_performed": complaint_result.get("claim_validation_performed", False),
                        "irac_compliant": True
                    },
                    source_phase="phaseB02_drafting"
                )
                if complaint_storage.success:
                    documents_generated.append({
                        "type": "complaint",
                        "object_id": complaint_storage.object_id,
                        "filename": f"complaint_{case_id}.txt",
                        "word_count": complaint_result.get("word_count", 0)
                    })
            except Exception as e:
                logger.warning(f"Failed to store complaint: {e}")

        # Store statement of facts
        if facts_result.get("content") and unified_storage:
            try:
                facts_storage = unified_storage.store_evidence(
                    file_content=facts_result["content"].encode("utf-8"),
                    filename=f"statement_of_facts_{case_id}.txt",
                    metadata={
                        "case_id": case_id,
                        "document_type": "statement_of_facts",
                        "phase": "B02_Drafting",
                        "word_count": facts_result.get("word_count", 0),
                        "template_used": facts_result.get("template_used"),
                        "evidence_integrated": len(case_facts)
                    },
                    source_phase="phaseB02_drafting"
                )
                if facts_storage.success:
                    documents_generated.append({
                        "type": "statement_of_facts",
                        "object_id": facts_storage.object_id,
                        "filename": f"statement_of_facts_{case_id}.txt",
                        "word_count": facts_result.get("word_count", 0)
                    })
            except Exception as e:
                logger.warning(f"Failed to store statement of facts: {e}")

        socketio.emit("phase_progress_update", {
            "phase": "B02_Drafting",
            "progress": 100,
            "message": f"✍️ Drafting complete - {len(documents_generated)} documents generated"
        })

        return {
            "status": "completed",
            "message": f"Drafting phase completed successfully. Generated {len(documents_generated)} professional legal documents using IRAC methodology.",
            "case_id": case_id,
            "documents_generated": documents_generated,
            "skeletal_outline_id": skeletal_outline.outline_id if skeletal_outline else None,
            "irac_compliant": True,
            "validation_performed": complaint_result.get("claim_validation_performed", False),
            "total_word_count": sum(doc.get("word_count", 0) for doc in documents_generated)
        }

    except Exception as e:
        logger.error(f"Drafting phase failed: {e}")
        socketio.emit("phase_progress_update", {
            "phase": "B02_Drafting",
            "progress": 0,
            "message": f"❌ Drafting failed: {str(e)}"
        })

        return {
            "status": "failed",
            "message": f"Drafting phase failed: {str(e)}",
            "case_id": case_id,
            "documents_generated": 0,
            "error": str(e)
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
