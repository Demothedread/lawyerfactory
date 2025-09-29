#!/usr/bin/env python3
"""
Simplified LawyerFactory API Server for Briefcaser Integration
Basic Flask server with mock responses for frontend testing and unified storage integration
"""

import json
import logging
import os
from pathlib import Path
import sys
import time

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src path for LawyerFactory imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from lawyerfactory.storage.enhanced_unified_storage_api import get_enhanced_unified_storage_api

    UNIFIED_STORAGE_AVAILABLE = True
    logger.info("✓ Unified storage API loaded successfully")
except ImportError as e:
    logger.warning(f"Unified storage not available: {e}")
    UNIFIED_STORAGE_AVAILABLE = False

# Create Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = "briefcaser-test-key"
CORS(app, origins=["*"])

# Create Socket.IO server
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Mock data stores
mock_cases = {}
mock_research_status = {}
mock_outline_status = {}

# Initialize unified storage if available
unified_storage = None
if UNIFIED_STORAGE_AVAILABLE:
    try:
        unified_storage = get_enhanced_unified_storage_api()
        logger.info("✓ Unified storage initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize unified storage: {e}")
        unified_storage = None


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "message": "Briefcaser API server is running",
            "timestamp": time.time(),
            "version": "1.0.0",
        }
    )


@app.route("/api/intake", methods=["POST"])
def process_intake():
    """Process legal intake form"""
    try:
        data = request.get_json()

        # Generate case ID
        case_id = f"case_{int(time.time())}"

        # Store case data
        mock_cases[case_id] = {
            "case_id": case_id,
            "client_name": data.get("clientName", ""),
            "other_party": data.get("otherPartyName", ""),
            "claim_description": data.get("claimDescription", ""),
            "created_at": time.time(),
            "status": "intake_complete",
        }

        # Emit progress update
        socketio.emit(
            "phase_progress_update",
            {
                "phase": "A01_Intake",
                "progress": 100,
                "message": f"Case {case_id} created successfully",
            },
        )

        logger.info(f"Created case: {case_id}")

        return jsonify(
            {
                "success": True,
                "case_id": case_id,
                "message": "Case created successfully",
                "case": mock_cases[case_id],
            }
        )

    except Exception as e:
        logger.error(f"Intake processing failed: {e}")
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


@app.route("/api/cases/<case_id>/documents", methods=["POST"])
def upload_documents(case_id):
    """Upload documents for a case (legacy endpoint with mock storage)"""
    try:
        files = request.files.getlist("files")

        if case_id not in mock_cases:
            return jsonify({"error": "Case not found"}), 404

        # Process uploaded files
        processed_docs = []
        for file in files:
            doc_info = {
                "filename": file.filename,
                "size": len(file.read()),
                "content_type": file.content_type,
                "uploaded_at": time.time(),
            }
            processed_docs.append(doc_info)

        # Update case with documents
        if "documents" not in mock_cases[case_id]:
            mock_cases[case_id]["documents"] = []
        mock_cases[case_id]["documents"].extend(processed_docs)

        # Emit progress update
        socketio.emit(
            "phase_progress_update",
            {
                "phase": "A01_Intake",
                "progress": 100,
                "message": f"Processed {len(processed_docs)} documents for case {case_id}",
            },
        )

        logger.info(f"Uploaded {len(processed_docs)} documents to case {case_id}")

        return jsonify(
            {
                "success": True,
                "case_id": case_id,
                "processed_documents": processed_docs,
                "message": f"Uploaded {len(processed_docs)} documents",
            }
        )

    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/research/start", methods=["POST"])
def start_research():
    """Start research phase"""
    try:
        data = request.get_json()
        case_id = data.get("case_id")
        research_query = data.get("research_query", "")

        if not case_id:
            return jsonify({"error": "Case ID required"}), 400

        if case_id not in mock_cases:
            return jsonify({"error": "Case not found"}), 404

        # Start research process
        mock_research_status[case_id] = {
            "status": "running",
            "progress": 10,
            "message": "Initializing research...",
        }

        # Emit initial progress
        socketio.emit(
            "phase_progress_update",
            {"phase": "A02_Research", "progress": 10, "message": "Research initialized"},
        )

        # Simulate research progress
        def simulate_research():
            import threading

            def progress_updates():
                time.sleep(2)
                mock_research_status[case_id] = {
                    "status": "running",
                    "progress": 50,
                    "message": "Analyzing legal precedents...",
                }
                socketio.emit(
                    "phase_progress_update",
                    {
                        "phase": "A02_Research",
                        "progress": 50,
                        "message": "Analyzing legal precedents...",
                    },
                )

                time.sleep(3)
                mock_research_status[case_id] = {
                    "status": "completed",
                    "progress": 100,
                    "message": "Research completed",
                }
                socketio.emit(
                    "phase_progress_update",
                    {
                        "phase": "A02_Research",
                        "progress": 100,
                        "message": "Research completed with 5 sources found",
                    },
                )

            threading.Thread(target=progress_updates).start()

        simulate_research()

        logger.info(f"Started research for case {case_id}")

        return jsonify({"success": True, "case_id": case_id, "message": "Research started"})

    except Exception as e:
        logger.error(f"Research start failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/research/status/<case_id>", methods=["GET"])
def get_research_status(case_id):
    """Get research status"""
    try:
        status = mock_research_status.get(
            case_id, {"status": "not_started", "progress": 0, "message": "Research not yet started"}
        )

        return jsonify(
            {
                "case_id": case_id,
                "status": status.get("status"),
                "progress": status.get("progress"),
                "message": status.get("message"),
            }
        )

    except Exception as e:
        logger.error(f"Research status check failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/outline/generate", methods=["POST"])
def generate_outline():
    """Generate document outline"""
    try:
        data = request.get_json()
        case_id = data.get("case_id")

        if not case_id:
            return jsonify({"error": "Case ID required"}), 400

        if case_id not in mock_cases:
            return jsonify({"error": "Case not found"}), 404

        # Start outline generation
        mock_outline_status[case_id] = {
            "status": "running",
            "progress": 10,
            "message": "Initializing outline generation...",
        }

        # Emit initial progress
        socketio.emit(
            "phase_progress_update",
            {"phase": "A03_Outline", "progress": 10, "message": "Outline generation initialized"},
        )

        # Simulate outline generation
        def simulate_outline():
            import threading

            def progress_updates():
                time.sleep(2)
                mock_outline_status[case_id] = {
                    "status": "running",
                    "progress": 75,
                    "message": "Generating document structure...",
                }
                socketio.emit(
                    "phase_progress_update",
                    {
                        "phase": "A03_Outline",
                        "progress": 75,
                        "message": "Generating document structure...",
                    },
                )

                time.sleep(3)
                mock_outline_status[case_id] = {
                    "status": "completed",
                    "progress": 100,
                    "message": "Outline completed",
                }
                socketio.emit(
                    "phase_progress_update",
                    {
                        "phase": "A03_Outline",
                        "progress": 100,
                        "message": "Outline generated with 7 sections",
                    },
                )

            threading.Thread(target=progress_updates).start()

        simulate_outline()

        logger.info(f"Started outline generation for case {case_id}")

        return jsonify(
            {"success": True, "case_id": case_id, "message": "Outline generation started"}
        )

    except Exception as e:
        logger.error(f"Outline generation failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/outline/status/<case_id>", methods=["GET"])
def get_outline_status(case_id):
    """Get outline generation status"""
    try:
        status = mock_outline_status.get(
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
                "status": status.get("status"),
                "progress": status.get("progress"),
                "message": status.get("message"),
            }
        )

    except Exception as e:
        logger.error(f"Outline status check failed: {e}")
        return jsonify({"error": str(e)}), 500


# Socket.IO event handlers
@socketio.on("connect")
def handle_connect():
    logger.info("Client connected via Socket.IO")
    emit("status", {"message": "Connected to Briefcaser API"})


@socketio.on("disconnect")
def handle_disconnect():
    logger.info("Client disconnected from Socket.IO")


if __name__ == "__main__":
    logger.info("🚀 Starting Briefcaser API server...")
    logger.info("📡 Socket.IO enabled for real-time updates")
    logger.info("🌐 CORS enabled for all origins")

    # Run the server
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True,
        use_reloader=False,  # Disable reloader for background compatibility
    )
