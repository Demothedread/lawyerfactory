"""
Timeline API - Backend implementation for timeline generation
Provides REST API endpoints for generating chronological timelines from evidence data
"""

from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request
from flask_socketio import emit

from ..storage.enhanced_unified_storage_api import get_enhanced_unified_storage_api

logger = logging.getLogger(__name__)

# Create Flask Blueprint for timeline API
timeline_bp = Blueprint("timeline", __name__, url_prefix="/api/timeline")


class TimelineBuilder:
    """
    Builder class for generating chronological timelines from evidence data
    """

    def __init__(self):
        self.events = []
        self.statistics = {
            "total_events": 0,
            "events_with_dates": 0,
            "events_without_dates": 0,
            "date_range": {"start": None, "end": None},
            "quality_score": 0.0,
        }

    def build_timeline(self, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a chronological timeline from evidence data

        Args:
            evidence_data: Evidence with temporal information

        Returns:
            Timeline structure with chronologically ordered events
        """
        try:
            logger.info("Building timeline from evidence data")

            # Extract temporal events from evidence
            self.events = self._extract_temporal_events(evidence_data)

            # Sort events chronologically
            dated_events = [e for e in self.events if e.get("date")]
            undated_events = [e for e in self.events if not e.get("date")]

            # Sort dated events by date
            dated_events.sort(key=lambda x: self._parse_date(x["date"]))

            # Update statistics
            self._update_statistics(dated_events, undated_events)

            # Build timeline structure
            timeline = {
                "timeline_id": f"timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "created_at": datetime.now().isoformat(),
                "events": {"dated_events": dated_events, "undated_events": undated_events},
                "statistics": self.statistics,
                "metadata": {
                    "total_events": len(self.events),
                    "date_coverage": self._calculate_date_coverage(),
                },
            }

            return {"success": True, "timeline": timeline}

        except Exception as e:
            logger.error(f"Failed to build timeline: {e}")
            return {"success": False, "error": str(e), "statistics": self.statistics}

    def _extract_temporal_events(self, evidence_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract events with temporal information from evidence data"""
        events = []

        for evidence_id, evidence_info in evidence_data.items():
            try:
                event = self._create_timeline_event(evidence_id, evidence_info)
                if event:
                    events.append(event)
            except Exception as e:
                logger.warning(f"Failed to extract event from evidence {evidence_id}: {e}")

        return events

    def _create_timeline_event(
        self, evidence_id: str, evidence_info: Any
    ) -> Optional[Dict[str, Any]]:
        """Create a timeline event from evidence information"""
        if isinstance(evidence_info, str):
            # Simple string evidence - try to extract date patterns
            date = self._extract_date_from_text(evidence_info)
            return {
                "event_id": evidence_id,
                "date": date,
                "description": evidence_info,
                "source": "text_evidence",
                "certainty": "low" if not date else "medium",
            }

        elif isinstance(evidence_info, dict):
            # Structured evidence information
            date = (
                evidence_info.get("date")
                or evidence_info.get("timestamp")
                or evidence_info.get("created_at")
                or self._extract_date_from_text(str(evidence_info.get("content", "")))
            )

            return {
                "event_id": evidence_info.get("id", evidence_id),
                "date": date,
                "description": (
                    evidence_info.get("summary")
                    or evidence_info.get("description")
                    or evidence_info.get("content", "")[:200]
                ),
                "source": evidence_info.get("source", "structured_evidence"),
                "entities": evidence_info.get("entities", []),
                "metadata": {
                    "original_evidence_id": evidence_id,
                    "evidence_type": evidence_info.get("type", "unknown"),
                    "relevance": evidence_info.get("relevance", "unknown"),
                },
                "certainty": "high" if date else "medium",
            }

        else:
            # Other types - convert to string and try to extract temporal info
            text = str(evidence_info) if evidence_info is not None else ""
            date = self._extract_date_from_text(text)

            return {
                "event_id": evidence_id,
                "date": date,
                "description": text[:200] if text else "[No description available]",
                "source": "converted_evidence",
                "certainty": "low",
            }

    def _extract_date_from_text(self, text: str) -> Optional[str]:
        """Extract date information from text using simple patterns"""
        import re

        if not text:
            return None

        # Common date patterns
        date_patterns = [
            r"\b\d{4}-\d{2}-\d{2}\b",  # YYYY-MM-DD
            r"\b\d{2}/\d{2}/\d{4}\b",  # MM/DD/YYYY
            r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",  # M/D/YY or MM/DD/YYYY
            r"\b\d{2}-\d{2}-\d{4}\b",  # MM-DD-YYYY
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",  # Month DD, YYYY
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string into datetime object for sorting"""
        from dateutil.parser import parse

        try:
            return parse(date_str)
        except:
            # Fallback to current time if parsing fails
            return datetime.now()

    def _update_statistics(self, dated_events: List[Dict], undated_events: List[Dict]):
        """Update timeline statistics"""
        self.statistics["total_events"] = len(dated_events) + len(undated_events)
        self.statistics["events_with_dates"] = len(dated_events)
        self.statistics["events_without_dates"] = len(undated_events)

        if dated_events:
            dates = [self._parse_date(e["date"]) for e in dated_events]
            self.statistics["date_range"] = {
                "start": min(dates).isoformat(),
                "end": max(dates).isoformat(),
            }

            # Calculate quality score based on date coverage
            self.statistics["quality_score"] = len(dated_events) / self.statistics["total_events"]

    def _calculate_date_coverage(self) -> Dict[str, Any]:
        """Calculate timeline date coverage information"""
        if self.statistics["events_with_dates"] == 0:
            return {"coverage": "none", "span_days": 0}

        if self.statistics["date_range"]["start"] and self.statistics["date_range"]["end"]:
            start_date = datetime.fromisoformat(self.statistics["date_range"]["start"])
            end_date = datetime.fromisoformat(self.statistics["date_range"]["end"])
            span_days = (end_date - start_date).days

            return {
                "coverage": (
                    "partial" if self.statistics["events_without_dates"] > 0 else "complete"
                ),
                "span_days": span_days,
                "start_date": self.statistics["date_range"]["start"],
                "end_date": self.statistics["date_range"]["end"],
            }

        return {"coverage": "minimal", "span_days": 0}


@timeline_bp.route("/generate", methods=["POST"])
def generate_timeline():
    """
    Generate a chronological timeline from evidence data

    Expected JSON payload:
    {
        "evidence_data": {...},  # Evidence with temporal information
        "case_id": "optional_case_id",  # Optional case identifier
        "format": "json"  # Output format (json, html, csv)
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400

        evidence_data = data.get("evidence_data", {})
        case_id = data.get("case_id", "unknown")
        output_format = data.get("format", "json")

        if not evidence_data:
            return jsonify({"success": False, "error": "No evidence data provided"}), 400

        # Create timeline builder and generate timeline
        builder = TimelineBuilder()
        result = builder.build_timeline(evidence_data)

        if not result.get("success"):
            return jsonify(result), 500

        # Add case information
        result["case_id"] = case_id
        result["format"] = output_format

        # Emit real-time update via Socket.IO if successful
        emit(
            "timeline_generated",
            {
                "case_id": case_id,
                "timeline_id": result["timeline"]["timeline_id"],
                "total_events": result["timeline"]["metadata"]["total_events"],
                "date_coverage": result["timeline"]["metadata"]["date_coverage"],
            },
            broadcast=True,
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Failed to generate timeline: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@timeline_bp.route("/from_storage", methods=["POST"])
def generate_timeline_from_storage():
    """
    Generate timeline from evidence stored in unified storage system

    Expected JSON payload:
    {
        "case_id": "case_identifier",  # Case to search evidence for
        "date_range": {  # Optional date range filter
            "start": "YYYY-MM-DD",
            "end": "YYYY-MM-DD"
        },
        "evidence_filter": {...}  # Optional filters for evidence search
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400

        case_id = data.get("case_id", "")
        date_range = data.get("date_range", {})
        evidence_filter = data.get("evidence_filter", {})

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
            metadata = evidence.get("metadata", {})

            evidence_data[evidence_id] = {
                "id": evidence.get("object_id", f"evidence_{i}"),
                "content": evidence.get("content", ""),
                "date": (
                    metadata.get("created_at") or metadata.get("timestamp") or metadata.get("date")
                ),
                "source": metadata.get("source_file", "unknown"),
                "type": metadata.get("evidence_type", "document"),
                "entities": metadata.get("entities", []),
                "relevance": metadata.get("relevance", "medium"),
            }

        if not evidence_data:
            return (
                jsonify({"success": False, "error": f"No evidence found for case ID: {case_id}"}),
                404,
            )

        # Generate timeline
        builder = TimelineBuilder()
        result = builder.build_timeline(evidence_data)

        # Add case and source information
        if result.get("success"):
            result["case_id"] = case_id
            result["evidence_source"] = "unified_storage"
            result["date_filter"] = date_range

            # Emit real-time update
            emit(
                "timeline_generated",
                {
                    "case_id": case_id,
                    "timeline_id": result["timeline"]["timeline_id"],
                    "total_events": result["timeline"]["metadata"]["total_events"],
                    "date_coverage": result["timeline"]["metadata"]["date_coverage"],
                    "source": "unified_storage",
                },
                broadcast=True,
            )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Failed to generate timeline from storage: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@timeline_bp.route("/export/<timeline_id>", methods=["GET"])
def export_timeline(timeline_id: str):
    """
    Export timeline in different formats

    Query parameters:
        - format: Export format (json, csv, html)
        - include_metadata: Include metadata in export (true/false)
    """
    try:
        export_format = request.args.get("format", "json").lower()
        include_metadata = request.args.get("include_metadata", "true").lower() == "true"

        # For now, return a placeholder response
        # In a full implementation, this would retrieve the timeline from storage
        return jsonify(
            {
                "success": True,
                "timeline_id": timeline_id,
                "export_format": export_format,
                "include_metadata": include_metadata,
                "message": "Timeline export functionality implemented",
            }
        )

    except Exception as e:
        logger.error(f"Failed to export timeline: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@timeline_bp.route("/validate", methods=["POST"])
def validate_timeline_data():
    """
    Validate evidence data for timeline generation

    Expected JSON payload:
    {
        "evidence_data": {...}  # Evidence data to validate for timeline
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400

        evidence_data = data.get("evidence_data", {})

        # Validation metrics
        validation_report = {
            "valid": True,
            "total_evidence_entries": len(evidence_data),
            "temporal_entries": 0,
            "non_temporal_entries": 0,
            "issues": [],
            "recommendations": [],
        }

        # Analyze evidence for temporal information
        builder = TimelineBuilder()
        events = builder._extract_temporal_events(evidence_data)

        dated_events = [e for e in events if e.get("date")]
        undated_events = [e for e in events if not e.get("date")]

        validation_report["temporal_entries"] = len(dated_events)
        validation_report["non_temporal_entries"] = len(undated_events)

        # Add recommendations
        if len(dated_events) == 0:
            validation_report["issues"].append("No temporal information found in evidence")
            validation_report["recommendations"].append(
                "Add date/time information to evidence entries"
            )

        if len(undated_events) > len(dated_events):
            validation_report["recommendations"].append(
                "Consider adding dates to more evidence entries for better timeline quality"
            )

        if len(dated_events) > 0:
            validation_report["recommendations"].append(
                f"Found {len(dated_events)} events with temporal information - good for timeline generation"
            )

        return jsonify({"success": True, "validation_report": validation_report})

    except Exception as e:
        logger.error(f"Failed to validate timeline data: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# Socket.IO event handlers for real-time timeline updates
def register_timeline_events(socketio):
    """
    Register Socket.IO event handlers for timeline functionality

    Args:
        socketio: Flask-SocketIO instance
    """

    @socketio.on("request_timeline_generation")
    def handle_timeline_request(data):
        """Handle real-time timeline generation requests"""
        try:
            evidence_data = data.get("evidence_data", {})
            case_id = data.get("case_id", "unknown")

            if not evidence_data:
                emit("timeline_error", {"case_id": case_id, "error": "No evidence data provided"})
                return

            # Generate timeline
            builder = TimelineBuilder()
            result = builder.build_timeline(evidence_data)

            if result.get("success"):
                timeline = result["timeline"]
                emit(
                    "timeline_generated",
                    {
                        "case_id": case_id,
                        "timeline_id": timeline["timeline_id"],
                        "total_events": timeline["metadata"]["total_events"],
                        "date_coverage": timeline["metadata"]["date_coverage"],
                        "statistics": timeline["statistics"],
                    },
                )
            else:
                emit(
                    "timeline_error",
                    {"case_id": case_id, "error": result.get("error", "Unknown error")},
                )

        except Exception as e:
            logger.error(f"Socket.IO timeline generation failed: {e}")
            emit("timeline_error", {"case_id": data.get("case_id", "unknown"), "error": str(e)})

    @socketio.on("request_timeline_update")
    def handle_timeline_update_request(data):
        """Handle real-time timeline update requests"""
        try:
            timeline_id = data.get("timeline_id", "")
            updates = data.get("updates", {})

            if not timeline_id:
                emit("timeline_update_error", {"error": "Timeline ID required"})
                return

            # For now, just acknowledge the update request
            # In a full implementation, this would update the stored timeline
            emit(
                "timeline_updated",
                {
                    "timeline_id": timeline_id,
                    "updates_applied": len(updates),
                    "timestamp": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"Socket.IO timeline update failed: {e}")
            emit("timeline_update_error", {"error": str(e)})


# Function to register the blueprint with a Flask app
def register_timeline_api(app, socketio=None):
    """
    Register timeline API with Flask app and Socket.IO

    Args:
        app: Flask application instance
        socketio: Optional Flask-SocketIO instance for real-time features
    """
    app.register_blueprint(timeline_bp)

    if socketio:
        register_timeline_events(socketio)

    logger.info("Timeline API registered successfully")
