"""
LawyerFactory Canonical Evidence API Routes
Consolidated evidence management API with PRIMARY/SECONDARY classification,
unified storage integration, and real-time updates.

This is the single source of truth for all evidence-related API functionality.

Key Features:
- Enhanced evidence table management
- PRIMARY/SECONDARY evidence classification
- Unified storage integration
- Real-time Socket.IO updates
- Advanced filtering and search
- Evidence-to-facts linking
- Research query generation
- Batch operations
- Export capabilities
- Download functionality

Consolidated from:
- apps/api/routes/evidence_flask.py (Flask evidence API)
- apps/api/routes/evidence.py (AIOHTTP evidence API)
- src/lawyerfactory/phases/phaseA01_intake/evidence_routes.py (Phase-specific evidence API)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import csv
import io
from datetime import datetime

# Add src to path for lawyerfactory imports
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from flask import Blueprint, jsonify, request, send_file
from flask_socketio import emit

# Import evidence table components with fallbacks
try:
    from lawyerfactory.storage.evidence.table import (
        ClaimEntry,
        EnhancedEvidenceTable,
        EvidenceEntry,
        EvidenceSource,
        EvidenceType,
        FactAssertion,
        PrivilegeMarker,
        RelevanceLevel,
    )
    EVIDENCE_TABLE_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✓ EnhancedEvidenceTable imported successfully")
except ImportError as e:
    EVIDENCE_TABLE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"EnhancedEvidenceTable not available: {e}")

# Import unified storage for download functionality
try:
    from lawyerfactory.storage.core.unified_storage_api import get_enhanced_unified_storage_api
    UNIFIED_STORAGE_AVAILABLE = True
    logger.info("✓ EnhancedUnifiedStorageAPI imported successfully")
except ImportError:
    UNIFIED_STORAGE_AVAILABLE = False
    logger.warning("EnhancedUnifiedStorageAPI not available")

# Create blueprint for evidence API
evidence_bp = Blueprint('evidence_api', __name__)

# Global evidence table instance and socketio reference
evidence_table = None
socketio_instance = None

def initialize_evidence_table():
    """Initialize the evidence table instance"""
    global evidence_table
    if EVIDENCE_TABLE_AVAILABLE and evidence_table is None:
        try:
            evidence_table = EnhancedEvidenceTable()
            logger.info("✓ Evidence table initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize evidence table: {e}")
            evidence_table = None
    return evidence_table

# ============================================================================
# ENHANCED EVIDENCE TABLE API ROUTES
# ============================================================================

@evidence_bp.route("/api/evidence", methods=["GET"])
def get_enhanced_evidence_table():
    """
    Get complete evidence table data with enhanced formatting and filtering
    Supports PRIMARY/SECONDARY evidence classification and advanced search
    """
    try:
        # Initialize evidence table if needed
        if not evidence_table:
            initialize_evidence_table()
            if not evidence_table:
                return jsonify({"error": "Evidence table not available"}), 503

        # Get query parameters for filtering
        query_params = request.args

        # Parse filter parameters
        evidence_source_filter = query_params.get("evidence_source", "all")  # 'all', 'primary', 'secondary'
        evidence_type_filter = query_params.get("evidence_type")
        relevance_level_filter = query_params.get("relevance_level")
        search_term = query_params.get("search", "")
        min_relevance_score = query_params.get("min_relevance_score")

        # Get evidence data
        data = evidence_table.export_to_dict()
        evidence_entries = data.get("evidence_entries", [])

        # Apply filters
        filtered_entries = []
        for entry_data in evidence_entries:
            # Evidence source filter
            if evidence_source_filter != "all":
                if entry_data.get("evidence_source") != evidence_source_filter:
                    continue

            # Evidence type filter
            if evidence_type_filter and entry_data.get("evidence_type") != evidence_type_filter:
                continue

            # Relevance level filter
            if relevance_level_filter and entry_data.get("relevance_level") != relevance_level_filter:
                continue

            # Relevance score filter
            if min_relevance_score:
                try:
                    min_score = float(min_relevance_score)
                    if entry_data.get("relevance_score", 0) < min_score:
                        continue
                except ValueError:
                    pass  # Invalid min_relevance_score, ignore

            # Search filter
            if search_term:
                search_lower = search_term.lower()
                searchable_text = (
                    f"{entry_data.get('source_document', '')} "
                    f"{entry_data.get('content', '')} "
                    f"{entry_data.get('bluebook_citation', '')} "
                    f"{entry_data.get('notes', '')} "
                    f"{' '.join(entry_data.get('key_terms', []))}"
                ).lower()

                if search_lower not in searchable_text:
                    continue

            filtered_entries.append(entry_data)

        # Format for frontend compatibility
        evidence_list = []
        for evidence_data in filtered_entries:
            evidence_entry = {
                "evidence_id": evidence_data.get("id", evidence_data.get("evidence_id", "unknown")),
                "object_id": evidence_data.get("object_id"),
                "filename": evidence_data.get("source_document", "Unknown"),
                "description": evidence_data.get("content", "")[:200],
                "evidence_source": evidence_data.get("evidence_source", "primary"),
                "status": "analyzed" if evidence_data.get("relevance_score", 0) > 0 else "stored",
                "file_size": len(evidence_data.get("content", "")),
                "upload_date": evidence_data.get("created_at"),
                "phase": evidence_data.get("phase", "unknown"),
                "tags": ", ".join(evidence_data.get("key_terms", [])),
                "facts": evidence_data.get("supporting_facts", []),
                "research_query": evidence_data.get("research_query"),
                "research_confidence": evidence_data.get("research_confidence", 0.0),
                "relevance_score": evidence_data.get("relevance_score", 0.0),
                "evidence_type": evidence_data.get("evidence_type", "documentary"),
                "bluebook_citation": evidence_data.get("bluebook_citation", ""),
            }
            evidence_list.append(evidence_entry)

        # Calculate statistics
        primary_count = len([e for e in evidence_list if e["evidence_source"] == "primary"])
        secondary_count = len([e for e in evidence_list if e["evidence_source"] == "secondary"])

        return jsonify({
            "success": True,
            "evidence": evidence_list,
            "total": len(evidence_list),
            "primary_count": primary_count,
            "secondary_count": secondary_count,
            "filters_applied": {
                "evidence_source": evidence_source_filter,
                "evidence_type": evidence_type_filter,
                "relevance_level": relevance_level_filter,
                "search": search_term,
                "min_relevance_score": min_relevance_score,
            }
        })

    except Exception as e:
        logger.error(f"Failed to get evidence table: {e}")
        return jsonify({"error": str(e)}), 500


@evidence_bp.route("/api/evidence", methods=["POST"])
def add_enhanced_evidence_entry():
    """Add new evidence entry with enhanced validation and classification"""
    try:
        # Initialize evidence table if needed
        if not evidence_table:
            initialize_evidence_table()
            if not evidence_table:
                return jsonify({"error": "Evidence table not available"}), 503

        data = request.get_json()

        # Validate required fields
        required_fields = ["source_document", "content", "evidence_source"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Field '{field}' is required"}), 400

        # Validate evidence_source
        valid_sources = ["primary", "secondary"]
        if data.get("evidence_source") not in valid_sources:
            return jsonify({
                "error": f"Invalid evidence_source. Must be one of: {valid_sources}"
            }), 400

        # Create evidence entry with enhanced metadata
        evidence = EvidenceEntry(
            source_document=data.get("source_document"),
            page_section=data.get("page_section", ""),
            content=data.get("content"),
            evidence_type=EvidenceType(data.get("evidence_type", "documentary")),
            evidence_source=EvidenceSource(data.get("evidence_source")),
            relevance_score=float(data.get("relevance_score", 0.0)),
            relevance_level=RelevanceLevel(data.get("relevance_level", "unknown")),
            bluebook_citation=data.get("bluebook_citation", ""),
            privilege_marker=PrivilegeMarker(data.get("privilege_marker", "none")),
            extracted_date=data.get("extracted_date"),
            witness_name=data.get("witness_name"),
            key_terms=data.get("key_terms", []),
            notes=data.get("notes", ""),
            research_query=data.get("research_query"),
            research_confidence=float(data.get("research_confidence", 0.0)),
            created_by=data.get("created_by", "user"),
            phase=data.get("phase", "phaseA01_intake"),
        )

        evidence_id = evidence_table.add_evidence(evidence)

        # Emit real-time update using the global socketio instance
        if socketio_instance:
            socketio_instance.emit("evidence_added", {
                "evidence_id": evidence_id,
                "evidence": evidence.to_dict(),
                "timestamp": datetime.now().isoformat()
            })

        return jsonify({
            "success": True,
            "evidence_id": evidence_id,
            "message": "Evidence entry added successfully",
            "evidence": evidence.to_dict()
        })

    except Exception as e:
        logger.error(f"Failed to add evidence entry: {e}")
        return jsonify({"error": str(e)}), 400


@evidence_bp.route("/api/evidence/<evidence_id>", methods=["PUT"])
def update_enhanced_evidence_entry(evidence_id):
    """Update existing evidence entry with enhanced validation"""
    try:
        # Initialize evidence table if needed
        if not evidence_table:
            initialize_evidence_table()
            if not evidence_table:
                return jsonify({"error": "Evidence table not available"}), 503

        data = request.get_json()

        # Convert enum strings if provided
        if "evidence_type" in data:
            data["evidence_type"] = EvidenceType(data["evidence_type"])
        if "evidence_source" in data:
            data["evidence_source"] = EvidenceSource(data["evidence_source"])
        if "relevance_level" in data:
            data["relevance_level"] = RelevanceLevel(data["relevance_level"])
        if "privilege_marker" in data:
            data["privilege_marker"] = PrivilegeMarker(data["privilege_marker"])

        success = evidence_table.update_evidence(evidence_id, data)

        if success:
            # Emit real-time update
            emit("evidence_updated", {
                "evidence_id": evidence_id,
                "updates": data,
                "timestamp": datetime.now().isoformat()
            })

            return jsonify({
                "success": True,
                "message": "Evidence entry updated successfully"
            })
        else:
            return jsonify({"error": "Evidence entry not found"}), 404

    except Exception as e:
        logger.error(f"Failed to update evidence entry: {e}")
        return jsonify({"error": str(e)}), 400


@evidence_bp.route("/api/evidence/<evidence_id>", methods=["DELETE"])
def delete_enhanced_evidence_entry(evidence_id):
    """Delete evidence entry with enhanced cleanup"""
    try:
        # Initialize evidence table if needed
        if not evidence_table:
            initialize_evidence_table()
            if not evidence_table:
                return jsonify({"error": "Evidence table not available"}), 503

        success = evidence_table.delete_evidence(evidence_id)

        if success:
            # Emit real-time update
            emit("evidence_deleted", {
                "evidence_id": evidence_id,
                "timestamp": datetime.now().isoformat()
            })

            return jsonify({
                "success": True,
                "message": "Evidence entry deleted successfully"
            })
        else:
            return jsonify({"error": "Evidence entry not found"}), 404

    except Exception as e:
        logger.error(f"Failed to delete evidence entry: {e}")
        return jsonify({"error": str(e)}), 400


@evidence_bp.route("/api/evidence/<evidence_id>/download", methods=["GET"])
def download_enhanced_evidence(evidence_id):
    """Download evidence file with enhanced error handling and unified storage integration"""
    try:
        # Initialize evidence table if needed
        if not evidence_table:
            initialize_evidence_table()
            if not evidence_table:
                return jsonify({"error": "Evidence table not available"}), 503

        # Get evidence entry from table
        evidence = evidence_table.get_evidence(evidence_id)

        if not evidence:
            return jsonify({"error": "Evidence entry not found"}), 404

        # Check if we have an object_id for unified storage
        if not evidence.object_id:
            return jsonify({
                "error": "No storage object_id available for this evidence"
            }), 404

        # Retrieve from unified storage if available
        if UNIFIED_STORAGE_AVAILABLE:
            try:
                unified_storage = get_enhanced_unified_storage_api()
                storage_result = unified_storage.get_evidence(
                    object_id=evidence.object_id,
                    target_tier="s3"  # Get raw file from S3/local storage
                )

                if storage_result and "content" in storage_result:
                    # Return file content with appropriate headers
                    filename = evidence.source_document or f"evidence_{evidence_id}"
                    content_type = storage_result.get("content_type", "application/octet-stream")

                    return send_file(
                        io.BytesIO(storage_result["content"]),
                        mimetype=content_type,
                        as_attachment=True,
                        download_name=filename
                    )
                else:
                    return jsonify({"error": "File content not found in storage"}), 404

            except Exception as storage_error:
                logger.error(f"Unified storage retrieval failed: {storage_error}")
                return jsonify({
                    "error": f"Storage retrieval failed: {str(storage_error)}"
                }), 500
        else:
            return jsonify({"error": "Unified storage not available"}), 503

    except Exception as e:
        logger.error(f"Failed to download evidence: {e}")
        return jsonify({"error": str(e)}), 500


@evidence_bp.route("/api/evidence/filter", methods=["GET"])
def get_filtered_enhanced_evidence():
    """Get filtered evidence entries with advanced filtering options"""
    try:
        # Initialize evidence table if needed
        if not evidence_table:
            initialize_evidence_table()
            if not evidence_table:
                return jsonify({"error": "Evidence table not available"}), 503

        # Parse comprehensive filter parameters
        filters = {}

        # Evidence source filter (primary/secondary)
        if "evidence_source" in request.args:
            filters["evidence_source"] = EvidenceSource(request.args["evidence_source"])

        # Evidence type filter
        if "evidence_type" in request.args:
            filters["evidence_type"] = EvidenceType(request.args["evidence_type"])

        # Relevance level filter
        if "relevance_level" in request.args:
            filters["relevance_level"] = RelevanceLevel(request.args["relevance_level"])

        # Source document filter
        if "source_document" in request.args:
            filters["source_document"] = request.args["source_document"]

        # Relevance score filter
        if "min_relevance_score" in request.args:
            filters["min_relevance_score"] = float(request.args["min_relevance_score"])

        # Phase filter
        if "phase" in request.args:
            filters["phase"] = request.args["phase"]

        # Date range filter
        if "date_from" in request.args:
            filters["date_from"] = request.args["date_from"]
        if "date_to" in request.args:
            filters["date_to"] = request.args["date_to"]

        # Get filtered results
        results = evidence_table.get_evidence_by_filters(**filters)

        return jsonify({
            "evidence_entries": [entry.to_dict() for entry in results],
            "total_count": len(results),
            "filters_applied": filters
        })

    except Exception as e:
        logger.error(f"Failed to get filtered evidence: {e}")
        return jsonify({"error": str(e)}), 400


@evidence_bp.route("/api/evidence/stats", methods=["GET"])
def get_enhanced_evidence_stats():
    """Get comprehensive evidence table statistics"""
    try:
        # Initialize evidence table if needed
        if not evidence_table:
            initialize_evidence_table()
            if not evidence_table:
                return jsonify({"error": "Evidence table not available"}), 503

        stats = evidence_table.get_stats()

        # Add enhanced statistics
        enhanced_stats = {
            **stats,
            "evidence_by_source": {
                "primary": len([e for e in evidence_table.evidence_entries.values()
                             if e.evidence_source == EvidenceSource.PRIMARY]),
                "secondary": len([e for e in evidence_table.evidence_entries.values()
                                if e.evidence_source == EvidenceSource.SECONDARY]),
            },
            "evidence_by_type": {},
            "evidence_by_phase": {},
            "average_relevance_score": 0.0,
            "high_relevance_count": 0,
        }

        # Calculate enhanced statistics
        total_relevance = 0
        for entry in evidence_table.evidence_entries.values():
            # By type
            entry_type = entry.evidence_type.value
            enhanced_stats["evidence_by_type"][entry_type] = \
                enhanced_stats["evidence_by_type"].get(entry_type, 0) + 1

            # By phase
            phase = entry.phase or "unknown"
            enhanced_stats["evidence_by_phase"][phase] = \
                enhanced_stats["evidence_by_phase"].get(phase, 0) + 1

            # Relevance statistics
            total_relevance += entry.relevance_score
            if entry.relevance_score >= 0.7:
                enhanced_stats["high_relevance_count"] += 1

        # Calculate average relevance score
        if evidence_table.evidence_entries:
            enhanced_stats["average_relevance_score"] = \
                total_relevance / len(evidence_table.evidence_entries)

        return jsonify(enhanced_stats)

    except Exception as e:
        logger.error(f"Failed to get evidence stats: {e}")
        return jsonify({"error": str(e)}), 500


@evidence_bp.route("/api/evidence/export", methods=["GET"])
def export_enhanced_evidence_data():
    """Export evidence data in various formats with enhanced options"""
    try:
        # Initialize evidence table if needed
        if not evidence_table:
            initialize_evidence_table()
            if not evidence_table:
                return jsonify({"error": "Evidence table not available"}), 503

        export_format = request.args.get("format", "json")
        include_facts = request.args.get("include_facts", "true").lower() == "true"
        include_research = request.args.get("include_research", "true").lower() == "true"

        if export_format == "json":
            data = evidence_table.export_to_dict()

            # Add enhanced metadata to export
            data["_export_metadata"] = {
                "exported_at": datetime.now().isoformat(),
                "total_entries": len(data.get("evidence_entries", [])),
                "include_facts": include_facts,
                "include_research": include_research,
            }

            return jsonify(data)

        elif export_format == "csv":
            # Convert to CSV format with enhanced fields
            output = io.StringIO()
            writer = csv.writer(output)

            # Enhanced header
            header = [
                "Evidence ID", "Source Document", "Page/Section", "Content",
                "Evidence Type", "Evidence Source", "Relevance Score", "Relevance Level",
                "Bluebook Citation", "Phase", "Created At", "Key Terms", "Notes"
            ]

            if include_facts:
                header.append("Supporting Facts")
            if include_research:
                header.extend(["Research Query", "Research Confidence"])

            writer.writerow(header)

            # Write evidence entries
            for entry in evidence_table.evidence_entries.values():
                row = [
                    entry.evidence_id,
                    entry.source_document,
                    entry.page_section,
                    entry.content[:200] + "..." if len(entry.content) > 200 else entry.content,
                    entry.evidence_type.value,
                    entry.evidence_source.value,
                    entry.relevance_score,
                    entry.relevance_level.value,
                    entry.bluebook_citation,
                    entry.phase or "",
                    entry.created_at,
                    "; ".join(entry.key_terms),
                    entry.notes,
                ]

                if include_facts:
                    row.append("; ".join(entry.supporting_facts))
                if include_research:
                    row.extend([entry.research_query or "", entry.research_confidence])

                writer.writerow(row)

            csv_content = output.getvalue()
            output.close()

            return send_file(
                io.BytesIO(csv_content.encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f"evidence_table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

        else:
            return jsonify({
                "error": "Unsupported export format. Use 'json' or 'csv'"
            }), 400

    except Exception as e:
        logger.error(f"Failed to export evidence data: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# FACTS MANAGEMENT API ROUTES
# ============================================================================

@evidence_bp.route("/api/facts", methods=["POST"])
def add_enhanced_fact_assertion():
    """Add new fact assertion with enhanced validation"""
    try:
        # Initialize evidence table if needed
        if not evidence_table:
            initialize_evidence_table()
            if not evidence_table:
                return jsonify({"error": "Evidence table not available"}), 503

        data = request.get_json()

        # Validate required fields
        if not data.get("fact_text"):
            return jsonify({"error": "fact_text is required"}), 400

        fact = FactAssertion(
            fact_text=data.get("fact_text"),
            confidence_score=float(data.get("confidence_score", 0.0)),
            chronological_order=int(data.get("chronological_order", 0)),
            date_occurred=data.get("date_occurred"),
            location=data.get("location", ""),
            parties_involved=data.get("parties_involved", []),
        )

        fact_id = evidence_table.add_fact(fact)

        # Emit real-time update
        emit("fact_added", {
            "fact_id": fact_id,
            "fact": fact.to_dict(),
            "timestamp": datetime.now().isoformat()
        })

        return jsonify({
            "success": True,
            "fact_id": fact_id,
            "message": "Fact assertion added successfully"
        })

    except Exception as e:
        logger.error(f"Failed to add fact assertion: {e}")
        return jsonify({"error": str(e)}), 400


@evidence_bp.route("/api/evidence/link", methods=["POST"])
def link_enhanced_evidence_to_fact():
    """Link evidence entry to fact assertion with enhanced validation"""
    try:
        # Initialize evidence table if needed
        if not evidence_table:
            initialize_evidence_table()
            if not evidence_table:
                return jsonify({"error": "Evidence table not available"}), 503

        data = request.get_json()
        evidence_id = data.get("evidence_id")
        fact_id = data.get("fact_id")

        if not evidence_id or not fact_id:
            return jsonify({
                "error": "Both evidence_id and fact_id are required"
            }), 400

        success = evidence_table.link_evidence_to_fact(evidence_id, fact_id)

        if success:
            # Emit real-time update
            emit("evidence_linked_to_fact", {
                "evidence_id": evidence_id,
                "fact_id": fact_id,
                "timestamp": datetime.now().isoformat()
            })

            return jsonify({
                "success": True,
                "message": "Evidence linked to fact successfully"
            })
        else:
            return jsonify({"error": "Evidence or fact not found"}), 404

    except Exception as e:
        logger.error(f"Failed to link evidence to fact: {e}")
        return jsonify({"error": str(e)}), 400


# ============================================================================
# CLAIMS MANAGEMENT API ROUTES
# ============================================================================

@evidence_bp.route("/api/claims", methods=["POST"])
def add_enhanced_claim_entry():
    """Add new claim entry with enhanced validation"""
    try:
        # Initialize evidence table if needed
        if not evidence_table:
            initialize_evidence_table()
            if not evidence_table:
                return jsonify({"error": "Evidence table not available"}), 503

        data = request.get_json()

        # Validate required fields
        if not data.get("cause_of_action"):
            return jsonify({"error": "cause_of_action is required"}), 400

        claim = ClaimEntry(
            cause_of_action=data.get("cause_of_action"),
            claim_strength=float(data.get("claim_strength", 0.0)),
            jurisdiction=data.get("jurisdiction", ""),
            statute_of_limitations=data.get("statute_of_limitations", ""),
            damages_sought=data.get("damages_sought", ""),
        )

        claim_id = evidence_table.add_claim(claim)

        # Emit real-time update
        emit("claim_added", {
            "claim_id": claim_id,
            "claim": claim.to_dict(),
            "timestamp": datetime.now().isoformat()
        })

        return jsonify({
            "success": True,
            "claim_id": claim_id,
            "message": "Claim entry added successfully"
        })

    except Exception as e:
        logger.error(f"Failed to add claim entry: {e}")
        return jsonify({"error": str(e)}), 400


# ============================================================================
# BATCH OPERATIONS API ROUTES
# ============================================================================

@evidence_bp.route("/api/evidence/batch", methods=["POST"])
def batch_enhanced_evidence_operations():
    """Perform batch operations on multiple evidence entries"""
    try:
        # Initialize evidence table if needed
        if not evidence_table:
            initialize_evidence_table()
            if not evidence_table:
                return jsonify({"error": "Evidence table not available"}), 503

        data = request.get_json()
        operation = data.get("operation")
        evidence_ids = data.get("evidence_ids", [])
        operation_data = data.get("data", {})

        if not operation or not evidence_ids:
            return jsonify({
                "error": "operation and evidence_ids are required"
            }), 400

        results = []

        for evidence_id in evidence_ids:
            try:
                if operation == "update":
                    success = evidence_table.update_evidence(evidence_id, operation_data)
                    results.append({
                        "evidence_id": evidence_id,
                        "success": success,
                        "operation": operation
                    })
                elif operation == "delete":
                    success = evidence_table.delete_evidence(evidence_id)
                    results.append({
                        "evidence_id": evidence_id,
                        "success": success,
                        "operation": operation
                    })
                else:
                    results.append({
                        "evidence_id": evidence_id,
                        "success": False,
                        "error": f"Unknown operation: {operation}"
                    })
            except Exception as e:
                results.append({
                    "evidence_id": evidence_id,
                    "success": False,
                    "error": str(e)
                })

        # Emit real-time update for batch operation
        emit("batch_operation_completed", {
            "operation": operation,
            "results": results,
            "timestamp": datetime.now().isoformat()
        })

        successful_operations = len([r for r in results if r["success"]])

        return jsonify({
            "success": True,
            "operation": operation,
            "results": results,
            "total_processed": len(results),
            "successful_operations": successful_operations,
            "message": f"Batch {operation} completed: {successful_operations}/{len(results)} successful"
        })

    except Exception as e:
        logger.error(f"Failed to perform batch operation: {e}")
        return jsonify({"error": str(e)}), 400


# ============================================================================
# RESEARCH INTEGRATION API ROUTES
# ============================================================================

@evidence_bp.route("/api/evidence/research", methods=["POST"])
def request_enhanced_research():
    """Request research from PRIMARY evidence with enhanced validation"""
    try:
        data = request.get_json()
        evidence_id = data.get("evidence_id")
        custom_keywords = data.get("keywords")

        if not evidence_id:
            return jsonify({"error": "evidence_id is required"}), 400

        # Initialize evidence table if needed
        if not evidence_table:
            initialize_evidence_table()
            if not evidence_table:
                return jsonify({"error": "Evidence table not available"}), 503

        # Get evidence entry
        evidence = evidence_table.get_evidence(evidence_id)
        if not evidence:
            return jsonify({"error": "Evidence entry not found"}), 404

        # Validate that evidence is PRIMARY
        if evidence.evidence_source != EvidenceSource.PRIMARY:
            return jsonify({
                "error": "Can only research from PRIMARY evidence"
            }), 400

        # Extract keywords from evidence content if not provided
        keywords = custom_keywords
        if not keywords:
            # Simple keyword extraction (in production, use NLP)
            content_words = evidence.content.lower().split()
            # Filter for meaningful words (basic implementation)
            stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
            keywords = [word for word in content_words if len(word) > 4 and word not in stop_words][:10]

        # Generate research ID
        research_id = f"research_{int(datetime.now().timestamp())}"

        # Emit research started event
        emit('research_started', {
            'research_id': research_id,
            'evidence_id': evidence_id,
            'keywords': keywords,
            'status': 'processing',
            'timestamp': datetime.now().isoformat()
        })

        # Store research request for tracking
        research_request = {
            'research_id': research_id,
            'evidence_id': evidence_id,
            'keywords': keywords,
            'status': 'processing',
            'started_at': datetime.now().isoformat()
        }

        return jsonify({
            "success": True,
            "research_id": research_id,
            "message": f"Research started with {len(keywords)} keywords from PRIMARY evidence",
            "keywords": keywords,
            "evidence": evidence.to_dict()
        })

    except Exception as e:
        logger.error(f"Failed to request research: {e}")
        return jsonify({"error": str(e)}), 400


# ============================================================================
# INITIALIZATION FUNCTION
# ============================================================================

def initialize_canonical_evidence_api(app, socketio):
    """
    Initialize the canonical evidence API with enhanced features
    This function should be called during app initialization
    """
    global socketio_instance
    
    try:
        # Store socketio reference for real-time updates
        socketio_instance = socketio
        
        # Initialize evidence table
        initialize_evidence_table()

        # Register blueprint
        app.register_blueprint(evidence_bp)

        logger.info("✓ Canonical Evidence API initialized successfully")
        logger.info("📊 Available endpoints:")
        logger.info("  - GET  /api/evidence")
        logger.info("  - POST /api/evidence")
        logger.info("  - PUT  /api/evidence/<evidence_id>")
        logger.info("  - DELETE /api/evidence/<evidence_id>")
        logger.info("  - GET  /api/evidence/<evidence_id>/download")
        logger.info("  - GET  /api/evidence/filter")
        logger.info("  - GET  /api/evidence/stats")
        logger.info("  - GET  /api/evidence/export")
        logger.info("  - POST /api/facts")
        logger.info("  - POST /api/evidence/link")
        logger.info("  - POST /api/claims")
        logger.info("  - POST /api/evidence/batch")
        logger.info("  - POST /api/evidence/research")

        return True

    except Exception as e:
        logger.error(f"Failed to initialize canonical evidence API: {e}")
        return False