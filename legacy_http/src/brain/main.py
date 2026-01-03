import sys
import os

# Add the current working directory to the Python path
sys.path.insert(0, os.getcwd())

import asyncio
from src.bridge.server import HttpBridge
import json  # Will need this for sending/receiving command data

# main.py for the Python "Brain" component
# This module will handle Logic, Coordinate Calculation, and Bezier Paths.


class Logic:
    """
    Handles the overall logic and decision-making for browser automation tasks.
    """

    def __init__(self, bridge: HttpBridge):
        self.bridge = bridge

    async def execute_task(self, task_data):
        """
        Executes a given automation task.
        """
        print(f"Executing task: {task_data}")

    async def search_duckduckgo(self, query: str):
        """
        Automates searching on DuckDuckGo and fetches the first page's result URLs.
        """
        print(f"Brain: Initiating DuckDuckGo search for: '{query}'")

        # 1. Navigate to DuckDuckGo homepage
        navigate_command_id = self.send_command_to_hands(
            {"action": "navigate", "url": "https://duckduckgo.com/"}
        )
        navigate_result = self.bridge.get_result(navigate_command_id)
        print(f"Brain: Navigation result: {navigate_result}")
        if navigate_result.get("status") != "success":
            print("Brain: Navigation failed, aborting search.")
            return
        await asyncio.sleep(10)  # Give page time to load

        # 2. Type query into search bar
        type_command_id = self.send_command_to_hands(
            {
                "action": "type",
                "selector": "input#searchbox_input",
                "value": query,
            }
        )
        type_result = self.bridge.get_result(type_command_id)
        print(f"Brain: Type result: {type_result}")
        if type_result.get("status") != "success":
            print("Brain: Typing failed, aborting search.")
            return
        await asyncio.sleep(5)  # Give time for typing animation/suggestions

        # 3. Wait for search results to load (wait for a common element on the results page)
        wait_command_id = self.send_command_to_hands(
            {"action": "wait_for_selector", "selector": "ol.react-results--main"}
        )
        wait_result = self.bridge.get_result(wait_command_id)
        print(f"Brain: Wait for selector result: {wait_result}")
        if wait_result.get("status") != "success":
            print("Brain: Waiting for search results failed, aborting search.")
            return
        print("Brain: Search results page loaded.")
        await asyncio.sleep(5) 
        # 4. Extract URLs from the first page
        extract_command_id = self.send_command_to_hands(
            {"action": "extract_urls", "selector": "a.result-title-a"}
        )
        extract_result = self.bridge.get_result(extract_command_id)
        print(f"Brain: Extraction result: {extract_result}")
        if extract_result.get("status") == "success" and "data" in extract_result:
            print("Brain: Extracted URLs:")
            for url in extract_result["data"]:
                print(f"- {url}")
            return extract_result["data"]
        else:
            print("Brain: Failed to extract URLs.")
            return []

    def send_command_to_hands(self, command: dict):
        """
        Sends a command to the userscript 'Hands' via the HttpBridge and returns the command ID.
        """
        return self.bridge.add_command(command)


class CoordinateCalculation:
    """
    Handles calculations related to screen coordinates, element positions, etc.
    """

    def __init__(self):
        pass

    def calculate_position(self, element_identifier):
        """
        Calculates the screen coordinates for a given element.
        """
        print(f"Calculating position for: {element_identifier}")
        return {"x": 0, "y": 0}  # Placeholder


class BezierPaths:
    """
    Generates realistic mouse movement paths using Bezier curves.
    """

    def __init__(self):
        pass

    def generate_path(self, start_coords, end_coords, duration):
        """
        Generates a series of coordinates forming a Bezier curve path.
        """
        print(f"Generating Bezier path from {start_coords} to {end_coords}")
        return [
            (start_coords["x"], start_coords["y"]),
            (end_coords["x"], end_coords["y"]),
        ]  # Placeholder


async def main():
    # Initialize the HTTP Bridge
    bridge = HttpBridge()
    bridge.start_server_in_thread()  # Start the HTTP server in a separate thread

    # Give the server a moment to start
    await asyncio.sleep(1)

    # Initialize the Brain's Logic with the bridge
    brain_logic = Logic(bridge)

    # New: Run DuckDuckGo search automation test case
    await brain_logic.search_duckduckgo("Stealth browser automation")

    # Keep the main task alive for a while or until results are processed
    # The HTTP server runs in a daemon thread, so the main program can exit
    # We might want to add a way to gracefully shut down the bridge here.
    # For now, let's just let it run for a bit after the search.
    # await asyncio.sleep(5) # Let some time pass for potential late responses
    bridge.shutdown_server()  # Explicitly shut down the server when main task is done.
    print("Brain: Main task finished, bridge shut down.")


if __name__ == "__main__":
    # In __main__, we need to ensure the HttpBridge is properly initialized before asyncio.run
    # because it's a singleton and start_server_in_thread() is called in main().
    # However, to gracefully handle KeyboardInterrupt for the main thread,
    # and allow the HttpBridge to manage its own threaded server, we run it this way.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Brain: Main program interrupted. Shutting down bridge...")
        # Get the singleton instance to shut it down
        bridge_instance = HttpBridge()
        bridge_instance.shutdown_server()
