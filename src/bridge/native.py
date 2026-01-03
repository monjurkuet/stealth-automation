import sys
import json
import struct
import threading
import queue
import logging

# Configure logging to file since stdout is used for communication
logging.basicConfig(
    filename="native_host.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class NativeBridge:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.command_queue = queue.Queue()
        self.results = {}
        self.incoming_messages = (
            queue.Queue()
        )  # Queue for messages initiated by the browser
        self.current_command_id = 0
        self._initialized = True
        self.running = True

        # Start reading thread
        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()

        # Set up signal handlers for graceful shutdown
        import signal

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()

    def get_incoming_message(self, block=True, timeout=None):
        """Retrieves the next message sent by the browser (not a result)."""
        try:
            return self.incoming_messages.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    def _get_next_command_id(self):
        self.current_command_id += 1
        return self.current_command_id

    def is_connection_healthy(self):
        """Check if the native messaging connection is healthy."""
        return self.running and not sys.stdin.closed

    def send_command(self, command):
        """Sends a command to the Chrome Extension."""
        if not self.is_connection_healthy():
            raise ConnectionError("Native messaging connection lost")

        command_id = self._get_next_command_id()
        command["id"] = command_id

        message = {"command": command}
        self._send_message(message)
        logging.info(f"Sent command {command_id}: {command['action']}")
        return command_id

    def get_result(self, command_id, timeout=30):
        """Waits for a result for a specific command ID."""
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            if command_id in self.results:
                result = self.results.pop(command_id)
                logging.info(f"Retrieved result for command {command_id}")
                return result
            time.sleep(0.1)

        logging.error(f"Timeout waiting for command {command_id}")
        return {"status": "error", "message": "Timeout"}

    def _send_message(self, message):
        """Encodes and writes a message to stdout."""
        try:
            json_msg = json.dumps(message, separators=(",", ":"))
            # Write 4-byte length prefix (little-endian)
            sys.stdout.buffer.write(struct.pack("I", len(json_msg)))
            # Write JSON message
            sys.stdout.buffer.write(json_msg.encode("utf-8"))
            sys.stdout.buffer.flush()
        except Exception as e:
            logging.error(f"Error sending message: {e}")

    def _read_loop(self):
        """Continuously reads messages from stdin."""
        while self.running:
            try:
                # Read 4-byte length prefix
                raw_length = sys.stdin.buffer.read(4)
                if not raw_length:
                    logging.info("Stdin closed, exiting read loop.")
                    self.running = False  # Signal shutdown
                    break

                msg_length = struct.unpack("I", raw_length)[0]

                # Read the JSON message
                raw_msg = sys.stdin.buffer.read(msg_length).decode("utf-8")
                message = json.loads(raw_msg)

                logging.debug(f"Received message: {message}")

                # Handle Result
                if "id" in message:
                    self.results[message["id"]] = message
                else:
                    # It's a new message/trigger from the browser
                    logging.info(f"Received trigger/event: {message}")
                    self.incoming_messages.put(message)

            except Exception as e:
                logging.error(f"Error in read loop: {e}")
                break

    def shutdown(self):
        """Gracefully shutdown the bridge."""
        logger.info("Shutting down NativeBridge...")
        self.running = False

        # Wait for read thread to finish
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2)

        logger.info("NativeBridge shutdown complete")
