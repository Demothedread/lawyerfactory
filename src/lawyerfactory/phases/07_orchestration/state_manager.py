"""
# Script Name: checkpoints.py
# Description: Checkpoint management for workflow recovery and state persistence.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: orchestration
Checkpoint management for workflow recovery and state persistence.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Manages workflow checkpoints for recovery"""

    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.checkpoint_interval = 300  # 5 minutes
        
        # Create checkpoints subdirectory
        self.checkpoints_dir = self.storage_path / "checkpoints"
        self.checkpoints_dir.mkdir(exist_ok=True)

    async def create_checkpoint(self, workflow_state) -> None:
        """Create a workflow checkpoint"""
        try:
            checkpoint_data = {
                'timestamp': datetime.now().isoformat(),
                'session_id': workflow_state.session_id,
                'current_phase': workflow_state.current_phase.value,
                'overall_status': workflow_state.overall_status.value,
                'completed_tasks': workflow_state.completed_tasks.copy(),
                'failed_tasks': workflow_state.failed_tasks.copy(),
                'global_context': workflow_state.global_context.copy(),
                'phases': {phase.value: status.value for phase, status in workflow_state.phases.items()},
                'knowledge_graph_id': workflow_state.knowledge_graph_id,
                'input_documents': workflow_state.input_documents.copy(),
                'pending_approvals': workflow_state.pending_approvals.copy(),
                'human_feedback_required': workflow_state.human_feedback_required,
            }
            
            # Generate checkpoint filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint_file = self.checkpoints_dir / f"checkpoint_{workflow_state.session_id}_{timestamp}.json"
            
            # Write checkpoint data
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            
            # Update workflow state
            workflow_state.last_checkpoint = datetime.now()
            workflow_state.checkpoint_data = checkpoint_data
            
            # Clean up old checkpoints (keep last 10)
            await self._cleanup_old_checkpoints(workflow_state.session_id)
            
            logger.info(f"Created checkpoint for session {workflow_state.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            raise

    async def restore_workflow(self, session_id: str, checkpoint_timestamp: Optional[str] = None):
        """Restore workflow from a specific checkpoint"""
        try:
            if checkpoint_timestamp:
                checkpoint_file = self.checkpoints_dir / f"checkpoint_{session_id}_{checkpoint_timestamp}.json"
            else:
                # Find the most recent checkpoint
                checkpoint_file = self._find_latest_checkpoint(session_id)
            
            if not checkpoint_file or not checkpoint_file.exists():
                raise FileNotFoundError(f"No checkpoint found for session {session_id}")
            
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            logger.info(f"Restored workflow from checkpoint for session {session_id}")
            return checkpoint_data
            
        except Exception as e:
            logger.error(f"Failed to restore from checkpoint: {e}")
            raise

    def _find_latest_checkpoint(self, session_id: str) -> Optional[Path]:
        """Find the most recent checkpoint file for a session"""
        pattern = f"checkpoint_{session_id}_*.json"
        checkpoint_files = list(self.checkpoints_dir.glob(pattern))
        
        if not checkpoint_files:
            return None
        
        # Sort by modification time and return the latest
        checkpoint_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return checkpoint_files[0]

    async def _cleanup_old_checkpoints(self, session_id: str, keep_count: int = 10):
        """Clean up old checkpoint files, keeping only the most recent ones"""
        try:
            pattern = f"checkpoint_{session_id}_*.json"
            checkpoint_files = list(self.checkpoints_dir.glob(pattern))
            
            if len(checkpoint_files) <= keep_count:
                return
            
            # Sort by modification time (newest first)
            checkpoint_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Remove old files beyond keep_count, run deletion in thread to avoid blocking event loop
            old_files = checkpoint_files[keep_count:]
            
            async def _remove_files(files):
                from pathlib import Path
                for old_file in files:
                    try:
                        # ensure file is a Path and exists before removal
                        ofp = Path(old_file)
                        if ofp.exists():
                            ofp.unlink()
                            logger.info(f"Removed old checkpoint: {ofp.name}")
                    except Exception as ex:
                        logger.warning(f"Failed to remove checkpoint {old_file}: {ex}")
            
            await asyncio.to_thread(lambda: asyncio.get_event_loop().run_until_complete(_remove_files(old_files)))
            
        except Exception as e:
            logger.error(f"Error during checkpoint cleanup for session {session_id}: {e}")
            # Do not raise here to avoid breaking workflow; just log
            return

    def list_checkpoints(self, session_id: str) -> list:
        """List all available checkpoints for a session"""
        pattern = f"checkpoint_{session_id}_*.json"
        checkpoint_files = list(self.checkpoints_dir.glob(pattern))
        
        checkpoints = []
        for file_path in checkpoint_files:
            try:
                # Extract timestamp from filename
                filename = file_path.stem
                timestamp_part = filename.split('_')[-2:]  # Get last two parts (date_time)
                timestamp_str = '_'.join(timestamp_part)
                
                # Get file stats
                stat = file_path.stat()
                
                checkpoints.append({
                    'timestamp': timestamp_str,
                    'file_path': str(file_path),
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                logger.warning(f"Error reading checkpoint file {file_path}: {e}")
        
        # Sort by timestamp (newest first)
        checkpoints.sort(key=lambda c: c['timestamp'], reverse=True)
        return checkpoints

    async def delete_checkpoints(self, session_id: str):
        """Delete all checkpoints for a session"""
        try:
            pattern = f"checkpoint_{session_id}_*.json"
            checkpoint_files = list(self.checkpoints_dir.glob(pattern))
            
            for file_path in checkpoint_files:
                file_path.unlink()
                logger.debug(f"Deleted checkpoint: {file_path}")
            
            logger.info(f"Deleted {len(checkpoint_files)} checkpoints for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete checkpoints: {e}")
            raise

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics for checkpoints"""
        try:
            checkpoint_files = list(self.checkpoints_dir.glob("checkpoint_*.json"))
            
            total_size = sum(f.stat().st_size for f in checkpoint_files)
            sessions = set()
            
            for file_path in checkpoint_files:
                try:
                    # Extract session ID from filename
                    filename = file_path.stem
                    parts = filename.split('_')
                    if len(parts) >= 3:
                        session_id = '_'.join(parts[1:-2])  # Remove 'checkpoint' prefix and timestamp suffix
                        sessions.add(session_id)
                except Exception:
                    pass
            
            return {
                'total_checkpoints': len(checkpoint_files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'unique_sessions': len(sessions),
                'storage_path': str(self.checkpoints_dir)
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {
                'error': str(e),
                'storage_path': str(self.checkpoints_dir)
            }