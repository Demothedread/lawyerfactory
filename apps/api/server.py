#!/usr/bin/env python3
"""
LawyerFactory Backend Server
Provides Socket.IO and REST API endpoints for the MultiSWARM UI
Enhanced with terminal interface support and real-time updates
"""

# Monkey patch must be done before any other imports
import eventlet

eventlet.monkey_patch()

import argparse
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LawyerFactoryServer:
    """Main server class for LawyerFactory backend"""

    def __init__(self):
        self.app = Flask(__name__, template_folder="../ui/templates", static_folder="../ui/static")
        CORS(self.app)

        # Initialize Socket.IO with CORS
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            async_mode="eventlet",
            logger=True,
            engineio_logger=True,
        )

        # Server state
        self.active_cases = {}
        self.agent_status = {
            "intake_agent": {"status": "idle", "progress": 0},
            "research_agent": {"status": "idle", "progress": 0},
            "drafting_agent": {"status": "idle", "progress": 0},
            "review_agent": {"status": "idle", "progress": 0},
            "orchestration_agent": {"status": "idle", "progress": 0},
        }

        self.phase_progress = {
            "A01_Intake": 0,
            "A02_Research": 0,
            "A03_Outline": 0,
            "B01_Review": 0,
            "B02_Drafting": 0,
            "C01_Editing": 0,
            "C02_Orchestration": 0,
        }

        self.case_packets = []
        self.notifications = []
        self.system_metrics = {
            "cpu_usage": 0,
            "memory_usage": 0,
            "network_usage": 0,
            "active_connections": 0,
            "uptime": 0,
        }
        self.terminal_logs = []

        self.setup_routes()
        self.setup_socket_events()

    def setup_routes(self):
        """Setup REST API routes"""

        @self.app.route("/")
        def index():
            """Serve the main terminal dashboard"""
            return render_template("terminal_dashboard.html")

        @self.app.route("/multiswarm")
        def multiswarm_dashboard():
            """Serve the multiswarm dashboard"""
            return render_template("multiswarm_dashboard.html")

        @self.app.route("/harvard")
        def harvard_dashboard():
            """Serve the Harvard workflow visualization"""
            return render_template("harvard_workflow_visualization.html")

        @self.app.route("/api/health", methods=["GET"])
        def health_check():
            return jsonify(
                {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "active_cases": len(self.active_cases),
                    "agents_online": sum(
                        1 for agent in self.agent_status.values() if agent["status"] != "offline"
                    ),
                    "system_metrics": self.system_metrics,
                }
            )

        @self.app.route("/api/system/metrics", methods=["GET"])
        def get_system_metrics():
            """Get current system metrics"""
            return jsonify(
                {
                    "success": True,
                    "metrics": self.system_metrics,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        @self.app.route("/api/terminal/logs", methods=["GET"])
        def get_terminal_logs():
            """Get terminal logs"""
            limit = request.args.get("limit", 50, type=int)
            return jsonify(
                {
                    "success": True,
                    "logs": self.terminal_logs[-limit:],
                    "total": len(self.terminal_logs),
                }
            )

        @self.app.route("/api/phases/status", methods=["GET"])
        def get_phase_status():
            """Get detailed phase status"""
            phase_details = {}
            for phase_id, progress in self.phase_progress.items():
                status = "pending"
                if progress == 100:
                    status = "completed"
                elif progress > 0:
                    status = "active"

                phase_details[phase_id] = {
                    "progress": progress,
                    "status": status,
                    "last_updated": datetime.now().isoformat(),
                }

            return jsonify(
                {
                    "success": True,
                    "phases": phase_details,
                    "overall_progress": sum(self.phase_progress.values())
                    / len(self.phase_progress),
                }
            )

        @self.app.route("/api/outputs", methods=["GET"])
        def get_outputs():
            """Get available output files"""
            outputs = []
            for packet in self.case_packets:
                outputs.append(
                    {
                        "id": packet["id"],
                        "title": packet["title"],
                        "type": "case_packet",
                        "generated_at": packet["generated_at"],
                        "documents": packet["documents"],
                        "metadata": packet["metadata"],
                    }
                )

            return jsonify({"success": True, "outputs": outputs, "total": len(outputs)})

        @self.app.route("/api/download/<output_id>", methods=["GET"])
        def download_output(output_id):
            """Download specific output file"""
            # In real implementation, this would serve actual files
            for packet in self.case_packets:
                if packet["id"] == output_id:
                    return jsonify(
                        {
                            "success": True,
                            "download_url": f"/downloads/{output_id}.zip",
                            "filename": f"{packet['title']}.zip",
                        }
                    )

            return jsonify({"success": False, "error": "Output not found"}), 404

        @self.app.route("/api/vector-store/status", methods=["GET"])
        def vector_store_status():
            """Mock vector store status for UI compatibility"""
            return jsonify(
                {
                    "success": True,
                    "stores": {
                        "primary_evidence": {
                            "documents": 1250,
                            "last_updated": datetime.now().isoformat(),
                        },
                        "case_opinions": {
                            "documents": 850,
                            "last_updated": datetime.now().isoformat(),
                        },
                        "general_rag": {
                            "documents": 2100,
                            "last_updated": datetime.now().isoformat(),
                        },
                    },
                    "validation_sub_vectors": 15,
                }
            )

        @self.app.route("/api/vector-store/apply-validation-filter", methods=["POST"])
        def apply_validation_filter():
            """Mock validation filter application"""
            data = request.get_json()
            validation_type = data.get("validation_type", "complaints_against_tesla")

            # Simulate processing
            self.socketio.emit(
                "vector_filter_applied",
                {
                    "validation_type": validation_type,
                    "document_count": 450,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            return jsonify(
                {
                    "success": True,
                    "validation_type": validation_type,
                    "document_count": 450,
                    "message": f"Applied {validation_type} filter successfully",
                }
            )

        @self.app.route("/api/cases", methods=["GET"])
        def get_cases():
            """Get all active cases"""
            return jsonify(
                {"cases": list(self.active_cases.values()), "total": len(self.active_cases)}
            )

        @self.app.route("/api/cases/<case_id>", methods=["GET"])
        def get_case(case_id):
            """Get specific case details"""
            if case_id in self.active_cases:
                return jsonify(self.active_cases[case_id])
            return jsonify({"error": "Case not found"}), 404

        @self.app.route("/api/agents/status", methods=["GET"])
        def get_agent_status():
            """Get current agent status"""
            return jsonify({"agents": self.agent_status, "timestamp": datetime.now().isoformat()})

        @self.app.route("/api/phases/progress", methods=["GET"])
        def get_phase_progress():
            """Get MultiSWARM phase progress"""
            return jsonify(
                {
                    "phases": self.phase_progress,
                    "overall_progress": sum(self.phase_progress.values())
                    / len(self.phase_progress),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Evidence Management API Endpoints for React Grid
        @self.app.route("/api/evidence", methods=["GET"])
        def get_evidence_list():
            """Get all evidence entries for the grid"""
            try:
                from lawyerfactory.storage.evidence.table import EnhancedEvidenceTable

                # Get query parameters for filtering
                evidence_type = request.args.get("evidence_type")
                relevance_level = request.args.get("relevance_level")
                source_document = request.args.get("source_document")
                min_relevance_score = request.args.get("min_relevance_score", type=float)

                # Initialize evidence table
                table = EnhancedEvidenceTable()

                # Get filtered evidence
                if any([evidence_type, relevance_level, source_document, min_relevance_score]):
                    from lawyerfactory.storage.evidence.table import EvidenceType, RelevanceLevel

                    evidence_list = table.get_evidence_by_filters(
                        evidence_type=EvidenceType(evidence_type) if evidence_type else None,
                        relevance_level=(
                            RelevanceLevel(relevance_level) if relevance_level else None
                        ),
                        source_document=source_document,
                        min_relevance_score=min_relevance_score,
                    )
                else:
                    evidence_list = list(table.evidence_entries.values())

                # Convert to grid format
                grid_data = []
                for entry in evidence_list:
                    entry_dict = entry.to_dict()
                    # Add metrics history for sparklines
                    entry_dict["metrics_history"] = [
                        entry.relevance_score * 0.8 + 0.1,
                        entry.relevance_score * 0.9 + 0.05,
                        entry.relevance_score,
                        entry.relevance_score * 1.1 - 0.05,
                        entry.relevance_score * 1.05,
                    ]
                    grid_data.append(entry_dict)

                return jsonify(
                    {
                        "success": True,
                        "data": grid_data,
                        "total": len(grid_data),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            except Exception as e:
                logger.error(f"Error getting evidence list: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/evidence/<evidence_id>", methods=["GET"])
        def get_evidence(evidence_id):
            """Get specific evidence entry"""
            try:
                from lawyerfactory.storage.evidence.table import EnhancedEvidenceTable

                table = EnhancedEvidenceTable()
                entry = table.get_evidence(evidence_id)

                if entry:
                    entry_dict = entry.to_dict()
                    entry_dict["metrics_history"] = [
                        entry.relevance_score * 0.8 + 0.1,
                        entry.relevance_score * 0.9 + 0.05,
                        entry.relevance_score,
                        entry.relevance_score * 1.1 - 0.05,
                        entry.relevance_score * 1.05,
                    ]
                    return jsonify(
                        {
                            "success": True,
                            "data": entry_dict,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                else:
                    return jsonify({"success": False, "error": "Evidence not found"}), 404

            except Exception as e:
                logger.error(f"Error getting evidence {evidence_id}: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/evidence", methods=["POST"])
        def create_evidence():
            """Create new evidence entry"""
            try:
                from lawyerfactory.storage.evidence.table import (
                    EnhancedEvidenceTable,
                    EvidenceEntry,
                    EvidenceType,
                    PrivilegeMarker,
                    RelevanceLevel,
                )

                data = request.get_json()
                if not data:
                    return jsonify({"success": False, "error": "No data provided"}), 400

                table = EnhancedEvidenceTable()

                # Create evidence entry
                evidence = EvidenceEntry(
                    source_document=data.get("source_document", ""),
                    content=data.get("content", ""),
                    evidence_type=EvidenceType(data.get("evidence_type", "documentary")),
                    relevance_score=float(data.get("relevance_score", 0.0)),
                    relevance_level=RelevanceLevel(data.get("relevance_level", "unknown")),
                    supporting_facts=data.get("supporting_facts", []),
                    bluebook_citation=data.get("bluebook_citation", ""),
                    privilege_marker=PrivilegeMarker(data.get("privilege_marker", "none")),
                    extracted_date=data.get("extracted_date"),
                    witness_name=data.get("witness_name"),
                    key_terms=data.get("key_terms", []),
                    notes=data.get("notes", ""),
                    created_by=data.get("created_by", "api_user"),
                )

                evidence_id = table.add_evidence(evidence)

                # Emit real-time update
                self.socketio.emit(
                    "evidence_created",
                    {
                        "evidence_id": evidence_id,
                        "evidence": evidence.to_dict(),
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                return (
                    jsonify(
                        {
                            "success": True,
                            "evidence_id": evidence_id,
                            "message": "Evidence created successfully",
                            "timestamp": datetime.now().isoformat(),
                        }
                    ),
                    201,
                )

            except Exception as e:
                logger.error(f"Error creating evidence: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/evidence/<evidence_id>", methods=["PUT"])
        def update_evidence(evidence_id):
            """Update existing evidence entry"""
            try:
                from lawyerfactory.storage.evidence.table import EnhancedEvidenceTable

                data = request.get_json()
                if not data:
                    return jsonify({"success": False, "error": "No data provided"}), 400

                table = EnhancedEvidenceTable()

                # Update evidence
                success = table.update_evidence(evidence_id, data)

                if success:
                    # Get updated entry
                    updated_entry = table.get_evidence(evidence_id)
                    if updated_entry:
                        # Emit real-time update
                        self.socketio.emit(
                            "evidence_updated",
                            {
                                "evidence_id": evidence_id,
                                "evidence": updated_entry.to_dict(),
                                "timestamp": datetime.now().isoformat(),
                            },
                        )

                    return jsonify(
                        {
                            "success": True,
                            "message": "Evidence updated successfully",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                else:
                    return jsonify({"success": False, "error": "Evidence not found"}), 404

            except Exception as e:
                logger.error(f"Error updating evidence {evidence_id}: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/evidence/<evidence_id>", methods=["DELETE"])
        def delete_evidence(evidence_id):
            """Delete evidence entry"""
            try:
                from lawyerfactory.storage.evidence.table import EnhancedEvidenceTable

                table = EnhancedEvidenceTable()

                # Delete evidence
                success = table.delete_evidence(evidence_id)

                if success:
                    # Emit real-time update
                    self.socketio.emit(
                        "evidence_deleted",
                        {"evidence_id": evidence_id, "timestamp": datetime.now().isoformat()},
                    )

                    return jsonify(
                        {
                            "success": True,
                            "message": "Evidence deleted successfully",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                else:
                    return jsonify({"success": False, "error": "Evidence not found"}), 404

            except Exception as e:
                logger.error(f"Error deleting evidence {evidence_id}: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/evidence/stats", methods=["GET"])
        def get_evidence_stats():
            """Get evidence table statistics"""
            try:
                from lawyerfactory.storage.evidence.table import EnhancedEvidenceTable

                table = EnhancedEvidenceTable()
                stats = table.get_stats()

                return jsonify(
                    {"success": True, "stats": stats, "timestamp": datetime.now().isoformat()}
                )

            except Exception as e:
                logger.error(f"Error getting evidence stats: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/evidence/export", methods=["GET"])
        def export_evidence():
            """Export evidence data for grid"""
            try:
                from lawyerfactory.storage.evidence.table import EnhancedEvidenceTable

                table = EnhancedEvidenceTable()
                export_data = table.export_to_dict()

                return jsonify(
                    {"success": True, "data": export_data, "timestamp": datetime.now().isoformat()}
                )

            except Exception as e:
                logger.error(f"Error exporting evidence: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

    def setup_socket_events(self):
        """Setup Socket.IO events"""

        @self.socketio.on("connect")
        def handle_connect():
            """Handle new client connections"""
            logger.info(f"Client connected: {request.sid}")
            emit(
                "connected",
                {
                    "message": "Welcome to the LawyerFactory server",
                    "timestamp": datetime.now().isoformat(),
                },
            )

        @self.socketio.on("disconnect")
        def handle_disconnect():
            """Handle client disconnections"""
            logger.info(f"Client disconnected: {request.sid}")

        @self.socketio.on("system_reset")
        def handle_system_reset():
            """Handle system reset command"""
            logger.info("System reset requested")
            self.add_terminal_log("SYSTEM", "System reset initiated", "warning")

            # Reset all state
            self.reset_system_state()

            emit(
                "system_reset_complete",
                {"message": "System reset completed", "timestamp": datetime.now().isoformat()},
            )

        # Evidence Grid Socket.IO Events
        @self.socketio.on("join_evidence_room")
        def handle_join_evidence_room(data):
            """Join evidence collaboration room"""
            room = data.get("room", "evidence_main")
            join_room(room)
            logger.info(f"Client {request.sid} joined evidence room: {room}")
            emit(
                "joined_evidence_room",
                {
                    "room": room,
                    "message": f"Joined evidence collaboration room: {room}",
                    "timestamp": datetime.now().isoformat(),
                },
            )

        @self.socketio.on("leave_evidence_room")
        def handle_leave_evidence_room(data):
            """Leave evidence collaboration room"""
            room = data.get("room", "evidence_main")
            leave_room(room)
            logger.info(f"Client {request.sid} left evidence room: {room}")
            emit(
                "left_evidence_room",
                {
                    "room": room,
                    "message": f"Left evidence collaboration room: {room}",
                    "timestamp": datetime.now().isoformat(),
                },
            )

        @self.socketio.on("evidence_grid_sync")
        def handle_evidence_grid_sync():
            """Sync evidence grid data for all clients"""
            try:
                from lawyerfactory.storage.evidence.table import EnhancedEvidenceTable

                table = EnhancedEvidenceTable()
                evidence_list = list(table.evidence_entries.values())

                # Convert to grid format
                grid_data = []
                for entry in evidence_list:
                    entry_dict = entry.to_dict()
                    entry_dict["metrics_history"] = [
                        entry.relevance_score * 0.8 + 0.1,
                        entry.relevance_score * 0.9 + 0.05,
                        entry.relevance_score,
                        entry.relevance_score * 1.1 - 0.05,
                        entry.relevance_score * 1.05,
                    ]
                    grid_data.append(entry_dict)

                emit(
                    "evidence_grid_synced",
                    {
                        "data": grid_data,
                        "total": len(grid_data),
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            except Exception as e:
                logger.error(f"Error syncing evidence grid: {e}")
                emit(
                    "evidence_sync_error",
                    {"error": str(e), "timestamp": datetime.now().isoformat()},
                )

        @self.socketio.on("evidence_bulk_update")
        def handle_evidence_bulk_update(data):
            """Handle bulk evidence updates"""
            try:
                updates = data.get("updates", [])
                if not updates:
                    emit(
                        "evidence_bulk_update_error",
                        {"error": "No updates provided", "timestamp": datetime.now().isoformat()},
                    )
                    return

                from lawyerfactory.storage.evidence.table import EnhancedEvidenceTable

                table = EnhancedEvidenceTable()
                success_count = 0
                errors = []

                for update in updates:
                    evidence_id = update.get("evidence_id")
                    update_data = update.get("data", {})

                    if table.update_evidence(evidence_id, update_data):
                        success_count += 1
                    else:
                        errors.append(f"Failed to update {evidence_id}")

                # Emit results
                emit(
                    "evidence_bulk_updated",
                    {
                        "success_count": success_count,
                        "error_count": len(errors),
                        "errors": errors,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                # Trigger grid sync for all clients
                self.socketio.emit("evidence_grid_sync", room="evidence_main")

            except Exception as e:
                logger.error(f"Error in bulk evidence update: {e}")
                emit(
                    "evidence_bulk_update_error",
                    {"error": str(e), "timestamp": datetime.now().isoformat()},
                )

        @self.socketio.on("evidence_filter_applied")
        def handle_evidence_filter(data):
            """Handle evidence filter application"""
            filter_criteria = data.get("filters", {})
            logger.info(f"Evidence filter applied: {filter_criteria}")

            # Broadcast filter to other clients in the room
            emit(
                "evidence_filter_updated",
                {
                    "filters": filter_criteria,
                    "applied_by": request.sid,
                    "timestamp": datetime.now().isoformat(),
                },
                room="evidence_main",
                skip_sid=request.sid,
            )

        @self.socketio.on("evidence_export_requested")
        def handle_evidence_export(data):
            """Handle evidence export request"""
            export_format = data.get("format", "json")
            logger.info(f"Evidence export requested: {export_format}")

            try:
                from lawyerfactory.storage.evidence.table import EnhancedEvidenceTable

                table = EnhancedEvidenceTable()
                export_data = table.export_to_dict()

                emit(
                    "evidence_export_ready",
                    {
                        "format": export_format,
                        "data": export_data,
                        "filename": f'evidence_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{export_format}',
                        "timestamp": datetime.now().isoformat(),
                    },
                )
            except Exception as e:
                logger.error(f"Evidence export failed: {e}")
                emit("evidence_export_error", {"error": str(e)})

        # Phase Workflow Socket.IO Handlers for React UI
        @self.socketio.on("start_phase")
        def handle_start_phase(data):
            """Handle phase start request from React UI"""
            phase_id = data.get("phase")
            logger.info(f"Phase {phase_id} start requested")

            try:
                # Initialize phase progress
                self.phase_progress[phase_id] = 0

                # Emit phase started confirmation
                emit(
                    "phase_started",
                    {
                        "phase": phase_id,
                        "timestamp": datetime.now().isoformat(),
                        "message": f"Phase {phase_id} has been initiated",
                    },
                )

                # Simulate phase progress updates
                def update_phase_progress():
                    for progress in [25, 50, 75, 100]:
                        time.sleep(2)  # Simulate work
                        self.phase_progress[phase_id] = progress
                        emit(
                            "phase_progress",
                            {
                                "phase": phase_id,
                                "progress": progress,
                                "timestamp": datetime.now().isoformat(),
                            },
                        )

                    # Mark phase complete
                    emit(
                        "phase_complete",
                        {
                            "phase": phase_id,
                            "timestamp": datetime.now().isoformat(),
                            "message": f"Phase {phase_id} completed successfully",
                        },
                    )

                # Start background progress simulation
                self.socketio.start_background_task(update_phase_progress)

            except Exception as e:
                logger.error(f"Error starting phase {phase_id}: {e}")
                emit(
                    "phase_error",
                    {"phase": phase_id, "error": str(e), "timestamp": datetime.now().isoformat()},
                )

        @self.socketio.on("get_phase_status")
        def handle_get_phase_status():
            """Handle request for current phase status"""
            emit(
                "phase_status_update",
                {"phases": self.phase_progress, "timestamp": datetime.now().isoformat()},
            )

        @self.socketio.on("workflow_reset")
        def handle_workflow_reset():
            """Handle workflow reset request"""
            logger.info("Workflow reset requested")
            self.phase_progress = {
                "A01": 0,
                "A02": 0,
                "A03": 0,
                "B01": 0,
                "B02": 0,
                "C01": 0,
                "C02": 0,
            }

            emit(
                "workflow_reset_complete",
                {"message": "Workflow has been reset", "timestamp": datetime.now().isoformat()},
            )

            # Broadcast to all clients
            self.socketio.emit(
                "workflow_state_changed",
                {
                    "action": "reset",
                    "phases": self.phase_progress,
                    "timestamp": datetime.now().isoformat(),
                },
            )

    def reset_system_state(self):
        """Reset server state"""
        self.active_cases.clear()
        self.case_packets.clear()
        self.notifications.clear()
        self.terminal_logs.clear()

        # Reset agent status
        for agent in self.agent_status:
            self.agent_status[agent] = {"status": "idle", "progress": 0}

        # Reset phase progress
        for phase in self.phase_progress:
            self.phase_progress[phase] = 0

    def add_terminal_log(self, source, message, level="info"):
        """Add log entry to terminal"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "message": message,
            "level": level,
        }
        self.terminal_logs.append(log_entry)
        if len(self.terminal_logs) > 1000:  # Keep only last 1000 entries
            self.terminal_logs = self.terminal_logs[-1000:]

    def run(self, host="127.0.0.1", port=5000, debug=False):
        """Run the server"""
        logger.info(f"Starting LawyerFactory server on {host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='LawyerFactory Backend Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    server = LawyerFactoryServer()
    server.run(host=args.host, port=args.port, debug=args.debug)
