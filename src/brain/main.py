import asyncio
from src.bridge.native import NativeBridge


class Logic:
    """
    Handles the overall logic and decision-making for browser automation tasks.
    """

    def __init__(self, bridge: NativeBridge):
        self.bridge = bridge

    async def execute_task(self, task_data):
        print(f"Executing task: {task_data}")

    async def search_duckduckgo(self, query: str):
        """
        Automates searching on DuckDuckGo using Native Messaging.
        """
        # 1. Navigate
        navigate_id = self.bridge.send_command(
            {"action": "navigate", "url": "https://duckduckgo.com/"}
        )
        result = self.bridge.get_result(navigate_id)
        if result.get("status") != "success":
            return

        await asyncio.sleep(3)

        # 2. Type
        type_id = self.bridge.send_command(
            {
                "action": "type",
                "selector": "input#searchbox_input",
                "value": query,
            }
        )
        result = self.bridge.get_result(type_id)
        if result.get("status") != "success":
            return

        await asyncio.sleep(2)

        # 3. Wait for results
        wait_id = self.bridge.send_command(
            {"action": "wait_for_selector", "selector": "ol.react-results--main"}
        )
        self.bridge.get_result(wait_id)

        await asyncio.sleep(2)

        # 4. Extract
        extract_id = self.bridge.send_command({"action": "extract_search_results"})
        result = self.bridge.get_result(extract_id)

        if result.get("status") == "success":
            # Since stdout is used for comms, we can't print there easily.
            # We log to file or stderr
            import logging
            import json

            data = result.get("data", [])
            formatted_json = json.dumps(data, indent=2)
            logging.info(f"Extracted Search Results:\n{formatted_json}")

            # If we want to save to a file for the user to see easily:
            with open("search_results.json", "w") as f:
                f.write(formatted_json)
