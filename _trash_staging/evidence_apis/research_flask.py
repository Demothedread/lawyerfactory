"""
Flask Research API routes for LawyerFactory
RESTful API endpoints for triggering legal research with Tavily integration
Extracts keywords from PRIMARY evidence → executes Tavily search → stores SECONDARY evidence
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for lawyerfactory imports
src_path = Path(__file__).parent.parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from flask import jsonify, request
from flask_socketio import emit

from lawyerfactory.agents.research.research import ResearchBot
from lawyerfactory.storage.evidence.table import (
    EnhancedEvidenceTable,
    EvidenceSource,
)

logger = logging.getLogger(__name__)


class FlaskResearchAPI:
    """Flask-compatible Research API handler"""
    
    def __init__(self, app=None, socketio=None):
        self.app = app
        self.socketio = socketio
        self.research_bot = ResearchBot()
        self.evidence_table = EnhancedEvidenceTable()
        
        if app:
            self.register_routes(app)
    
    def register_routes(self, app):
        """Register Flask routes"""
        app.add_url_rule(
            "/api/research/execute",
            "execute_research",
            self.execute_research,
            methods=["POST"]
        )
        app.add_url_rule(
            "/api/research/extract-keywords",
            "extract_keywords",
            self.extract_keywords,
            methods=["POST"]
        )
        app.add_url_rule(
            "/api/research/status/<research_id>",
            "get_research_status",
            self.get_research_status,
            methods=["GET"]
        )
        
        logger.info("Flask Research API routes registered")
    
    def execute_research(self):
        """
        Execute research based on PRIMARY evidence keywords.
        
        Request JSON:
        {
            "case_id": "case_123",
            "evidence_id": "evidence_456",  # PRIMARY evidence to research from
            "keywords": ["tesla", "autonomous vehicle", "liability"],  # Optional: override keywords
            "max_results": 5  # Optional: max results per source
        }
        
        Returns:
        {
            "research_id": "research_789",
            "status": "processing",
            "message": "Research started"
        }
        """
        try:
            data = request.get_json()
            
            case_id = data.get("case_id")
            evidence_id = data.get("evidence_id")
            keywords = data.get("keywords")
            max_results = data.get("max_results", 5)
            
            if not case_id:
                return jsonify({"error": "case_id is required"}), 400
            
            # If keywords not provided, extract from evidence
            if not keywords and evidence_id:
                evidence = self.evidence_table.get_evidence(evidence_id)
                
                if not evidence:
                    return jsonify({"error": f"Evidence {evidence_id} not found"}), 404
                
                # Check if evidence is PRIMARY
                if evidence.evidence_source != EvidenceSource.PRIMARY:
                    return jsonify({
                        "error": "Can only research from PRIMARY evidence"
                    }), 400
                
                # Extract keywords from evidence content
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    keywords = loop.run_until_complete(
                        self.research_bot.extract_keywords_from_evidence(
                            evidence.content,
                            case_type=None
                        )
                    )
                finally:
                    loop.close()
                
                logger.info(f"Extracted {len(keywords)} keywords from evidence {evidence_id}")
            
            if not keywords:
                return jsonify({"error": "No keywords provided or extracted"}), 400
            
            # Generate research ID
            import uuid
            research_id = str(uuid.uuid4())
            
            # Emit Socket.IO event: research started
            if self.socketio:
                self.socketio.emit('research_started', {
                    'research_id': research_id,
                    'case_id': case_id,
                    'evidence_id': evidence_id,
                    'keywords': keywords,
                    'status': 'processing'
                })
            
            # Execute research asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                research_result = loop.run_until_complete(
                    self.research_bot.research_from_evidence_keywords(
                        case_id=case_id,
                        evidence_id=evidence_id or "manual",
                        keywords=keywords,
                        max_results_per_source=max_results,
                    )
                )
            finally:
                loop.close()
            
            # Emit Socket.IO event: research completed
            if self.socketio:
                self.socketio.emit('research_completed', {
                    'research_id': research_id,
                    'case_id': case_id,
                    'evidence_id': evidence_id,
                    'status': 'completed',
                    'total_sources': research_result.get('total_sources', 0),
                    'secondary_evidence_ids': research_result.get('secondary_evidence_ids', []),
                    'confidence_score': research_result.get('confidence_score', 0.0),
                })
            
            return jsonify({
                "research_id": research_id,
                "status": "completed",
                "result": research_result,
                "message": f"Research completed with {len(research_result.get('secondary_evidence_ids', []))} SECONDARY evidence entries"
            })
        
        except Exception as e:
            logger.error(f"Research execution failed: {e}")
            
            # Emit Socket.IO event: research failed
            if self.socketio:
                self.socketio.emit('research_failed', {
                    'research_id': research_id if 'research_id' in locals() else 'unknown',
                    'case_id': data.get('case_id') if data else 'unknown',
                    'status': 'failed',
                    'error': str(e)
                })
            
            return jsonify({"error": str(e)}), 500
    
    def extract_keywords(self):
        """
        Extract keywords from evidence content without executing research.
        
        Request JSON:
        {
            "evidence_id": "evidence_456",  # Evidence to extract from
            "content": "Optional text content"  # Or provide content directly
        }
        
        Returns:
        {
            "keywords": ["keyword1", "keyword2", ...],
            "count": 10
        }
        """
        try:
            data = request.get_json()
            
            evidence_id = data.get("evidence_id")
            content = data.get("content")
            
            # Get content from evidence if not provided
            if not content and evidence_id:
                evidence = self.evidence_table.get_evidence(evidence_id)
                if not evidence:
                    return jsonify({"error": f"Evidence {evidence_id} not found"}), 404
                content = evidence.content
            
            if not content:
                return jsonify({"error": "No content provided or found"}), 400
            
            # Extract keywords
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                keywords = loop.run_until_complete(
                    self.research_bot.extract_keywords_from_evidence(
                        content,
                        case_type=None
                    )
                )
            finally:
                loop.close()
            
            return jsonify({
                "keywords": keywords,
                "count": len(keywords)
            })
        
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    def get_research_status(self, research_id):
        """
        Get status of a research request.
        (Placeholder for future async research tracking)
        """
        # TODO: Implement async research status tracking
        return jsonify({
            "research_id": research_id,
            "status": "unknown",
            "message": "Research status tracking not yet implemented"
        })

