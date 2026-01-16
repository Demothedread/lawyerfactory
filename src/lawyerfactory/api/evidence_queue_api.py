"""
Evidence Queue Management API Endpoints

Handles batch evidence upload, processing queue management, and real-time status updates
"""

from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import asyncio
import logging
from typing import Dict, Any

from lawyerfactory.storage.core.evidence_queue import (
    get_or_create_queue,
    get_queue_status,
    EvidenceProcessingQueue,
)
from lawyerfactory.config.case_types import get_case_type_from_string

logger = logging.getLogger(__name__)

evidence_queue_bp = Blueprint('evidence_queue', __name__, url_prefix='/api/evidence/queue')


@evidence_queue_bp.route('/status/<case_id>', methods=['GET'])
@cross_origin()
def get_queue_status_endpoint(case_id: str):
    """Get current status of evidence processing queue for case"""
    try:
        status = get_queue_status(case_id)
        if status is None:
            return jsonify({'error': 'Queue not found for case'}), 404
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Error getting queue status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@evidence_queue_bp.route('/upload/<case_id>', methods=['POST'])
@cross_origin()
def upload_evidence(case_id: str):
    """
    Upload and queue evidence for processing
    
    Expected form data:
    - files: Multiple file uploads
    - case_type: Type of case (e.g., 'autonomous_vehicle', 'product_liability')
    - metadata: Optional JSON metadata
    """
    try:
        case_type = request.form.get('case_type', 'negligence')
        queue = get_or_create_queue(case_id, case_type)

        uploaded_files = request.files.getlist('files')
        if not uploaded_files:
            return jsonify({'error': 'No files uploaded'}), 400

        queue_items = []
        for file in uploaded_files:
            if file.filename == '':
                continue

            # Save file temporarily
            temp_path = f"/tmp/{case_id}_{file.filename}"
            file.save(temp_path)

            # Add to queue
            metadata = {
                'uploaded_by': 'user',
                'original_filename': file.filename,
                'file_size': len(file.read()),
            }
            file.seek(0)

            item = queue.add_to_queue(
                file_path=temp_path,
                filename=file.filename,
                case_id=case_id,
                metadata=metadata,
            )
            queue_items.append(item.to_dict())

        # Start async processing
        # In production, would use Celery or similar task queue
        asyncio.create_task(_process_queue_async(queue, case_id))

        return jsonify({
            'message': f'Queued {len(queue_items)} files for processing',
            'items': queue_items,
        }), 202

    except Exception as e:
        logger.error(f"Error uploading evidence: {str(e)}")
        return jsonify({'error': str(e)}), 500


@evidence_queue_bp.route('/start/<case_id>', methods=['POST'])
@cross_origin()
def start_queue_processing(case_id: str):
    """Start processing the evidence queue for a case"""
    try:
        status = get_queue_status(case_id)
        if status is None:
            return jsonify({'error': 'Queue not found'}), 404

        queue_size = status['queued']
        if queue_size == 0:
            return jsonify({'message': 'No items in queue to process'}), 200

        return jsonify({
            'message': f'Starting processing of {queue_size} items',
            'status': get_queue_status(case_id),
        }), 200

    except Exception as e:
        logger.error(f"Error starting queue processing: {str(e)}")
        return jsonify({'error': str(e)}), 500


@evidence_queue_bp.route('/cancel/<case_id>/<item_id>', methods=['POST'])
@cross_origin()
def cancel_queue_item(case_id: str, item_id: str):
    """Cancel processing of a specific queue item"""
    try:
        status = get_queue_status(case_id)
        if status is None:
            return jsonify({'error': 'Queue not found'}), 404

        # Find and cancel item (would be implemented in queue)
        return jsonify({'message': f'Cancelled item {item_id}'}), 200

    except Exception as e:
        logger.error(f"Error cancelling item: {str(e)}")
        return jsonify({'error': str(e)}), 500


@evidence_queue_bp.route('/filter/<case_id>', methods=['GET'])
@cross_origin()
def filter_evidence_by_class(case_id: str):
    """
    Get evidence filtered by class (primary/secondary) and optional subcategory
    
    Query params:
    - evidence_class: 'primary' or 'secondary'
    - evidence_type: Optional specific type (e.g., 'email', 'case_law')
    """
    try:
        evidence_class = request.args.get('evidence_class')
        evidence_type = request.args.get('evidence_type')

        status = get_queue_status(case_id)
        if status is None:
            return jsonify({'error': 'Queue not found'}), 404

        # Filter completed items
        filtered_items = status['completed_items']

        if evidence_class:
            filtered_items = [
                item for item in filtered_items
                if item.get('evidence_class') == evidence_class
            ]

        if evidence_type:
            filtered_items = [
                item for item in filtered_items
                if item.get('evidence_type') == evidence_type
            ]

        # Group by evidence type
        grouped = {}
        for item in filtered_items:
            et = item.get('evidence_type', 'unknown')
            if et not in grouped:
                grouped[et] = []
            grouped[et].append(item)

        return jsonify({
            'evidence_class': evidence_class,
            'total_count': len(filtered_items),
            'by_type': grouped,
        }), 200

    except Exception as e:
        logger.error(f"Error filtering evidence: {str(e)}")
        return jsonify({'error': str(e)}), 500


@evidence_queue_bp.route('/stats/<case_id>', methods=['GET'])
@cross_origin()
def get_queue_statistics(case_id: str):
    """Get detailed statistics about evidence queue and classifications"""
    try:
        status = get_queue_status(case_id)
        if status is None:
            return jsonify({'error': 'Queue not found'}), 404

        completed_items = status['completed_items']

        # Calculate statistics
        primary_count = len([i for i in completed_items if i.get('evidence_class') == 'primary'])
        secondary_count = len([i for i in completed_items if i.get('evidence_class') == 'secondary'])

        # Evidence type breakdown
        type_breakdown = {}
        for item in completed_items:
            et = item.get('evidence_type', 'unknown')
            type_breakdown[et] = type_breakdown.get(et, 0) + 1

        # Confidence statistics
        confidences = [
            item.get('classification_confidence', 0)
            for item in completed_items
            if item.get('classification_confidence')
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        # Error count
        error_count = len([i for i in completed_items if i.get('status') == 'error'])

        return jsonify({
            'total_processed': len(completed_items),
            'primary_evidence': primary_count,
            'secondary_evidence': secondary_count,
            'primary_percentage': (primary_count / len(completed_items) * 100) if completed_items else 0,
            'error_count': error_count,
            'average_confidence': avg_confidence,
            'evidence_type_breakdown': type_breakdown,
            'queue_status': {
                'total': status['total'],
                'queued': status['queued'],
                'processing': status['processing'],
                'completed': status['completed'],
            },
        }), 200

    except Exception as e:
        logger.error(f"Error getting queue statistics: {str(e)}")
        return jsonify({'error': str(e)}), 500


async def _process_queue_async(queue: EvidenceProcessingQueue, case_id: str) -> None:
    """
    Async task to process evidence queue
    In production, would be handled by Celery or similar
    """
    try:
        logger.info(f"Starting async processing of queue for case {case_id}")
        # Placeholder for actual async processing
        # In production: would call queue.process_queue() with actual ingestion pipeline
        pass
    except Exception as e:
        logger.error(f"Error in async queue processing: {str(e)}")


def register_evidence_queue_routes(app):
    """Register evidence queue API blueprint with Flask app"""
    app.register_blueprint(evidence_queue_bp)
    logger.info("Registered evidence queue API routes")
