"""
Socket.IO event emitter for phase progress and evidence updates
Provides a clean interface for phases to emit real-time events without direct Socket.IO dependency
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Global socketio instance (will be injected from server)
_socketio_instance = None


def set_socketio_instance(socketio):
    """Set the global Socket.IO instance from the Flask app"""
    global _socketio_instance
    _socketio_instance = socketio
    logger.info("Socket.IO instance registered for phase events")


def emit_evidence_processed(
    case_id: str,
    evidence_id: str,
    object_id: str,
    filename: str,
    status: str = "analyzed",
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Emit evidence_processed event when evidence is processed
    
    Args:
        case_id: Case identifier
        evidence_id: Evidence table ID
        object_id: Unified storage ObjectID
        filename: Original filename
        status: Processing status (stored, processing, analyzed, error)
        metadata: Additional metadata
    """
    if not _socketio_instance:
        logger.warning("Socket.IO not available - cannot emit evidence_processed event")
        return
    
    try:
        event_data = {
            "case_id": case_id,
            "evidence_id": evidence_id,
            "object_id": object_id,
            "filename": filename,
            "status": status,
            "metadata": metadata or {}
        }
        
        _socketio_instance.emit("evidence_processed", event_data)
        logger.debug(f"Emitted evidence_processed: {filename} ({status})")
    except Exception as e:
        logger.error(f"Failed to emit evidence_processed event: {e}")


def emit_evidence_uploaded(
    case_id: str,
    evidence_id: str,
    object_id: str,
    filename: str,
    file_size: int = 0,
    phase: str = "phaseA01_intake"
):
    """
    Emit evidence_uploaded event when new evidence is uploaded
    
    Args:
        case_id: Case identifier
        evidence_id: Evidence table ID
        object_id: Unified storage ObjectID
        filename: Original filename
        file_size: File size in bytes
        phase: Source phase
    """
    if not _socketio_instance:
        logger.warning("Socket.IO not available - cannot emit evidence_uploaded event")
        return
    
    try:
        event_data = {
            "case_id": case_id,
            "evidence_id": evidence_id,
            "object_id": object_id,
            "filename": filename,
            "file_size": file_size,
            "phase": phase
        }
        
        _socketio_instance.emit("evidence_uploaded", event_data)
        logger.debug(f"Emitted evidence_uploaded: {filename}")
    except Exception as e:
        logger.error(f"Failed to emit evidence_uploaded event: {e}")


def emit_evidence_status_changed(
    case_id: str,
    evidence_id: str,
    filename: str,
    old_status: str,
    new_status: str
):
    """
    Emit evidence_status_changed event when evidence status changes
    
    Args:
        case_id: Case identifier
        evidence_id: Evidence table ID
        filename: Original filename
        old_status: Previous status
        new_status: New status
    """
    if not _socketio_instance:
        logger.warning("Socket.IO not available - cannot emit evidence_status_changed event")
        return
    
    try:
        event_data = {
            "case_id": case_id,
            "evidence_id": evidence_id,
            "filename": filename,
            "old_status": old_status,
            "new_status": new_status
        }
        
        _socketio_instance.emit("evidence_status_changed", event_data)
        logger.debug(f"Emitted evidence_status_changed: {filename} ({old_status} → {new_status})")
    except Exception as e:
        logger.error(f"Failed to emit evidence_status_changed event: {e}")


def emit_phase_progress(
    phase: str,
    progress: int,
    message: str,
    case_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Emit phase_progress_update event for workflow progress
    
    Args:
        phase: Phase identifier (e.g., "A01_Intake")
        progress: Progress percentage (0-100)
        message: Progress message
        case_id: Optional case identifier
        metadata: Additional metadata
    """
    if not _socketio_instance:
        logger.warning("Socket.IO not available - cannot emit phase_progress event")
        return
    
    try:
        event_data = {
            "phase": phase,
            "progress": progress,
            "message": message,
            "case_id": case_id,
            "metadata": metadata or {}
        }
        
        _socketio_instance.emit("phase_progress_update", event_data)
        logger.debug(f"Emitted phase_progress_update: {phase} ({progress}%)")
    except Exception as e:
        logger.error(f"Failed to emit phase_progress_update event: {e}")
