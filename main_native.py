#!/usr/bin/env python3
import asyncio
import logging
import os
import signal
import subprocess
import sys
import time

sys.path.insert(0, os.getcwd())

from src.brain.main import Orchestrator
from src.bridge.http import app, set_bridge_and_orchestrator
from src.bridge.http_bridge import HTTPBridge
from src.common.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def kill_existing_instances():
    current_pid = os.getpid()
    try:
        result = subprocess.run(
            ["pgrep", "-f", "main_native.py"], capture_output=True, text=True
        )

        if result.returncode == 0:
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                try:
                    pid_int = int(pid)
                    if pid_int != current_pid and pid_int > 0:
                        logger.info(f"Killing previous instance (PID: {pid_int})")
                        os.kill(pid_int, signal.SIGHUP)
                        time.sleep(0.1)
                except (ValueError, OSError) as e:
                    logger.debug(f"Could not kill PID {pid}: {e}")

        time.sleep(0.5)

    except Exception as e:
        logger.debug(f"Error checking for existing instances: {e}")


def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


async def main():
    logger.info("=" * 60)
    logger.info("HTTP Host Starting...")
    logger.info("=" * 60)

    bridge = HTTPBridge()
    orchestrator = Orchestrator(bridge)
    set_bridge_and_orchestrator(bridge, orchestrator)

    import uvicorn

    config = uvicorn.Config(app, host="127.0.0.1", port=9427, log_level="info")
    server = uvicorn.Server(config)
    logger.info("✓ HTTP Server listening on 127.0.0.1:9427")
    logger.info("✓ Orchestrator ready")
    logger.info("Waiting for HTTP requests...")
    logger.info("-" * 60)
    await server.serve()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)

    kill_existing_instances()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nReceived keyboard interrupt")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("HTTP Host stopped")
        logger.info("=" * 60)
