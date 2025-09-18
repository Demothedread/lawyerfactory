"""
Shot List API - Backend implementation for shot list generation
Provides REST API endpoints for generating shot lists from evidence data
"""

from datetime import datetime
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request
from flask_socketio import emit

from ..storage.enhanced_unified_storage_api import get_enhanced_unified_storage_api
from ..storage.evidence.shotlist import ShotlistBuilder, build_shotlist_from_facts_matrix

logger = logging.getLogger(__name__)

# Create Flask Blueprint for shot list API
shot_list_bp = Blueprint("shot_list", __name__, url_prefix="/api/shot_list")


@shot_list_bp.route("/generate", methods=["POST"])
def generate_shot_list():
    """
    Generate a shot list from evidence data

    Expected JSON payload:
    {
        "evidence_data": {...},  # Evidence references from facts matrix
        "output_directory": "optional/path",  # Optional output directory
        "case_id": "optional_case_id"  # Optional case identifier
    }

    Returns:
    {
        "success": true/false,
        "output_file": "path/to/generated/shotlist.csv",
        "evidence_count": number,
        "statistics": {...},
        "error": "error message if failed"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400

        evidence_data = data.get("evidence_data", {})
        output_directory = data.get("output_directory")
        case_id = data.get("case_id", "unknown")

        if not evidence_data:
            return jsonify({"success": False, "error": "No evidence data provided"}), 400

        # Create shot list builder
        builder = ShotlistBuilder(output_directory)

        # Generate shot list
        result = builder.build(evidence_data)

        # Emit real-time update via Socket.IO if successful
        if result.get("success"):
            emit(
                "shot_list_generated",
                {
                    "case_id": case_id,
                    "output_file": result["output_file"],
                    "evidence_count": result["evidence_count"],
                    "timestamp": result.get("timestamp"),
                },
                broadcast=True,
            )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Failed to generate shot list: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@shot_list_bp.route("/from_facts_matrix", methods=["POST"])
def generate_from_facts_matrix():
    """
    Generate shot list directly from a complete facts matrix

    Expected JSON payload:
    {
        "facts_matrix": {...},  # Complete facts matrix
        "output_directory": "optional/path",  # Optional output directory
        "case_id": "optional_case_id"  # Optional case identifier
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400

        facts_matrix = data.get("facts_matrix", {})
        output_directory = data.get("output_directory")
        case_id = data.get("case_id", "unknown")

        if not facts_matrix:
            return jsonify({"success": False, "error": "No facts matrix provided"}), 400

        # Generate shot list from facts matrix
        result = build_shotlist_from_facts_matrix(facts_matrix, output_directory)

        # Emit real-time update via Socket.IO if successful
        if result.get("success"):
            emit(
                "shot_list_generated",
                {
                    "case_id": case_id,
                    "output_file": result["output_file"],
                    "evidence_count": result["evidence_count"],
                    "timestamp": result.get("timestamp"),
                },
                broadcast=True,
            )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Failed to generate shot list from facts matrix: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@shot_list_bp.route("/validate", methods=["POST"])
def validate_evidence_data():
    """
    Validate evidence data structure before generating shot list

    Expected JSON payload:
    {
        "evidence_data": {...}  # Evidence data to validate
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400

        evidence_data = data.get("evidence_data", {})

        # Create builder and validate
        builder = ShotlistBuilder()
        validation_report = builder.validate_evidence_data(evidence_data)

        return jsonify({"success": True, "validation_report": validation_report})

    except Exception as e:
        logger.error(f"Failed to validate evidence data: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@shot_list_bp.route("/from_storage", methods=["POST"])
def generate_from_storage():
    """
    Generate shot list from evidence stored in unified storage system

    Expected JSON payload:
    {
        "case_id": "case_identifier",  # Case to search evidence for
        "evidence_filter": {...},  # Optional filters for evidence search
        "output_directory": "optional/path"  # Optional output directory
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400

        case_id = data.get("case_id", "")
        evidence_filter = data.get("evidence_filter", {})
        output_directory = data.get("output_directory")

        if not case_id:
            return jsonify({"success": False, "error": "Case ID is required"}), 400

        # Get unified storage API
        storage_api = get_enhanced_unified_storage_api()

        # Search for evidence related to the case
        search_query = f"case:{case_id}"
        evidence_results = await storage_api.search_evidence(search_query, "all")

        # Convert storage results to evidence data format
        evidence_data = {}
        for i, evidence in enumerate(evidence_results):
            evidence_id = f"storage_{evidence.get('object_id', i)}"
            evidence_data[evidence_id] = {
                "fact_id": evidence.get("object_id", f"fact_{i}"),
                "source_id": evidence.get("metadata", {}).get("source_file", "unknown"),
                "timestamp": evidence.get("metadata", {}).get("created_at", ""),
                "summary": evidence.get("content", "")[:500],  # Truncate for summary
                "entities": evidence.get("metadata", {}).get("entities", []),
                "citations": evidence.get("metadata", {}).get("citations", []),
            }

        if not evidence_data:
            return (
                jsonify({"success": False, "error": f"No evidence found for case ID: {case_id}"}),
                404,
            )

        # Generate shot list
        builder = ShotlistBuilder(output_directory)
        result = builder.build(evidence_data)

        # Add case information to result
        result["case_id"] = case_id
        result["evidence_source"] = "unified_storage"

        # Emit real-time update via Socket.IO if successful
        if result.get("success"):
            emit(
                "shot_list_generated",
                {
                    "case_id": case_id,
                    "output_file": result["output_file"],
                    "evidence_count": result["evidence_count"],
                    "timestamp": result.get("timestamp"),
                    "source": "unified_storage",
                },
                broadcast=True,
            )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Failed to generate shot list from storage: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@shot_list_bp.route("/status/<path:filename>", methods=["GET"])
def get_shot_list_status(filename: str):
    """
    Get status information about a generated shot list file

    Args:
        filename: Name of the shot list file to check

    Returns:
        Status information about the file
    """
    try:
        file_path = Path(filename)

        if not file_path.exists():
            return jsonify({"exists": False, "error": "File not found"}), 404

        # Get file statistics
        stat = file_path.stat()

        return jsonify(
            {
                "exists": True,
                "filename": file_path.name,
                "size_bytes": stat.st_size,
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_readable": file_path.is_file() and file_path.stat().st_mode & 0o444,
            }
        )

    except Exception as e:
        logger.error(f"Failed to get shot list status: {e}")
        return jsonify({"exists": False, "error": str(e)}), 500


@shot_list_bp.route("/list", methods=["GET"])
def list_shot_lists():
    """
    List all generated shot list files in the default output directory

    Query parameters:
        - output_dir: Optional directory to search (defaults to current directory)
        - pattern: Optional filename pattern to match (defaults to "shot_list_*.csv")
    """
    try:
        output_dir = request.args.get("output_dir", ".")
        pattern = request.args.get("pattern", "shot_list_*.csv")

        search_path = Path(output_dir)

        if not search_path.exists():
            return jsonify({"success": False, "error": f"Directory not found: {output_dir}"}), 404

        # Find matching files
        shot_list_files = []
        for file_path in search_path.glob(pattern):
            if file_path.is_file():
                stat = file_path.stat()
                shot_list_files.append(
                    {
                        "filename": file_path.name,
                        "full_path": str(file_path),
                        "size_bytes": stat.st_size,
                        "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    }
                )

        # Sort by creation time (newest first)
        shot_list_files.sort(key=lambda x: x["created_time"], reverse=True)

        return jsonify(
            {
                "success": True,
                "shot_lists": shot_list_files,
                "total_count": len(shot_list_files),
                "search_directory": str(search_path),
                "search_pattern": pattern,
            }
        )

    except Exception as e:
        logger.error(f"Failed to list shot lists: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# Socket.IO event handlers for real-time shot list updates
def register_shot_list_events(socketio):
    """
    Register Socket.IO event handlers for shot list functionality

    Args:
        socketio: Flask-SocketIO instance
    """

    @socketio.on("request_shot_list_generation")
    def handle_shot_list_request(data):
        """Handle real-time shot list generation requests"""
        try:
            evidence_data = data.get("evidence_data", {})
            case_id = data.get("case_id", "unknown")
            output_directory = data.get("output_directory")

            if not evidence_data:
                emit("shot_list_error", {"case_id": case_id, "error": "No evidence data provided"})
                return

            # Generate shot list
            builder = ShotlistBuilder(output_directory)
            result = builder.build(evidence_data)

            if result.get("success"):
                emit(
                    "shot_list_generated",
                    {
                        "case_id": case_id,
                        "output_file": result["output_file"],
                        "evidence_count": result["evidence_count"],
                        "statistics": result["statistics"],
                        "timestamp": result.get("timestamp"),
                    },
                )
            else:
                emit(
                    "shot_list_error",
                    {"case_id": case_id, "error": result.get("error", "Unknown error")},
                )

        except Exception as e:
            logger.error(f"Socket.IO shot list generation failed: {e}")
            emit("shot_list_error", {"case_id": data.get("case_id", "unknown"), "error": str(e)})

    @socketio.on("request_shot_list_status")
    def handle_shot_list_status_request(data):
        """Handle real-time shot list status requests"""
        try:
            filename = data.get("filename", "")

            if not filename:
                emit("shot_list_status_error", {"error": "Filename required"})
                return

            file_path = Path(filename)

            if file_path.exists():
                stat = file_path.stat()
                emit(
                    "shot_list_status",
                    {
                        "filename": file_path.name,
                        "exists": True,
                        "size_bytes": stat.st_size,
                        "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    },
                )
            else:
                emit("shot_list_status", {"filename": filename, "exists": False})

        except Exception as e:
            logger.error(f"Socket.IO shot list status failed: {e}")
            emit("shot_list_status_error", {"error": str(e)})


# Function to register the blueprint with a Flask app
def register_shot_list_api(app, socketio=None):
    """
    Register shot list API with Flask app and Socket.IO

    Args:
        app: Flask application instance
        socketio: Optional Flask-SocketIO instance for real-time features
    """
    app.register_blueprint(shot_list_bp)

    if socketio:
        register_shot_list_events(socketio)

    logger.info("Shot list API registered successfully")
