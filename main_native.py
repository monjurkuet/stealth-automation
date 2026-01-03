#!/usr/bin/env python3
import asyncio
import logging
import os
import signal
import sys

# Ensure we can import from src
sys.path.insert(0, os.getcwd())

from src.brain.main import Orchestrator
from src.bridge.native import NativeBridge
from src.common.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# Process management
PID_FILE = "/tmp/stealth_automation.pid"


def ensure_single_instance():
    """Ensure only one instance of the native host is running."""
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE) as f:
                old_pid = int(f.read().strip())

            # Check if the process is still running
            try:
                os.kill(old_pid, 0)  # Signal 0 checks if process exists
                logger.warning(f"Instance already running (PID: {old_pid}), exiting")
                sys.exit(1)
            except OSError:
                # Process doesn't exist, clean up PID file
                os.unlink(PID_FILE)
    except (FileNotFoundError, ValueError):
        pass

    # Write current PID
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def cleanup_pid_file():
    """Clean up PID file on shutdown."""
    try:
        if os.path.exists(PID_FILE):
            os.unlink(PID_FILE)
    except OSError:
        pass


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    cleanup_pid_file()
    sys.exit(0)


async def handle_external_command(reader, writer):
    """Handles connections from external Python scripts (trigger.py)."""
    try:
        data = await reader.read(1024)
        message = data.decode().strip()
        logger.info(f"Received external command: {message}")

        # Handle both formats: "action:query:platform" and "action:query"
        if message.count(":") == 2:
            # Format: "action:query:platform"
            parts = message.split(":", 2)
            action = parts[0]
            query = parts[1]
            platform = parts[2]
        elif message.count(":") == 1:
            # Format: "action:query" (backward compatibility)
            parts = message.split(":", 1)
            action = parts[0]
            query = parts[1]
            platform = None
        else:
            writer.write(b"ERROR: Invalid format")
            return

        logger.info(
            f"Parsed message - action: {action}, query: {query}, platform: {platform}"
        )

        logger.info(
            f"Parsed message - action: {action}, query: {query}, platform: {platform}"
        )

        msg = {
            "action": action,
            "query": query,
        }

        if platform:
            msg["platform"] = platform

        bridge = NativeBridge()
        bridge.incoming_messages.put(msg)

        writer.write(b"OK")

    except Exception as e:
        logger.error(f"Error in external command handler: {e}")
        writer.write(b"ERROR")


async def main():
    logger.info("Native Host Started")

    bridge = NativeBridge()
    orchestrator = Orchestrator(bridge)

    server = None
    try:
        server = await asyncio.start_server(handle_external_command, "127.0.0.1", 9999)
        logger.info("External Command Server listening on 127.0.0.1:9999")
        asyncio.create_task(server.serve_forever())
    except OSError as e:
        if e.errno == 98:
            logger.error("Port 9999 is busy. External triggers disabled.")
        else:
            logger.error(f"Failed to start external server: {e}")

    logger.info("Waiting for triggers from browser or terminal...")

    while bridge.running:
        msg = bridge.get_incoming_message(block=False)

        if msg:
            action = msg.get("action")
            logger.info(f"Received trigger: {action}")

            if action in ["start_search", "start_task"]:
                result = await orchestrator.dispatch(msg)
                logger.info(f"Task result: {result.get('status')}")

            elif action == "list_platforms":
                result = await orchestrator.list_platforms()
                logger.info(f"Available platforms: {result}")

            elif action == "ping":
                logger.info("Ping received.")

            else:
                logger.warning(f"Unknown action: {action}")

        await asyncio.sleep(0.1)


if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Ensure single instance
    # ensure_single_instance()  # Commented out to allow multiple instances

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.critical(f"Main crashed: {e}")
    finally:
        # cleanup_pid_file()  # Commented out since we're not using PID file
        pass
