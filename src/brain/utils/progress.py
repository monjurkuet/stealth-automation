import logging
from typing import Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Track and emit progress events during task execution.
    """

    def __init__(self, platform: str, bridge=None):
        self.platform = platform
        self.bridge = bridge
        self.start_time = datetime.now(timezone.utc)
        self.events = []

    async def emit(self, event_type: str, data: Optional[Dict] = None):
        """Emit a progress event."""
        event = {
            "event_type": event_type,
            "platform": self.platform,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data or {},
            "elapsed_seconds": (
                datetime.now(timezone.utc) - self.start_time
            ).total_seconds(),
        }

        self.events.append(event)
        logger.debug(f"Progress event: {event_type}")

        if self.bridge:
            try:
                self.bridge.send_command({"action": "progress_update", "event": event})
            except Exception as e:
                logger.warning(f"Failed to send progress to bridge: {e}")

    def get_summary(self) -> Dict:
        """Get progress summary."""
        return {
            "platform": self.platform,
            "duration_seconds": (
                datetime.now(timezone.utc) - self.start_time
            ).total_seconds(),
            "total_events": len(self.events),
            "events_by_type": self._count_events_by_type(),
        }

    def _count_events_by_type(self) -> Dict[str, int]:
        """Count events by type."""
        counts = {}
        for evt in self.events:
            evt_type = evt["event_type"]
            counts[evt_type] = counts.get(evt_type, 0) + 1
        return counts
