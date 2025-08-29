#!/usr/bin/env python3
"""
LawyerFactory Backend Server
Provides Socket.IO and REST API endpoints for the MultiSWARM UI
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import eventlet
eventlet.monkey_patch()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LawyerFactoryServer:
    """Main server class for LawyerFactory backend"""

    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)

        # Initialize Socket.IO with CORS
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            async_mode='eventlet',
            logger=True,
            engineio_logger=True
        )

        # Server state
        self.active_cases = {}
        self.agent_status = {
            'intake_agent': {'status': 'idle', 'progress': 0},
            'research_agent': {'status': 'idle', 'progress': 0},
            'drafting_agent': {'status': 'idle', 'progress': 0},
            'review_agent': {'status': 'idle', 'progress': 0},
            'orchestration_agent': {'status': 'idle', 'progress': 0}
        }

        self.phase_progress = {
            'A01_Intake': 0,
            'A02_Research': 0,
            'A03_Outline': 0,
            'B01_Review': 0,
            'B02_Drafting': 0,
            'C01_Editing': 0,
            'C02_Orchestration': 0
        }

        self.case_packets = []
        self.notifications = []

        self.setup_routes()
        self.setup_socket_events()

    def setup_routes(self):
        """Setup REST API routes"""

        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'active_cases': len(self.active_cases),
                'agents_online': sum(1 for agent in self.agent_status.values() if agent['status'] != 'offline')
            })

        @self.app.route('/api/vector-store/status', methods=['GET'])
        def vector_store_status():
            """Mock vector store status for UI compatibility"""
            return jsonify({
                'success': True,
                'stores': {
                    'primary_evidence': {
                        'documents': 1250,
                        'last_updated': datetime.now().isoformat()
                    },
                    'case_opinions': {
                        'documents': 850,
                        'last_updated': datetime.now().isoformat()
                    },
                    'general_rag': {
                        'documents': 2100,
                        'last_updated': datetime.now().isoformat()
                    }
                },
                'validation_sub_vectors': 15
            })

        @self.app.route('/api/vector-store/apply-validation-filter', methods=['POST'])
        def apply_validation_filter():
            """Mock validation filter application"""
            data = request.get_json()
            validation_type = data.get('validation_type', 'complaints_against_tesla')

            # Simulate processing
            self.socketio.emit('vector_filter_applied', {
                'validation_type': validation_type,
                'document_count': 450,
                'timestamp': datetime.now().isoformat()
            })

            return jsonify({
                'success': True,
                'validation_type': validation_type,
                'document_count': 450,
                'message': f'Applied {validation_type} filter successfully'
            })

        @self.app.route('/api/cases', methods=['GET'])
        def get_cases():
            """Get all active cases"""
            return jsonify({
                'cases': list(self.active_cases.values()),
                'total': len(self.active_cases)
            })

        @self.app.route('/api/cases/<case_id>', methods=['GET'])
        def get_case(case_id):
            """Get specific case details"""
            if case_id in self.active_cases:
                return jsonify(self.active_cases[case_id])
            return jsonify({'error': 'Case not found'}), 404

        @self.app.route('/api/agents/status', methods=['GET'])
        def get_agent_status():
            """Get current agent status"""
            return jsonify({
                'agents': self.agent_status,
                'timestamp': datetime.now().isoformat()
            })

        @self.app.route('/api/phases/progress', methods=['GET'])
        def get_phase_progress():
            """Get MultiSWARM phase progress"""
            return jsonify({
                'phases': self.phase_progress,
                'overall_progress': sum(self.phase_progress.values()) / len(self.phase_progress),
                'timestamp': datetime.now().isoformat()
            })

    def setup_socket_events(self):
        """Setup Socket.IO event handlers"""

        @self.socketio.on('connect')
        def handle_connect():
            logger.info(f"Client connected: {request.sid}")
            emit('server_ready', {
                'message': 'LawyerFactory backend ready',
                'timestamp': datetime.now().isoformat()
            })

        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info(f"Client disconnected: {request.sid}")

        @self.socketio.on('start_legal_intake')
        def handle_legal_intake(data):
            """Handle legal intake form submission"""
            logger.info(f"Starting legal intake: {data}")

            case_id = f"case_{int(time.time())}"
            case_data = {
                'id': case_id,
                'status': 'intake_processing',
                'client_info': data,
                'created_at': datetime.now().isoformat(),
                'current_phase': 'A01_Intake',
                'progress': 0
            }

            self.active_cases[case_id] = case_data

            # Start intake processing simulation
            self.socketio.start_background_task(self.simulate_intake_processing, case_id, data)

            emit('intake_started', {
                'case_id': case_id,
                'message': 'Legal intake processing started',
                'timestamp': datetime.now().isoformat()
            })

        @self.socketio.on('start_factory')
        def handle_start_factory():
            """Handle factory start command"""
            logger.info("Starting LawyerFactory")

            # Reset all agents to active
            for agent in self.agent_status:
                self.agent_status[agent]['status'] = 'active'
                self.agent_status[agent]['progress'] = 0

            # Start the MultiSWARM processing pipeline
            self.socketio.start_background_task(self.simulate_multiswarm_pipeline)

            emit('factory_started', {
                'message': 'LawyerFactory MultiSWARM pipeline initiated',
                'timestamp': datetime.now().isoformat()
            })

        @self.socketio.on('request_status_update')
        def handle_status_request():
            """Handle status update requests"""
            emit('status_update', {
                'agents': self.agent_status,
                'phases': self.phase_progress,
                'active_cases': len(self.active_cases),
                'timestamp': datetime.now().isoformat()
            })

    def simulate_intake_processing(self, case_id: str, intake_data: Dict[str, Any]):
        """Simulate the intake processing workflow"""
        try:
            # Phase 1: Document intake
            self.update_agent_status('intake_agent', 'processing', 25)
            self.socketio.emit('agent_activity', {
                'agent': 'Intake Agent',
                'action': 'Processing client information',
                'progress': 25
            })
            time.sleep(2)

            # Phase 2: Initial analysis
            self.update_agent_status('intake_agent', 'processing', 50)
            self.socketio.emit('agent_activity', {
                'agent': 'Intake Agent',
                'action': 'Analyzing case details',
                'progress': 50
            })
            time.sleep(2)

            # Phase 3: Jurisdiction check
            self.update_agent_status('intake_agent', 'processing', 75)
            self.socketio.emit('agent_activity', {
                'agent': 'Intake Agent',
                'action': 'Validating jurisdiction',
                'progress': 75
            })
            time.sleep(2)

            # Phase 4: Complete
            self.update_agent_status('intake_agent', 'completed', 100)
            self.phase_progress['A01_Intake'] = 100

            # Update case status
            if case_id in self.active_cases:
                self.active_cases[case_id]['status'] = 'intake_completed'
                self.active_cases[case_id]['progress'] = 100

            self.socketio.emit('phase_completed', {
                'phase': 'A01_Intake',
                'case_id': case_id,
                'message': 'Intake processing completed successfully'
            })

        except Exception as e:
            logger.error(f"Error in intake processing: {e}")
            self.socketio.emit('error', {
                'phase': 'A01_Intake',
                'error': str(e)
            })

    def simulate_multiswarm_pipeline(self):
        """Simulate the complete MultiSWARM pipeline"""
        phases = [
            ('A01_Intake', 'intake_agent', 'Intake Agent'),
            ('A02_Research', 'research_agent', 'Research Agent'),
            ('A03_Outline', 'research_agent', 'Research Agent'),
            ('B01_Review', 'review_agent', 'Review Agent'),
            ('B02_Drafting', 'drafting_agent', 'Drafting Agent'),
            ('C01_Editing', 'review_agent', 'Review Agent'),
            ('C02_Orchestration', 'orchestration_agent', 'Orchestration Agent')
        ]

        for phase_name, agent_key, agent_name in phases:
            try:
                # Start phase
                self.socketio.emit('phase_change', {
                    'phase': phase_name,
                    'status': 'starting',
                    'timestamp': datetime.now().isoformat()
                })

                # Simulate agent work
                for progress in range(0, 101, 20):
                    self.update_agent_status(agent_key, 'processing', progress)
                    self.phase_progress[phase_name] = progress

                    self.socketio.emit('agent_activity', {
                        'agent': agent_name,
                        'action': f'Processing {phase_name}',
                        'progress': progress
                    })

                    time.sleep(1)

                # Complete phase
                self.update_agent_status(agent_key, 'completed', 100)
                self.phase_progress[phase_name] = 100

                self.socketio.emit('phase_completed', {
                    'phase': phase_name,
                    'message': f'{phase_name} completed successfully'
                })

                # Generate case packet for final phase
                if phase_name == 'C02_Orchestration':
                    self.generate_case_packet()

                time.sleep(2)

            except Exception as e:
                logger.error(f"Error in phase {phase_name}: {e}")
                self.socketio.emit('error', {
                    'phase': phase_name,
                    'error': str(e)
                })

    def update_agent_status(self, agent_key: str, status: str, progress: int):
        """Update agent status"""
        if agent_key in self.agent_status:
            self.agent_status[agent_key]['status'] = status
            self.agent_status[agent_key]['progress'] = progress

    def generate_case_packet(self):
        """Generate final case packet"""
        case_packet = {
            'id': f"packet_{int(time.time())}",
            'title': 'Complete Legal Case Package',
            'generated_at': datetime.now().isoformat(),
            'documents': [
                {'type': 'complaint', 'filename': 'complaint_draft.pdf', 'status': 'ready'},
                {'type': 'motion', 'filename': 'motion_to_dismiss_response.pdf', 'status': 'ready'},
                {'type': 'brief', 'filename': 'legal_brief.pdf', 'status': 'ready'},
                {'type': 'evidence', 'filename': 'evidence_packet.pdf', 'status': 'ready'}
            ],
            'metadata': {
                'total_pages': 45,
                'jurisdiction': 'Federal',
                'case_type': 'Contract Dispute',
                'confidence_score': 0.92
            }
        }

        self.case_packets.append(case_packet)

        self.socketio.emit('case_packet_ready', {
            'packet': case_packet,
            'message': 'Complete case packet generated and ready for delivery'
        })

    def run(self, host: str = '127.0.0.1', port: int = 5000):
        """Run the server"""
        logger.info(f"Starting LawyerFactory server on {host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=False)


if __name__ == '__main__':
    server = LawyerFactoryServer()
    server.run()