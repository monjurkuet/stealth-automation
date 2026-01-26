import asyncio
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class HTTPBridge:
    """Bridge for HTTP-based communication."""

    def __init__(self):
        self.running = True
        self._queue = asyncio.Queue()
        self._pending_commands = {}
        self._command_id = 0

    def incoming_message(self, message: Dict):
        """Add a message to the incoming queue."""
        self._queue.put_nowait(message)

    async def get_incoming_message(self, block: bool = True) -> Optional[Dict]:
        """Get a message from the incoming queue."""
        if block:
            return await self._queue.get()
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    def send_command(self, command: Dict) -> int:
        """Queue a command to be executed by the browser extension."""
        self._command_id += 1
        command_id = self._command_id
        command["id"] = command_id
        self._pending_commands[command_id] = command
        logger.info(f"Queued command {command_id}: {command.get('action')}")
        return command_id

    async def get_result(self, command_id: int, timeout: int = 30) -> Dict:
        """Wait for a result from the browser extension."""
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if command_id in self._pending_commands:
                cmd = self._pending_commands[command_id]
                if "result" in cmd:
                    result = cmd["result"]
                    del self._pending_commands[command_id]
                    logger.info(f"Received result for command {command_id}")
                    return result
            await asyncio.sleep(0.1)
        logger.error(f"Timeout waiting for command {command_id}")
        return {"status": "error", "message": "Timeout"}

    def get_pending_command(self) -> Optional[Dict]:
        """Get the next pending command to be executed."""
        for cmd_id, command in list(self._pending_commands.items()):
            if "result" not in command:
                return command
        return None

    def set_command_result(self, command_id: int, result: Dict):
        """Set the result for a command."""
        if command_id in self._pending_commands:
            self._pending_commands[command_id]["result"] = result
            logger.debug(f"Set result for command {command_id}")

    def send_response(self, response: Dict):
        """Send a response (for compatibility)."""
        logger.debug(f"Response: {response}")
