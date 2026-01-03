import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


class JSONLStorage:
    """
    Append-only JSONL file storage.
    Saves items one per line for easy streaming and partial recovery.
    """

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"JSONL storage initialized: {self.filepath}")

    async def append_item(self, platform: str, data: Dict):
        """Append a single item entry."""
        entry = {
            "status": "item",
            "platform": platform,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        self._append(entry)

    async def append_summary(self, platform: str, summary: Dict):
        """Append a summary entry."""
        entry = {
            "status": "summary",
            "platform": platform,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": summary,
        }
        self._append(entry)

    async def append_error(self, platform: str, error: Dict):
        """Append an error entry."""
        entry = {
            "status": "error",
            "platform": platform,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": error,
        }
        self._append(entry)
        logger.error(f"Error saved to JSONL: {error}")

    async def append_progress(self, platform: str, progress: Dict):
        """Append a progress event entry."""
        entry = {
            "status": "progress",
            "platform": platform,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": progress,
        }
        self._append(entry)

    def _append(self, entry: Dict):
        """Internal append to file."""
        try:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to JSONL: {e}")
            raise

    def get_filepath(self) -> str:
        """Get the current filepath."""
        return str(self.filepath)
