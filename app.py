"""
Enhanced LawyerFactory Web Application
Flask backend with WebSocket support for real-time case initiation workflow.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import uuid
import mimetypes
from werkzeug.utils import secure_filename

from flask import Flask, render_template, request, jsonify, send_file, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import eventlet

# Import LawyerFactory components
try:
    from knowledge_graph import KnowledgeGraph
    from knowledge_graph_extensions import extend_knowledge_graph
except ImportError as e:
    logger.error(f"Failed to import knowledge graph: {e}")
    KnowledgeGraph = None

try:
    from lawyerfactory.enhanced_workflow import EnhancedWorkflowManager
except ImportError as e:
    logger.error(f"Failed to import enhanced workflow: {e}")
    EnhancedWorkflowManager = None

try:
    from maestro.enhanced_maestro import EnhancedMaestro
    from maestro.workflow_models import WorkflowPhase
except ImportError as e:
    logger.error(f"Failed to import maestro: {e}")
    EnhancedMaestro = None
    WorkflowPhase = None

try:
    from lawyerfactory.document_generator.generator import DocumentGenerator
except ImportError as e:
    logger.error(f"Failed to import document generator: {e}")
    DocumentGenerator = None

eventlet.monkey_patch()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global application state
app_state = {
    'knowledge_graph': None,
    'workflow_manager': None,
    'active_sessions': {},  # session_id -> workflow_data
    'upload_sessions': {}   # upload_session_id -> upload_data
}

def initialize_components():
    """Initialize backend components"""
    try:
        # Create necessary directories
        Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
        Path('knowledge_graphs').mkdir(exist_ok=True)
        Path('workflow_storage').mkdir(exist_ok=True)
        
        # Initialize knowledge graph
        app_state['knowledge_graph'] = KnowledgeGraph('knowledge_graphs/main.db')
        
        # Initialize workflow manager
        app_state['workflow_manager'] = EnhancedWorkflowManager(
            knowledge_graph_path='knowledge_graphs/main.db',
            storage_path='workflow_storage'
        )
        
        logger.info("Backend components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise

# API Routes

@app.route('/')
def index():
    """Serve the enhanced factory interface"""
    return render_template('enhanced_factory.html')

@app.route('/api/workflows', methods=['GET'])
def list_workflows():
    """List all workflows"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        workflows = loop.run_until_complete(app_state['workflow_manager'].list_workflows())
        loop.close()
        
        return jsonify({
            'success': True,
            'workflows': workflows
        })
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/workflow', methods=['POST'])
def create_workflow():
    """Create a new lawsuit generation workflow"""
    try:
        data = request.get_json()
        case_name = data.get('case_name')
        case_folder = data.get('case_folder', '')
        case_description = data.get('case_description', '')
        uploaded_files = data.get('uploaded_files', [])
        
        if not case_name:
            return jsonify({'success': False, 'error': 'Case name is required'}), 400
        
        # Create unique session ID
        session_id = f"workflow_{uuid.uuid4().hex[:12]}"
        
        # Initialize workflow asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if case_folder:
            workflow_session_id = loop.run_until_complete(
                app_state['workflow_manager'].create_lawsuit_workflow(
                    case_name=case_name,
                    case_folder=case_folder,
                    case_description=case_description
                )
            )
        else:
            # Use uploaded files
            input_documents = [os.path.join(app.config['UPLOAD_FOLDER'], f) for f in uploaded_files]
            workflow_session_id = loop.run_until_complete(
                app_state['workflow_manager'].maestro.start_workflow(
                    case_name=case_name,
                    input_documents=input_documents,
                    initial_context={
                        'case_description': case_description,
                        'workflow_type': 'lawsuit_generation'
                    }
                )
            )
        
        loop.close()
        
        # Store session data
        app_state['active_sessions'][session_id] = {
            'workflow_session_id': workflow_session_id,
            'case_name': case_name,
            'case_description': case_description,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        # Start monitoring workflow
        socketio.start_background_task(monitor_workflow, session_id, workflow_session_id)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'workflow_session_id': workflow_session_id
        })
        
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/workflow/<session_id>/status', methods=['GET'])
def get_workflow_status(session_id):
    """Get workflow status"""
    try:
        if session_id not in app_state['active_sessions']:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        workflow_session_id = app_state['active_sessions'][session_id]['workflow_session_id']
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        status = loop.run_until_complete(
            app_state['workflow_manager'].get_workflow_status(workflow_session_id)
        )
        loop.close()
        
        return jsonify({
            'success': True,
            'status': status,
            'session_data': app_state['active_sessions'][session_id]
        })
        
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/workflow/<session_id>/approve', methods=['POST'])
def approve_workflow_phase(session_id):
    """Approve a workflow phase transition"""
    try:
        data = request.get_json()
        approval_decision = data.get('approved', True)
        feedback = data.get('feedback', '')
        
        if session_id not in app_state['active_sessions']:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        workflow_session_id = app_state['active_sessions'][session_id]['workflow_session_id']
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            app_state['workflow_manager'].submit_human_feedback(
                workflow_session_id,
                approval_decision,
                feedback
            )
        )
        loop.close()
        
        # Emit status update via WebSocket
        socketio.emit('workflow_status_update', {
            'session_id': session_id,
            'event': 'phase_approved' if approval_decision else 'phase_rejected',
            'feedback': feedback
        }, room=session_id)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Failed to approve workflow phase: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload for case documents"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False, 
                'error': f'File type {file_ext} not allowed. Allowed types: {", ".join(allowed_extensions)}'
            }), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        file.save(file_path)
        
        # Start document processing
        upload_session_id = f"upload_{uuid.uuid4().hex[:8]}"
        app_state['upload_sessions'][upload_session_id] = {
            'filename': unique_filename,
            'original_filename': filename,
            'file_path': file_path,
            'upload_time': datetime.now().isoformat(),
            'status': 'uploaded'
        }
        
        # Process document asynchronously
        socketio.start_background_task(process_uploaded_document, upload_session_id, file_path)
        
        return jsonify({
            'success': True,
            'upload_session_id': upload_session_id,
            'filename': unique_filename,
            'original_filename': filename
        })
        
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/knowledge-graph/entities', methods=['GET'])
def get_entities():
    """Get entities from knowledge graph"""
    try:
        entity_type = request.args.get('type')
        search_query = request.args.get('search')
        
        if search_query:
            # Semantic search
            results = app_state['knowledge_graph'].semantic_search(search_query, top_k=20)
        else:
            # Query by type or get all
            results = app_state['knowledge_graph'].query_entities(entity_type=entity_type)
        
        return jsonify({
            'success': True,
            'entities': results
        })
        
    except Exception as e:
        logger.error(f"Failed to get entities: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/knowledge-graph/relationships', methods=['GET'])
def get_relationships():
    """Get relationships from knowledge graph"""
    try:
        entity_id = request.args.get('entity_id')
        
        if entity_id:
            # Get relationships for specific entity
            relationships = app_state['knowledge_graph'].get_entity_relationships(entity_id)
        else:
            # Get all relationships (limited)
            relationships = app_state['knowledge_graph'].get_all_relationships(limit=100)
        
        return jsonify({
            'success': True,
            'relationships': relationships
        })
        
    except Exception as e:
        logger.error(f"Failed to get relationships: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/workflow/<session_id>/document', methods=['GET'])
def download_generated_document(session_id):
    """Download generated lawsuit document"""
    try:
        if session_id not in app_state['active_sessions']:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        workflow_session_id = app_state['active_sessions'][session_id]['workflow_session_id']
        
        # Get workflow status to check if document is ready
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        status = loop.run_until_complete(
            app_state['workflow_manager'].get_workflow_status(workflow_session_id)
        )
        loop.close()
        
        if status.get('current_phase') != WorkflowPhase.ORCHESTRATION.value:
            return jsonify({
                'success': False, 
                'error': 'Document not ready yet. Workflow still in progress.'
            }), 400
        
        # Generate document if not already generated
        document_path = f"workflow_storage/{workflow_session_id}_complaint.txt"
        
        if not os.path.exists(document_path):
            # Generate document using document generator
            case_data = app_state['knowledge_graph'].get_case_facts(workflow_session_id)
            research_findings = {}  # Would come from research bot results
            
            generator = DocumentGenerator(case_data, research_findings)
            document_content = generator.generate('complaint')
            
            # Save document
            with open(document_path, 'w') as f:
                f.write(document_content)
        
        return send_file(
            document_path,
            as_attachment=True,
            download_name=f"{app_state['active_sessions'][session_id]['case_name']}_complaint.txt",
            mimetype='text/plain'
        )
        
    except Exception as e:
        logger.error(f"Failed to generate document: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# WebSocket Events

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_session')
def handle_join_session(data):
    """Join a workflow session for real-time updates"""
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        emit('joined_session', {'session_id': session_id})
        logger.info(f"Client {request.sid} joined session {session_id}")

@socketio.on('leave_session')
def handle_leave_session(data):
    """Leave a workflow session"""
    session_id = data.get('session_id')
    if session_id:
        leave_room(session_id)
        emit('left_session', {'session_id': session_id})
        logger.info(f"Client {request.sid} left session {session_id}")

# Background Tasks

def monitor_workflow(session_id, workflow_session_id):
    """Monitor workflow progress and emit updates"""
    logger.info(f"Starting workflow monitoring for session {session_id}")
    
    try:
        last_phase = None
        last_progress = 0
        
        while session_id in app_state['active_sessions']:
            try:
                # Get current status
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                status = loop.run_until_complete(
                    app_state['workflow_manager'].get_workflow_status(workflow_session_id)
                )
                loop.close()
                
                current_phase = status.get('current_phase')
                current_progress = status.get('progress_percentage', 0)
                
                # Check for phase changes
                if current_phase != last_phase:
                    socketio.emit('workflow_phase_change', {
                        'session_id': session_id,
                        'from_phase': last_phase,
                        'to_phase': current_phase,
                        'status': status
                    }, room=session_id)
                    last_phase = current_phase
                
                # Check for progress changes
                if abs(current_progress - last_progress) >= 5:  # 5% threshold
                    socketio.emit('workflow_progress_update', {
                        'session_id': session_id,
                        'progress': current_progress,
                        'status': status
                    }, room=session_id)
                    last_progress = current_progress
                
                # Check if workflow is complete
                if status.get('status') in ['completed', 'failed']:
                    socketio.emit('workflow_completed', {
                        'session_id': session_id,
                        'final_status': status.get('status'),
                        'status': status
                    }, room=session_id)
                    
                    # Update session status
                    app_state['active_sessions'][session_id]['status'] = status.get('status')
                    break
                
                # Check for human approval needed
                if status.get('pending_human_approval'):
                    socketio.emit('approval_required', {
                        'session_id': session_id,
                        'phase': current_phase,
                        'status': status
                    }, room=session_id)
                
                eventlet.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring workflow {session_id}: {e}")
                eventlet.sleep(10)  # Wait longer on error
                
    except Exception as e:
        logger.error(f"Failed to monitor workflow {session_id}: {e}")
        socketio.emit('workflow_error', {
            'session_id': session_id,
            'error': str(e)
        }, room=session_id)

def process_uploaded_document(upload_session_id, file_path):
    """Process uploaded document and extract entities"""
    logger.info(f"Processing uploaded document: {upload_session_id}")
    
    try:
        # Update status
        app_state['upload_sessions'][upload_session_id]['status'] = 'processing'
        
        socketio.emit('document_processing_update', {
            'upload_session_id': upload_session_id,
            'status': 'processing',
            'message': 'Extracting text and entities...'
        })
        
        # Process document through knowledge graph ingestion
        pipeline = app_state['knowledge_graph'].DocumentIngestionPipeline(app_state['knowledge_graph'])
        document_id = pipeline.ingest(file_path)
        
        # Get extracted entities
        facts = app_state['knowledge_graph'].get_case_facts(document_id)
        
        # Update status
        app_state['upload_sessions'][upload_session_id].update({
            'status': 'completed',
            'document_id': document_id,
            'entities_extracted': len(facts.get('entities', [])),
            'relationships_found': len(facts.get('relationships', []))
        })
        
        socketio.emit('document_processing_complete', {
            'upload_session_id': upload_session_id,
            'document_id': document_id,
            'entities': facts.get('entities', []),
            'relationships': facts.get('relationships', []),
            'stats': {
                'entities_extracted': len(facts.get('entities', [])),
                'relationships_found': len(facts.get('relationships', []))
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to process document {upload_session_id}: {e}")
        app_state['upload_sessions'][upload_session_id]['status'] = 'failed'
        app_state['upload_sessions'][upload_session_id]['error'] = str(e)
        
        socketio.emit('document_processing_error', {
            'upload_session_id': upload_session_id,
            'error': str(e)
        })

if __name__ == '__main__':
    initialize_components()
    
    # Run the application
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
