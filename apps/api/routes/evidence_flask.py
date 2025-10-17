"""
Flask-compatible Evidence API routes for LawyerFactory
RESTful API endpoints for evidence management with unified storage integration
"""

import logging
import sys
from pathlib import Path

# Add src to path for lawyerfactory imports
src_path = Path(__file__).parent.parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from flask import jsonify, request, send_file
from io import BytesIO

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

# Import unified storage for download functionality
try:
    from lawyerfactory.storage.core.unified_storage_api import (
        get_enhanced_unified_storage_api,
    )
    UNIFIED_STORAGE_AVAILABLE = True
except ImportError:
    UNIFIED_STORAGE_AVAILABLE = False

logger = logging.getLogger(__name__)


class FlaskEvidenceAPI:
    """Flask-compatible Evidence table API handler"""
    
    def __init__(self, app=None, storage_path: str = "evidence_table.json"):
        self.evidence_table = EnhancedEvidenceTable(storage_path)
        self.app = app
        
        if app:
            self.register_routes(app)
    
    def register_routes(self, app):
        """Register Flask routes"""
        # Evidence management routes
        app.add_url_rule("/api/evidence", "get_evidence_table", self.get_evidence_table, methods=["GET"])
        app.add_url_rule("/api/evidence", "add_evidence_entry", self.add_evidence_entry, methods=["POST"])
        app.add_url_rule("/api/evidence/<evidence_id>", "update_evidence_entry", self.update_evidence_entry, methods=["PUT"])
        app.add_url_rule("/api/evidence/<evidence_id>", "delete_evidence_entry", self.delete_evidence_entry, methods=["DELETE"])
        
        # Evidence download route
        app.add_url_rule("/api/evidence/<evidence_id>/download", "download_evidence", self.download_evidence, methods=["GET"])
        
        # Filtering and search routes
        app.add_url_rule("/api/evidence/filter", "get_filtered_evidence", self.get_filtered_evidence, methods=["GET"])
        app.add_url_rule("/api/evidence/stats", "get_evidence_stats", self.get_evidence_stats, methods=["GET"])
        app.add_url_rule("/api/evidence/export", "export_evidence_data", self.export_evidence_data, methods=["GET"])
        
        logger.info("Flask Evidence API routes registered")
    
    def get_evidence_table(self):
        """Get complete evidence table data"""
        try:
            data = self.evidence_table.export_to_dict()
            # Format for frontend compatibility
            evidence_list = []
            
            # evidence_entries is a list, not a dict
            evidence_entries = data.get("evidence_entries", [])
            if isinstance(evidence_entries, list):
                for evidence_data in evidence_entries:
                    evidence_entry = {
                        "evidence_id": evidence_data.get("id", evidence_data.get("evidence_id", "unknown")),
                        "object_id": evidence_data.get("object_id"),
                        "filename": evidence_data.get("source_document", "Unknown"),
                        "description": evidence_data.get("content", "")[:200],
                        "evidence_source": evidence_data.get("evidence_source", "primary"),  # NEW: PRIMARY/SECONDARY
                        "status": "analyzed" if evidence_data.get("relevance_score", 0) > 0 else "stored",
                        "file_size": len(evidence_data.get("content", "")),  # Approximate
                        "upload_date": evidence_data.get("created_at"),
                        "phase": evidence_data.get("phase", "unknown"),
                        "tags": ", ".join(evidence_data.get("key_terms", [])),
                        "facts": evidence_data.get("supporting_facts", []),
                        "research_query": evidence_data.get("research_query"),  # NEW: Research query
                        "research_confidence": evidence_data.get("research_confidence", 0.0),  # NEW: Confidence
                    }
                    evidence_list.append(evidence_entry)
            
            return jsonify({"evidence": evidence_list, "total": len(evidence_list)})
        except Exception as e:
            logger.error(f"Failed to get evidence table: {e}")
            return jsonify({"error": str(e)}), 500
    
    def add_evidence_entry(self):
        """Add new evidence entry"""
        try:
            data = request.get_json()
            
            # Create evidence entry from request data
            evidence = EvidenceEntry(
                source_document=data.get("source_document", ""),
                page_section=data.get("page_section", ""),
                content=data.get("content", ""),
                evidence_type=EvidenceType(data.get("evidence_type", "documentary")),
                evidence_source=EvidenceSource(data.get("evidence_source", "primary")),  # NEW: PRIMARY/SECONDARY
                relevance_score=float(data.get("relevance_score", 0.0)),
                relevance_level=RelevanceLevel(data.get("relevance_level", "unknown")),
                bluebook_citation=data.get("bluebook_citation", ""),
                privilege_marker=PrivilegeMarker(data.get("privilege_marker", "none")),
                extracted_date=data.get("extracted_date"),
                witness_name=data.get("witness_name"),
                key_terms=data.get("key_terms", []),
                notes=data.get("notes", ""),
                research_query=data.get("research_query"),  # NEW: Research query
                research_confidence=float(data.get("research_confidence", 0.0)),  # NEW: Confidence
                created_by=data.get("created_by", "user")
            )
            
            evidence_id = self.evidence_table.add_evidence(evidence)
            
            return jsonify({
                "success": True,
                "evidence_id": evidence_id,
                "message": "Evidence entry added successfully"
            })
        
        except Exception as e:
            logger.error(f"Failed to add evidence entry: {e}")
            return jsonify({"error": str(e)}), 400
    
    def update_evidence_entry(self, evidence_id):
        """Update existing evidence entry"""
        try:
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
            
            success = self.evidence_table.update_evidence(evidence_id, data)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "Evidence entry updated successfully"
                })
            else:
                return jsonify({"error": "Evidence entry not found"}), 404
        
        except Exception as e:
            logger.error(f"Failed to update evidence entry: {e}")
            return jsonify({"error": str(e)}), 400
    
    def delete_evidence_entry(self, evidence_id):
        """Delete evidence entry"""
        try:
            success = self.evidence_table.delete_evidence(evidence_id)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "Evidence entry deleted successfully"
                })
            else:
                return jsonify({"error": "Evidence entry not found"}), 404
        
        except Exception as e:
            logger.error(f"Failed to delete evidence entry: {e}")
            return jsonify({"error": str(e)}), 400
    
    def get_filtered_evidence(self):
        """Get filtered evidence entries"""
        try:
            # Parse filter parameters
            evidence_type = None
            if "evidence_type" in request.args:
                evidence_type = EvidenceType(request.args["evidence_type"])
            
            relevance_level = None
            if "relevance_level" in request.args:
                relevance_level = RelevanceLevel(request.args["relevance_level"])
            
            source_document = request.args.get("source_document")
            
            min_relevance_score = None
            if "min_relevance_score" in request.args:
                min_relevance_score = float(request.args["min_relevance_score"])
            
            # Get filtered results
            results = self.evidence_table.get_evidence_by_filters(
                evidence_type=evidence_type,
                relevance_level=relevance_level,
                source_document=source_document,
                min_relevance_score=min_relevance_score,
            )
            
            return jsonify({
                "evidence_entries": [entry.to_dict() for entry in results],
                "total_count": len(results),
            })
        
        except Exception as e:
            logger.error(f"Failed to get filtered evidence: {e}")
            return jsonify({"error": str(e)}), 400
    
    def get_evidence_stats(self):
        """Get evidence table statistics"""
        try:
            stats = self.evidence_table.get_stats()
            return jsonify(stats)
        except Exception as e:
            logger.error(f"Failed to get evidence stats: {e}")
            return jsonify({"error": str(e)}), 500
    
    def export_evidence_data(self):
        """Export evidence data in various formats"""
        try:
            export_format = request.args.get("format", "json")
            
            if export_format == "json":
                data = self.evidence_table.export_to_dict()
                return jsonify(data)
            
            elif export_format == "csv":
                # Convert to CSV format
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow([
                    "Evidence ID", "Source Document", "Page/Section", "Content",
                    "Evidence Type", "Relevance Score", "Bluebook Citation",
                    "Created At"
                ])
                
                # Write evidence entries
                for entry in self.evidence_table.evidence_entries.values():
                    writer.writerow([
                        entry.evidence_id,
                        entry.source_document,
                        entry.page_section,
                        entry.content[:200] + "..." if len(entry.content) > 200 else entry.content,
                        entry.evidence_type.value,
                        entry.relevance_score,
                        entry.bluebook_citation,
                        entry.created_at
                    ])
                
                csv_content = output.getvalue()
                output.close()
                
                response = jsonify(csv_content)
                response.headers["Content-Type"] = "text/csv"
                response.headers["Content-Disposition"] = "attachment; filename=evidence_table.csv"
                return response
            
            else:
                return jsonify(
                    {"error": "Unsupported export format. Use 'json' or 'csv'"}
                ), 400
        
        except Exception as e:
            logger.error(f"Failed to export evidence data: {e}")
            return jsonify({"error": str(e)}), 500
    
    def download_evidence(self, evidence_id):
        """Download evidence file by evidence_id using unified storage"""
        try:
            # Get evidence entry from table
            evidence = self.evidence_table.get_evidence(evidence_id)
            
            if not evidence:
                return jsonify({"error": "Evidence entry not found"}), 404
            
            # Check if we have an object_id for unified storage
            if not evidence.object_id:
                return jsonify(
                    {"error": "No storage object_id available for this evidence"}
                ), 404
            
            # Retrieve from unified storage if available
            if UNIFIED_STORAGE_AVAILABLE:
                try:
                    import asyncio
                    
                    unified_storage = get_enhanced_unified_storage_api()
                    
                    # Run async retrieval in sync context
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        storage_result = loop.run_until_complete(
                            unified_storage.get_evidence(
                                object_id=evidence.object_id,
                                target_tier="s3"  # Get raw file from S3/local storage
                            )
                        )
                    finally:
                        loop.close()
                    
                    if storage_result and "content" in storage_result:
                        # Return file content with appropriate headers
                        filename = evidence.source_document or f"evidence_{evidence_id}"
                        content_type = storage_result.get("content_type", "application/octet-stream")
                        
                        return send_file(
                            BytesIO(storage_result["content"]),
                            mimetype=content_type,
                            as_attachment=True,
                            download_name=filename
                        )
                    else:
                        return jsonify({"error": "File content not found in storage"}), 404
                        
                except Exception as storage_error:
                    logger.error(f"Unified storage retrieval failed: {storage_error}")
                    return jsonify(
                        {"error": f"Storage retrieval failed: {str(storage_error)}"}
                    ), 500
            else:
                return jsonify({"error": "Unified storage not available"}), 503
        
        except Exception as e:
            logger.error(f"Failed to download evidence: {e}")
            return jsonify({"error": str(e)}), 500
