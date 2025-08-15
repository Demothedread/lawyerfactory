"""
Enhanced LawyerFactory Web Application
Flask backend with WebSocket support for real-time case initiation workflow.
"""

import asyncio
import json
import logging
import mimetypes
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import eventlet
from flask import Flask, jsonify, render_template, request, send_file, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename

# Disable Eventlet's green DNS to prevent DNS resolution timeouts
os.environ['EVENTLET_NO_GREENDNS'] = 'yes'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import LawyerFactory components
try:
    from knowledge_graph import KnowledgeGraph, DocumentIngestionPipeline
    from knowledge_graph_extensions import extend_knowledge_graph
except ImportError as e:
    logger.error(f"Failed to import knowledge graph: {e}")
    KnowledgeGraph = None
    DocumentIngestionPipeline = None

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

try:
    from lawyerfactory.prompt_integration import create_prompt_processor
    from lawyerfactory.mcp_memory_integration import MCPMemoryManager, PneumonicMemoryIntegration
except ImportError as e:
    logger.error(f"Failed to import prompt integration or MCP memory: {e}")
    create_prompt_processor = None
    MCPMemoryManager = None
    PneumonicMemoryIntegration = None

# Monkey patch only what's needed for Flask-SocketIO, completely excluding socket to avoid DNS issues
eventlet.monkey_patch(socket=False, select=True, thread=True, time=True, os=False)

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
        if KnowledgeGraph:
            app_state['knowledge_graph'] = KnowledgeGraph('knowledge_graphs/main.db')
        
        # Initialize workflow manager
        if EnhancedWorkflowManager:
            app_state['workflow_manager'] = EnhancedWorkflowManager(
                knowledge_graph_path='knowledge_graphs/main.db',
                storage_path='workflow_storage'
            )
        
        # Initialize MCP memory integration
        if MCPMemoryManager and PneumonicMemoryIntegration:
            # Create MCP tools interface for memory operations
            mcp_tools = {
                'create_entities': lambda data: None,  # Will be replaced with actual MCP calls
                'search_nodes': lambda data: [],
                'open_nodes': lambda data: [],
                'add_observations': lambda data: None
            }
            
            app_state['mcp_memory_manager'] = MCPMemoryManager(mcp_tools)
            app_state['pneumonic_integration'] = PneumonicMemoryIntegration(app_state['mcp_memory_manager'])
            logger.info("MCP memory integration initialized")
        
        # Initialize prompt processor with MCP memory integration
        if create_prompt_processor and app_state['workflow_manager']:
            app_state['prompt_processor'] = create_prompt_processor(
                maestro=app_state['workflow_manager'].maestro,
                llm_service=None,  # Can be configured later with actual LLM service
                mcp_memory_manager=app_state.get('mcp_memory_manager')
            )
            logger.info("Prompt processor initialized with MCP memory integration")
        
        logger.info("Backend components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise

# API Routes

@app.route('/')
def index():
    """Serve the enhanced factory interface"""
    return render_template('enhanced_factory.html')

@app.route('/harvard-workflow')
def harvard_workflow_visualization():
    """Serve the Harvard-themed workflow visualization interface"""
    return render_template('harvard_workflow_visualization.html')

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
        
        workflow_session_id = loop.run_until_complete(
            app_state['workflow_manager'].create_lawsuit_workflow(
                case_name=case_name,
                session_id=session_id,
                case_folder=case_folder,
                case_description=case_description,
                uploaded_documents=uploaded_files
            )
        )
        loop.close()
        
        # Store session
        app_state['active_sessions'][session_id] = {
            'case_name': case_name,
            'workflow_session_id': workflow_session_id,
            'start_time': datetime.now().isoformat()
        }
        
        # Start monitoring
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
        # FIX: Pass session_id as explicit parameter
        status = asyncio.run(app_state['workflow_manager'].get_workflow_status(session_id=session_id))
        if status:
            return jsonify({'success': True, 'status': status})
        else:
            return jsonify({'success': False, 'error': 'Workflow not found'}), 404
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/workflow/<session_id>/approve', methods=['POST'])
def approve_workflow_phase(session_id):
    """Approve a workflow phase transition"""
    try:
        data = request.get_json()
        phase_to_approve = data.get('phase')
        
        if not phase_to_approve:
            return jsonify({'success': False, 'error': 'Phase not specified'}), 400
            
        asyncio.run(app_state['workflow_manager'].approve_phase(session_id, phase_to_approve))
        
        return jsonify({'success': True, 'message': f'Phase {phase_to_approve} approved'})
        
    except Exception as e:
        logger.error(f"Failed to approve phase: {e}")
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
        entities = app_state['knowledge_graph'].query_entities()
        return jsonify({'success': True, 'entities': entities})
    except Exception as e:
        logger.error(f"Failed to get entities: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/knowledge-graph/relationships', methods=['GET'])
def get_relationships():
    """Get relationships from knowledge graph"""
    try:
        relationships = app_state['knowledge_graph'].query_relationships()
        return jsonify({'success': True, 'relationships': relationships})
    except Exception as e:
        logger.error(f"Failed to get relationships: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/workflow/<session_id>/document', methods=['GET'])
def download_generated_document(session_id):
    """Download generated lawsuit document"""
    try:
        workflow = asyncio.run(app_state['workflow_manager'].get_workflow_status(session_id))
        if not workflow or 'output_document_path' not in workflow:
            return jsonify({'success': False, 'error': 'Document not found'}), 404
        
        doc_path = workflow['output_document_path']
        if not os.path.exists(doc_path):
            return jsonify({'success': False, 'error': 'File not found on server'}), 404
            
        return send_file(doc_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Failed to download document: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# SocketIO Event Handlers

@socketio.on('connect')
def handle_connect():
    """Handle new client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connection_ack', {'message': 'Connected to LawyerFactory backend'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_session')
def handle_join_session(data):
    """Join a client to a specific session room"""
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        logger.info(f"Client {request.sid} joined session {session_id}")
        emit('session_joined', {'session_id': session_id}, room=session_id)

@socketio.on('leave_session')
def handle_leave_session(data):
    """Remove a client from a specific session room"""
    session_id = data.get('session_id')
    if session_id:
        leave_room(session_id)
        logger.info(f"Client {request.sid} left session {session_id}")
        emit('session_left', {'session_id': session_id}, room=session_id)


@socketio.on('analyze_case_prompt')
def handle_analyze_case_prompt(data):
    """Handle LLM-powered case prompt analysis"""
    try:
        case_prompt = data.get('case_prompt', '').strip()
        session_id = data.get('session_id')
        document_type_hint = data.get('document_type_hint')
        
        if not case_prompt:
            emit('prompt_analysis_error', {
                'session_id': session_id,
                'error': 'No case prompt provided',
                'timestamp': datetime.now().isoformat()
            })
            return
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        logger.info(f"Analyzing case prompt for session {session_id}")
        
        if app_state['prompt_processor']:
            # Process the prompt asynchronously
            def process_prompt():
                try:
                    # Run the async prompt processing
                    result = asyncio.run(
                        app_state['prompt_processor'].process_case_prompt(
                            session_id=session_id,
                            case_prompt=case_prompt,
                            document_type_hint=document_type_hint,
                            socketio=socketio
                        )
                    )
                    
                    # Store result for later use
                    if 'success' not in result or result['success'] is not False:
                        app_state['active_sessions'][session_id] = {
                            'type': 'prompt_analysis',
                            'prompt_analysis': result,
                            'created_at': datetime.now().isoformat(),
                            'status': 'analysis_complete'
                        }
                        
                        # Store in MCP memory for pneumonic compression
                        if app_state.get('pneumonic_integration'):
                            asyncio.run(
                                app_state['pneumonic_integration'].capture_workflow_context(
                                    session_id=session_id,
                                    phase='prompt_analysis',
                                    context_data=result
                                )
                            )
                    
                except Exception as e:
                    logger.error(f"Prompt analysis failed for session {session_id}: {e}")
                    socketio.emit('prompt_analysis_error', {
                        'session_id': session_id,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Start processing in background thread
            socketio.start_background_task(process_prompt)
            
        else:
            emit('prompt_analysis_error', {
                'session_id': session_id,
                'error': 'Prompt processor not available',
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Error handling prompt analysis: {e}")
        emit('prompt_analysis_error', {
            'session_id': data.get('session_id'),
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('get_analysis_summary')
def handle_get_analysis_summary(data):
    """Get keyword summary for analyzed prompt"""
    try:
        session_id = data.get('session_id')
        
        if not session_id or session_id not in app_state['active_sessions']:
            emit('analysis_summary_error', {
                'session_id': session_id,
                'error': 'No analysis found for session'
            })
            return
        
        if app_state['prompt_processor']:
            summary = app_state['prompt_processor'].get_keyword_summary_for_ui(session_id)
            
            if summary:
                emit('analysis_summary', {
                    'session_id': session_id,
                    'summary': summary
                })
            else:
                emit('analysis_summary_error', {
                    'session_id': session_id,
                    'error': 'No summary available'
                })
        else:
            emit('analysis_summary_error', {
                'session_id': session_id,
                'error': 'Prompt processor not available'
            })
            
    except Exception as e:
        logger.error(f"Error getting analysis summary: {e}")
        emit('analysis_summary_error', {
            'session_id': data.get('session_id'),
            'error': str(e)
        })

@socketio.on('update_analysis_feedback')
def handle_update_analysis_feedback(data):
    """Update analysis with human feedback"""
    try:
        session_id = data.get('session_id')
        feedback = data.get('feedback', {})
        
        if not session_id:
            emit('feedback_update_error', {
                'error': 'No session ID provided'
            })
            return
        
        if app_state['prompt_processor']:
            def update_with_feedback():
                try:
                    updated_analysis = asyncio.run(
                        app_state['prompt_processor'].update_analysis_with_feedback(
                            session_id, feedback
                        )
                    )
                    
                    # Update stored session data
                    if session_id in app_state['active_sessions']:
                        app_state['active_sessions'][session_id]['prompt_analysis'] = updated_analysis
                        app_state['active_sessions'][session_id]['human_reviewed'] = True
                    
                    socketio.emit('analysis_updated', {
                        'session_id': session_id,
                        'analysis_result': updated_analysis
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to update analysis with feedback: {e}")
                    socketio.emit('feedback_update_error', {
                        'session_id': session_id,
                        'error': str(e)
                    })
            
            # Process feedback in background
            socketio.start_background_task(update_with_feedback)
        else:
            emit('feedback_update_error', {
                'session_id': session_id,
                'error': 'Prompt processor not available'
            })
            
    except Exception as e:
        logger.error(f"Error updating analysis feedback: {e}")
        emit('feedback_update_error', {
            'session_id': data.get('session_id'),
            'error': str(e)
        })

# Background Tasks

def monitor_workflow(session_id, workflow_session_id):
    """Monitor workflow progress and emit updates"""
    logger.info(f"Starting workflow monitoring for session {workflow_session_id}")
    
    try:
        while True:
            try:
                # DEBUG: Log the parameter being passed to get_workflow_status
                logger.debug(f"Calling get_workflow_status with session_id parameter: {workflow_session_id}")
                logger.debug(f"Parameter type: {type(workflow_session_id)}")
                
                # FIX: Pass workflow_session_id as the session_id parameter explicitly
                status = asyncio.run(app_state['workflow_manager'].get_workflow_status(session_id=workflow_session_id))
                
                if status:
                    socketio.emit('workflow_update', {
                        'session_id': workflow_session_id,
                        'status': status
                    }, room=workflow_session_id)
                
                if status and status.get('overall_status') in ['COMPLETED', 'FAILED']:
                    logger.info(f"Workflow {workflow_session_id} finished with status: {status.get('overall_status')}")
                    break
                    
            except Exception as e:
                logger.error(f"Error monitoring workflow {workflow_session_id}: {e}")
            
            socketio.sleep(10)  # Check every 10 seconds
            
    except Exception as e:
        logger.error(f"Workflow monitoring failed for {workflow_session_id}: {e}")

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
        if DocumentIngestionPipeline:
            pipeline = DocumentIngestionPipeline(app_state['knowledge_graph'])
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
        else:
            raise ImportError("DocumentIngestionPipeline not available")
        
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
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
