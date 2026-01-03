#!/usr/bin/env python3
import sys
import os
import asyncio
import logging
import threading

# Ensure we can import from src
sys.path.insert(0, os.getcwd())

from src.bridge.native import NativeBridge
from src.brain.main import Logic

# Setup logging
logging.basicConfig(
    filename="native_host.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


async def handle_external_command(reader, writer):
    """Handles connections from external Python scripts (trigger.py)."""
    try:
        data = await reader.read(1024)
        message = data.decode().strip()
        logging.info(f"Received external command: {message}")

        # Basic protocol: "search:query"
        if message.startswith("search:"):
            query = message.split(":", 1)[1]
            # We need access to brain_logic here.
            # A simple pattern is to put this query into a shared queue or event.
            # For simplicity in this script, we'll store it in a global/shared context
            # or rely on the main loop to pick it up if we restructure slightly.

            # Better approach: Direct execution if we are careful with concurrency,
            # or put it in the bridge's incoming_messages queue to be handled by the main loop.
            from src.bridge.native import NativeBridge

            bridge = NativeBridge()  # It's a singleton
            bridge.incoming_messages.put({"action": "start_search", "query": query})

            writer.write(b"OK")
        else:
            writer.write(b"UNKNOWN_COMMAND")

        await writer.drain()
        writer.close()
    except Exception as e:
        logging.error(f"Error in external command handler: {e}")


async def main():
    logging.info("Native Host Started")

    bridge = NativeBridge()
    brain_logic = Logic(bridge)

    # Start the External Command Server (TCP)
    server = None
    try:
        server = await asyncio.start_server(handle_external_command, "127.0.0.1", 9999)
        logging.info("External Command Server listening on 127.0.0.1:9999")
        asyncio.create_task(server.serve_forever())
    except OSError as e:
        if e.errno == 98:  # Address already in use
            logging.error(
                "Port 9999 is busy. External triggers will be disabled for this instance."
            )
        else:
            logging.error(f"Failed to start external server: {e}")

    logging.info("Waiting for triggers from browser or terminal...")

    while bridge.running:
        # Check for incoming messages (from Browser OR External Server)
        msg = bridge.get_incoming_message(block=False)

        if msg:
            action = msg.get("action")
            logging.info(f"Received trigger: {action}")

            if action == "start_search":
                query = msg.get("query", "Stealth Automation")
                logging.info(f"Starting DuckDuckGo Search for: {query}")
                # Run the task
                await brain_logic.search_duckduckgo(query)
                logging.info("Search task finished.")

            elif action == "ping":
                logging.info("Ping received.")

        await asyncio.sleep(0.1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.critical(f"Main crashed: {e}")
