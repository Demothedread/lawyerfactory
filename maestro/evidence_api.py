"""
Enhanced Evidence Table API for LawyerFactory
RESTful API endpoints for evidence, facts, and claims management.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

try:
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except ImportError:
    web = None
    AIOHTTP_AVAILABLE = False

from .evidence_table import (
    EnhancedEvidenceTable, EvidenceEntry, FactAssertion, ClaimEntry,
    EvidenceType, RelevanceLevel, PrivilegeMarker
)

logger = logging.getLogger(__name__)


class EvidenceAPI:
    """Evidence table API handler"""
    
    def __init__(self, storage_path: str = "evidence_table.json"):
        self.evidence_table = EnhancedEvidenceTable(storage_path)
    
    async def get_evidence_table(self, request) -> web.Response:
        """Get complete evidence table data"""
        try:
            data = self.evidence_table.export_to_dict()
            return web.json_response(data)
        except Exception as e:
            logger.error(f"Failed to get evidence table: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def add_evidence_entry(self, request) -> web.Response:
        """Add new evidence entry"""
        try:
            data = await request.json()
            
            # Create evidence entry from request data
            evidence = EvidenceEntry(
                source_document=data.get("source_document", ""),
                page_section=data.get("page_section", ""),
                content=data.get("content", ""),
                evidence_type=EvidenceType(data.get("evidence_type", "documentary")),
                relevance_score=float(data.get("relevance_score", 0.0)),
                relevance_level=RelevanceLevel(data.get("relevance_level", "unknown")),
                bluebook_citation=data.get("bluebook_citation", ""),
                privilege_marker=PrivilegeMarker(data.get("privilege_marker", "none")),
                extracted_date=data.get("extracted_date"),
                witness_name=data.get("witness_name"),
                key_terms=data.get("key_terms", []),
                notes=data.get("notes", ""),
                created_by=data.get("created_by", "user")
            )
            
            evidence_id = self.evidence_table.add_evidence(evidence)
            
            return web.json_response({
                "success": True,
                "evidence_id": evidence_id,
                "message": "Evidence entry added successfully"
            })
        
        except Exception as e:
            logger.error(f"Failed to add evidence entry: {e}")
            return web.json_response({"error": str(e)}, status=400)
    
    async def update_evidence_entry(self, request) -> web.Response:
        """Update existing evidence entry"""
        try:
            evidence_id = request.match_info.get("evidence_id")
            data = await request.json()
            
            # Convert enum strings if provided
            if "evidence_type" in data:
                data["evidence_type"] = EvidenceType(data["evidence_type"])
            if "relevance_level" in data:
                data["relevance_level"] = RelevanceLevel(data["relevance_level"])
            if "privilege_marker" in data:
                data["privilege_marker"] = PrivilegeMarker(data["privilege_marker"])
            
            success = self.evidence_table.update_evidence(evidence_id, data)
            
            if success:
                return web.json_response({
                    "success": True,
                    "message": "Evidence entry updated successfully"
                })
            else:
                return web.json_response({"error": "Evidence entry not found"}, status=404)
        
        except Exception as e:
            logger.error(f"Failed to update evidence entry: {e}")
            return web.json_response({"error": str(e)}, status=400)
    
    async def delete_evidence_entry(self, request) -> web.Response:
        """Delete evidence entry"""
        try:
            evidence_id = request.match_info.get("evidence_id")
            
            success = self.evidence_table.delete_evidence(evidence_id)
            
            if success:
                return web.json_response({
                    "success": True,
                    "message": "Evidence entry deleted successfully"
                })
            else:
                return web.json_response({"error": "Evidence entry not found"}, status=404)
        
        except Exception as e:
            logger.error(f"Failed to delete evidence entry: {e}")
            return web.json_response({"error": str(e)}, status=400)
    
    async def get_filtered_evidence(self, request) -> web.Response:
        """Get filtered evidence entries"""
        try:
            query_params = request.query
            
            # Parse filter parameters
            evidence_type = None
            if "evidence_type" in query_params:
                evidence_type = EvidenceType(query_params["evidence_type"])
            
            relevance_level = None
            if "relevance_level" in query_params:
                relevance_level = RelevanceLevel(query_params["relevance_level"])
            
            source_document = query_params.get("source_document")
            
            min_relevance_score = None
            if "min_relevance_score" in query_params:
                min_relevance_score = float(query_params["min_relevance_score"])
            
            # Get filtered results
            results = self.evidence_table.get_evidence_by_filters(
                evidence_type=evidence_type,
                relevance_level=relevance_level,
                source_document=source_document,
                min_relevance_score=min_relevance_score
            )
            
            return web.json_response({
                "evidence_entries": [entry.to_dict() for entry in results],
                "total_count": len(results)
            })
        
        except Exception as e:
            logger.error(f"Failed to get filtered evidence: {e}")
            return web.json_response({"error": str(e)}, status=400)
    
    async def add_fact_assertion(self, request) -> web.Response:
        """Add new fact assertion"""
        try:
            data = await request.json()
            
            fact = FactAssertion(
                fact_text=data.get("fact_text", ""),
                confidence_score=float(data.get("confidence_score", 0.0)),
                chronological_order=int(data.get("chronological_order", 0)),
                date_occurred=data.get("date_occurred"),
                location=data.get("location", ""),
                parties_involved=data.get("parties_involved", [])
            )
            
            fact_id = self.evidence_table.add_fact(fact)
            
            return web.json_response({
                "success": True,
                "fact_id": fact_id,
                "message": "Fact assertion added successfully"
            })
        
        except Exception as e:
            logger.error(f"Failed to add fact assertion: {e}")
            return web.json_response({"error": str(e)}, status=400)
    
    async def link_evidence_to_fact(self, request) -> web.Response:
        """Link evidence entry to fact assertion"""
        try:
            data = await request.json()
            evidence_id = data.get("evidence_id")
            fact_id = data.get("fact_id")
            
            if not evidence_id or not fact_id:
                return web.json_response(
                    {"error": "Both evidence_id and fact_id are required"}, 
                    status=400
                )
            
            success = self.evidence_table.link_evidence_to_fact(evidence_id, fact_id)
            
            if success:
                return web.json_response({
                    "success": True,
                    "message": "Evidence linked to fact successfully"
                })
            else:
                return web.json_response(
                    {"error": "Evidence or fact not found"}, 
                    status=404
                )
        
        except Exception as e:
            logger.error(f"Failed to link evidence to fact: {e}")
            return web.json_response({"error": str(e)}, status=400)
    
    async def add_claim_entry(self, request) -> web.Response:
        """Add new claim entry"""
        try:
            data = await request.json()
            
            claim = ClaimEntry(
                cause_of_action=data.get("cause_of_action", ""),
                claim_strength=float(data.get("claim_strength", 0.0)),
                jurisdiction=data.get("jurisdiction", ""),
                statute_of_limitations=data.get("statute_of_limitations", ""),
                damages_sought=data.get("damages_sought", "")
            )
            
            claim_id = self.evidence_table.add_claim(claim)
            
            return web.json_response({
                "success": True,
                "claim_id": claim_id,
                "message": "Claim entry added successfully"
            })
        
        except Exception as e:
            logger.error(f"Failed to add claim entry: {e}")
            return web.json_response({"error": str(e)}, status=400)
    
    async def get_evidence_stats(self, request) -> web.Response:
        """Get evidence table statistics"""
        try:
            stats = self.evidence_table.get_stats()
            return web.json_response(stats)
        except Exception as e:
            logger.error(f"Failed to get evidence stats: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def export_evidence_data(self, request) -> web.Response:
        """Export evidence data in various formats"""
        try:
            export_format = request.query.get("format", "json")
            
            if export_format == "json":
                data = self.evidence_table.export_to_dict()
                return web.json_response(data)
            
            elif export_format == "csv":
                # Convert to CSV format
                import io
                import csv
                
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
                
                return web.Response(
                    text=csv_content,
                    content_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=evidence_table.csv"}
                )
            
            else:
                return web.json_response(
                    {"error": "Unsupported export format. Use 'json' or 'csv'"},
                    status=400
                )
        
        except Exception as e:
            logger.error(f"Failed to export evidence data: {e}")
            return web.json_response({"error": str(e)}, status=500)


def setup_evidence_routes(app, api_instance: EvidenceAPI):
    """Setup evidence API routes"""
    
    # Evidence management routes
    app.router.add_get("/api/evidence", api_instance.get_evidence_table)
    app.router.add_post("/api/evidence", api_instance.add_evidence_entry)
    app.router.add_put("/api/evidence/{evidence_id}", api_instance.update_evidence_entry)
    app.router.add_delete("/api/evidence/{evidence_id}", api_instance.delete_evidence_entry)
    
    # Filtering and search routes
    app.router.add_get("/api/evidence/filter", api_instance.get_filtered_evidence)
    app.router.add_get("/api/evidence/stats", api_instance.get_evidence_stats)
    app.router.add_get("/api/evidence/export", api_instance.export_evidence_data)
    
    # Facts management routes
    app.router.add_post("/api/facts", api_instance.add_fact_assertion)
    app.router.add_post("/api/evidence/link", api_instance.link_evidence_to_fact)
    
    # Claims management routes
    app.router.add_post("/api/claims", api_instance.add_claim_entry)
    
    logger.info("Evidence API routes configured")


# Legacy compatibility wrapper
async def handle_enhanced_evidence_table(request):
    """Enhanced evidence table handler for backward compatibility"""
    api = EvidenceAPI()
    return await api.get_evidence_table(request)