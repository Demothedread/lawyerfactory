"""
Event system for workflow coordination and monitoring.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Callable, Awaitable, Optional

logger = logging.getLogger(__name__)


class EventBus:
    """Event system for workflow coordination"""

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000

    async def emit(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to all subscribers"""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history.pop(0)
        
        # Notify subscribers
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to event type: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event type"""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
                if not self.subscribers[event_type]:
                    del self.subscribers[event_type]
                logger.debug(f"Unsubscribed from event type: {event_type}")
            except ValueError:
                logger.warning(f"Callback not found for event type: {event_type}")

    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get event history, optionally filtered by type"""
        if event_type:
            events = [e for e in self.event_history if e['type'] == event_type]
        else:
            events = self.event_history
        
        return events[-limit:] if limit else events

    def clear_history(self):
        """Clear event history"""
        self.event_history.clear()
        logger.info("Event history cleared")