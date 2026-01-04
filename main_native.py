#!/usr/bin/env python3
import asyncio
import logging
import os
import signal
import subprocess
import sys
import time

# Ensure we can import from src
sys.path.insert(0, os.getcwd())

from src.brain.main import Orchestrator
from src.bridge.native import NativeBridge
from src.brain.factory import AutomationFactory  # ADDED
from src.common.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# Configuration
# COMMAND_TIMEOUT is now configured per task, removed global variable


def kill_existing_instances():
    """Kill all main_native.py processes except current one."""
    current_pid = os.getpid()
    try:
        # Get all python processes with main_native.py
        result = subprocess.run(
            ["pgrep", "-f", "main_native.py"], capture_output=True, text=True
        )

        if result.returncode == 0:
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                try:
                    pid_int = int(pid)
                    if pid_int != current_pid:
                        logger.info(f"Killing previous instance (PID: {pid_int})")
                        os.kill(pid_int, signal.SIGHUP)
                        time.sleep(0.1)
                except (ValueError, OSError) as e:
                    logger.debug(f"Could not kill PID {pid}: {e}")

        # Give killed processes time to clean up
        time.sleep(0.5)

    except Exception as e:
        logger.debug(f"Error checking for existing instances: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


async def handle_external_command(reader, writer):
    """Handles connections from external Python scripts (trigger.py)."""
    addr = writer.get_extra_info("peername")
    logger.debug(f"Connection from {addr}")

    try:
        # Add timeout to prevent hanging
        data = await asyncio.wait_for(reader.read(1024), timeout=5.0)
        message = data.decode().strip()

        if not message:
            writer.write(b"ERROR: Empty message")
            await writer.drain()
            return

        logger.info(f"Received external command: {message}")

        # Validate and parse message format
        parts = message.split(":")
        if len(parts) == 3:
            # Format: "action:query:platform"
            action, query, platform = parts
        elif len(parts) == 2:
            # Format: "action:query" (backward compatibility)
            action, query = parts
            platform = None
        else:
            error_msg = (
                "ERROR: Invalid format. Use 'action:query' or 'action:query:platform'"
            )
            logger.warning(f"Invalid message format: {message}")
            writer.write(error_msg.encode())
            await writer.drain()
            return

        # Validate action
        valid_actions = ["start_search", "start_task", "list_platforms", "ping"]
        if action not in valid_actions:
            error_msg = (
                f"ERROR: Invalid action. Valid actions: {', '.join(valid_actions)}"
            )
            logger.warning(f"Invalid action received: {action}")
            writer.write(error_msg.encode())
            await writer.drain()
            return

        logger.info(f"Parsed - action: {action}, query: {query}, platform: {platform}")

        msg = {
            "action": action,
            "query": query,
        }

        if platform:
            msg["platform"] = platform

        bridge = NativeBridge()
        bridge.incoming_messages.put(msg)

        writer.write(b"OK")
        await writer.drain()

    except asyncio.TimeoutError:
        logger.error(f"Timeout reading from {addr}")
        writer.write(b"ERROR: Timeout")
        await writer.drain()
    except UnicodeDecodeError:
        logger.error(f"Invalid encoding from {addr}")
        writer.write(b"ERROR: Invalid encoding")
        await writer.drain()
    except Exception as e:
        logger.error(f"Error in external command handler: {e}", exc_info=True)
        writer.write(b"ERROR: Internal error")
        await writer.drain()
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            logger.debug(f"Error closing writer: {e}")


async def main():
    logger.info("=" * 60)
    logger.info("Native Host Starting...")
    logger.info("=" * 60)

    bridge = NativeBridge()
    orchestrator = Orchestrator(bridge)

    server = None

    try:
        # Try to start the server
        server = await asyncio.start_server(handle_external_command, "127.0.0.1", 9999)
        logger.info("✓ External Command Server listening on 127.0.0.1:9999")
        # Start server task
        asyncio.create_task(server.serve_forever())
    except OSError as e:
        if e.errno == 98:  # Address already in use
            logger.error("✗ Port 9999 is already in use")
            logger.error("  Run with pkill flag or wait a moment and try again")
            logger.error("  External triggers will be DISABLED")
        else:
            logger.error(f"✗ Failed to start external server: {e}")
            logger.error("  External triggers will be DISABLED")

    logger.info("✓ Orchestrator ready")
    logger.info("Waiting for triggers from browser or terminal...")
    logger.info("-" * 60)

    while bridge.running:
        msg = bridge.get_incoming_message(block=False)

        if msg:
            action = msg.get("action")
            logger.info(f"→ Received trigger: {action}")

            # Initialize with a default timeout before any potential use
            current_task_timeout = (
                90  # Default fallback if platform config fails or action is not a task
            )

            try:
                if action in ["start_search", "start_task"]:
                    platform = msg.get("platform")
                    if platform:
                        try:
                            platform_info = AutomationFactory.get_platform_info(
                                platform
                            )
                            current_task_timeout = platform_info.get(
                                "task_execution_s", 90
                            )
                        except ValueError as e:
                            logger.warning(
                                f"Could not get platform info for {platform}: {e}. Using default timeout."
                            )

                    # Execute task with configurable timeout
                    result = await asyncio.wait_for(
                        orchestrator.dispatch(msg), timeout=current_task_timeout
                    )
                    status = result.get("status", "unknown")
                    logger.info(f"✓ Task completed: {status}")

                elif action == "list_platforms":
                    result = await orchestrator.list_platforms()
                    platforms = result.get("platforms", [])
                    logger.info(f"✓ Available platforms: {', '.join(platforms)}")

                elif action == "ping":
                    logger.info("✓ Ping acknowledged")

                else:
                    logger.warning(f"✗ Unknown action: {action}")

            except asyncio.TimeoutError:
                # current_task_timeout is guaranteed to be bound here
                logger.error(f"✗ Task timed out after {current_task_timeout}s")
            except Exception as e:
                logger.error(f"✗ Task failed: {e}", exc_info=True)

        # Reduced polling frequency to save CPU
        await asyncio.sleep(0.2)


if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)

    # Always kill existing instances before starting (needed for Chrome extension)
    kill_existing_instances()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nReceived keyboard interrupt")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Native Host stopped")
        logger.info("=" * 60)
