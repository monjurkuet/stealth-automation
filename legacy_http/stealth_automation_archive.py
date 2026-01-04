#!/usr/bin/env python3
"""
Stealth Automation Archive
==========================

This is a monolithic archive of the Stealth Browser Automation Framework.
It contains both the Python 'Brain' and 'Bridge' components, as well as the
JavaScript 'Hands' userscript.

Usage:
1. Copy the USERSCRIPT_CONTENT (below) into your browser's userscript manager (e.g., Tampermonkey).
2. Run this script: python3 stealth_automation_archive.py
"""

import http.server
import socketserver
import json
import threading
import queue
import time
import asyncio

# --- Part 1: The "Hands" (Userscript) ---

USERSCRIPT_CONTENT = r"""
// ==UserScript==
// @name         Stealth Automation Hands
// @namespace    http://tampermonkey.net/
// @version      0.2
// @description  Connects to Python Brain via HTTP polling for stealth browser automation
// @author       You
// @match        *://*/*
// @grant        GM_xmlhttpRequest
// @grant        GM_addStyle
// @connect      localhost
// ==/UserScript==

(function() {
    'use strict';

    console.log("Hands: Script starting on " + window.location.href);

    const httpBridgeUrl = 'http://localhost:8765'; // Address of the Python HTTP Bridge
    const pollingInterval = 500; // Poll every 500ms
    let statusDiv = null;

    // --- UI Helper Functions ---
    function createStatusOverlay() {
        if (document.getElementById('stealth-hands-status')) return;

        statusDiv = document.createElement('div');
        statusDiv.id = 'stealth-hands-status';
        statusDiv.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: #fff;
            padding: 8px 12px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
            z-index: 999999;
            pointer-events: none;
            user-select: none;
            border: 1px solid #444;
            box-shadow: 0 2px 5px rgba(0,0,0,0.5);
        `;
        statusDiv.textContent = 'Hands: Initializing...';
        document.body.appendChild(statusDiv);
    }

    function updateStatus(text, color = '#fff') {
        if (!statusDiv) createStatusOverlay();
        if (statusDiv) {
            statusDiv.textContent = `Hands: ${text}`;
            statusDiv.style.color = color;
        }
    }

    // Initialize UI as soon as body is available
    if (document.body) {
        createStatusOverlay();
    } else {
        window.addEventListener('DOMContentLoaded', createStatusOverlay);
    }

    // --- Communication Functions ---

    // Function to send data back to the Brain via HTTP POST
    window.sendToBrain = function(data) {
        updateStatus('Sending result...', '#00ccff');
        GM_xmlhttpRequest({
            method: "POST",
            url: `${httpBridgeUrl}/result`,
            headers: {
                "Content-Type": "application/json"
            },
            data: JSON.stringify(data),
            onload: function(response) {
                console.log("Hands: Result sent to Brain. Response:", response.responseText);
                updateStatus('Idle (Connected)', '#00ff00');
            },
            onerror: function(error) {
                console.error("Hands: Error sending result to Brain:", error);
                updateStatus('Error sending result', '#ff0000');
            }
        });
    };

    // Function to poll the Brain for new commands
    function initPolling() {
        console.log("Hands: Starting polling loop...");
        setInterval(() => {
            GM_xmlhttpRequest({
                method: "GET",
                url: `${httpBridgeUrl}/command`,
                onload: async function(response) {
                    try {
                        const responseData = JSON.parse(response.responseText);
                        // Update status to green if we successfully reached the server (even if no command)
                        if (statusDiv && statusDiv.textContent === 'Hands: Initializing...') {
                             updateStatus('Idle (Connected)', '#00ff00');
                        }

                        const command = responseData.command;
                        if (command) {
                            console.log('Hands: Received command from Brain:', command);
                            updateStatus(`Exec: ${command.action}`, '#ffff00');
                            await handleCommand(command);
                        }
                    } catch (e) {
                        console.error("Hands: Error parsing command response:", e);
                        updateStatus('Parse Error', '#ff0000');
                    }
                },
                onerror: function(error) {
                    console.warn("Hands: Polling error (Server offline?):", error);
                    updateStatus('Disconnected', '#ff0000');
                }
            });
        }, pollingInterval);
    }


    // --- Command Handling Functions ---
    async function handleCommand(command) {
        let result = { id: command.id, status: 'error', message: 'Command not handled' };
        try {
            switch (command.action) {
                case 'navigate':
                    console.log(`Hands: Navigating to ${command.url}`);
                    updateStatus(`Navigating: ${command.url}`, '#ffff00');
                    result = { id: command.id, status: 'success', message: 'Navigation initiated' };
                    // Ensure the result is sent before navigating
                    await new Promise(resolve => {
                        GM_xmlhttpRequest({
                            method: "POST",
                            url: `${httpBridgeUrl}/result`,
                            headers: { "Content-Type": "application/json" },
                            data: JSON.stringify(result),
                            onload: function(response) {
                                console.log("Hands: Result sent before navigation:", response.responseText);
                                resolve();
                            },
                            onerror: function(error) {
                                console.error("Hands: Error sending result before navigation:", error);
                                resolve(); // Resolve even on error
                            }
                        });
                    });
                    window.location.href = command.url;
                    break;
                case 'type':
                    console.log(`Hands: Typing "${command.value}" into "${command.selector}"`);
                    const inputElement = await waitForSelector(command.selector);
                    if (inputElement) {
                        inputElement.value = command.value;
                        const parentForm = inputElement.closest('form');
                        if (parentForm) {
                            parentForm.submit();
                            result = { id: command.id, status: 'success', message: 'Typed text and submitted form' };
                        } else {
                            inputElement.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', bubbles: true }));
                            inputElement.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', bubbles: true }));
                            inputElement.dispatchEvent(new Event('change', { bubbles: true }));
                            result = { id: command.id, status: 'success', message: 'Typed text and dispatched events' };
                        }
                    } else {
                        result = { id: command.id, status: 'error', message: `Element not found for typing: ${command.selector}`};
                    }
                    break;
                case 'click':
                    console.log(`Hands: Clicking "${command.selector}"`);
                    const clickElement = await waitForSelector(command.selector);
                    if (clickElement) {
                        clickElement.click();
                        result = { id: command.id, status: 'success', message: 'Clicked element' };
                    } else {
                        result = { id: command.id, status: 'error', message: `Element not found for clicking: ${command.selector}`};
                    }
                    break;
                case 'wait_for_selector':
                    console.log(`Hands: Waiting for "${command.selector}"`);
                    const foundElement = await waitForSelector(command.selector, command.timeout || 10000);
                    if (foundElement) {
                        result = { id: command.id, status: 'success', message: `Element "${command.selector}" appeared.`};
                    } else {
                        result = { id: command.id, status: 'error', message: `Timeout waiting for element: ${command.selector}`};
                    }
                    break;
                case 'extract_urls':
                    console.log(`Hands: Extracting URLs with selector "${command.selector}"`);
                    const urls = await extractUrls(command.selector);
                    result = { id: command.id, status: 'success', data: urls};
                    break;
                default:
                    console.warn('Hands: Unknown command received:', command);
                    result = { id: command.id, status: 'error', message: `Unknown command: ${command.action}`};
            }
        } catch (e) {
            console.error('Hands: Error handling command:', e);
            result = { id: command.id, status: 'error', message: e.message };
        }
        
        // For navigation, we already sent the result. For others, send it now.
        if (command.action !== 'navigate') {
            window.sendToBrain(result);
        }
    }

    async function waitForSelector(selector, timeout = 10000) {
        return new Promise((resolve) => {
            const startTime = Date.now();
            const interval = setInterval(() => {
                const element = document.querySelector(selector);
                if (element) {
                    clearInterval(interval);
                    resolve(element);
                } else if (Date.now() - startTime > timeout) {
                    clearInterval(interval);
                    resolve(null); // Timeout
                }
            }, 200); // Check every 200ms
        });
    }

    async function extractUrls(selector) {
        const links = Array.from(document.querySelectorAll(selector));
        return links.map(link => link.href).filter(href => href && href.startsWith('http'));
    }

    // Start polling when the script loads
    initPolling();

})();
"""

# --- Part 2: The "Bridge" (HTTP Server) ---

PORT = 8765


class HttpBridge:
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
        self.results = {}  # Store results by command ID or some identifier
        self.current_command_id = 0
        self.server_thread = None
        self.httpd = None
        self._initialized = True

    def _get_next_command_id(self):
        self.current_command_id += 1
        return self.current_command_id

    def add_command(self, command):
        command_id = self._get_next_command_id()
        command["id"] = command_id
        self.command_queue.put(command)
        print(f"Bridge: Added command {command_id} to queue: {command['action']}")
        return command_id

    def get_result(self, command_id, timeout=30):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if command_id in self.results:
                result = self.results.pop(command_id)
                print(f"Bridge: Retrieved result for command {command_id}")
                return result
            time.sleep(0.1)  # Check every 100ms
        print(f"Bridge: Timeout getting result for command {command_id}")
        return {
            "status": "error",
            "message": f"Timeout waiting for result for command {command_id}",
        }

    def start_server_in_thread(self):
        if self.server_thread and self.server_thread.is_alive():
            print("Bridge: HTTP server already running.")
            return

        Handler = self._create_request_handler()
        self.httpd = socketserver.TCPServer(("", PORT), Handler)
        self.server_thread = threading.Thread(
            target=self.httpd.serve_forever, daemon=True
        )
        self.server_thread.start()
        print(f"Bridge: HTTP server started in background on http://localhost:{PORT}")

    def shutdown_server(self):
        if self.httpd:
            print("Bridge: Shutting down HTTP server...")
            self.httpd.shutdown()
            self.httpd.server_close()
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join()
            print("Bridge: HTTP server shut down.")

    def _create_request_handler(self):
        bridge_instance = self  # Capture instance for handler

        class RequestHandler(http.server.BaseHTTPRequestHandler):
            def _set_headers(self):
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")  # Crucial for CORS
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header(
                    "Access-Control-Allow-Headers", "X-Requested-With, Content-Type"
                )
                self.end_headers()

            def do_OPTIONS(self):
                self._set_headers()

            def do_GET(self):
                self._set_headers()
                response_content = {"command": None}
                if (
                    self.path == "/command"
                    and not bridge_instance.command_queue.empty()
                ):
                    command = bridge_instance.command_queue.get()
                    response_content["command"] = command
                    print(f"Bridge: Sent command {command['id']} via GET.")
                elif self.path != "/command":
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))
                    return

                self.wfile.write(json.dumps(response_content).encode("utf-8"))

            def do_POST(self):
                self._set_headers()
                response_content = {"status": "success"}
                if self.path == "/result":
                    try:
                        content_length = int(self.headers["Content-Length"])
                        post_data = self.rfile.read(content_length)
                        result = json.loads(post_data.decode("utf-8"))
                        command_id = result.get("id")
                        if command_id is not None:
                            bridge_instance.results[command_id] = result
                            print(f"Bridge: Received result for command {command_id}.")
                        else:
                            print(
                                "Bridge: Received POST /result without a command 'id'."
                            )
                            response_content = {
                                "status": "error",
                                "message": "Missing command ID",
                            }

                    except Exception as e:
                        print(f"Bridge: Error processing POST /result: {e}")
                        response_content = {"status": "error", "message": str(e)}
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))
                    return

                self.wfile.write(json.dumps(response_content).encode("utf-8"))

        return RequestHandler


# --- Part 3: The "Brain" (Logic & Main) ---


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
    print("----------------------------------------------------------------")
    print("Welcome to the Stealth Automation Archive")
    print("----------------------------------------------------------------")
    print("Make sure you have copied 'USERSCRIPT_CONTENT' from this file")
    print("into your userscript manager (Tampermonkey) and enabled it.")
    print("----------------------------------------------------------------")

    # Initialize the HTTP Bridge
    bridge = HttpBridge()
    bridge.start_server_in_thread()  # Start the HTTP server in a separate thread

    # Give the server a moment to start
    await asyncio.sleep(1)

    # Initialize the Brain's Logic with the bridge
    brain_logic = Logic(bridge)

    # Run DuckDuckGo search automation test case
    await brain_logic.search_duckduckgo("Stealth browser automation")

    bridge.shutdown_server()  # Explicitly shut down the server when main task is done.
    print("Brain: Main task finished, bridge shut down.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Brain: Main program interrupted. Shutting down bridge...")
        bridge_instance = HttpBridge()
        bridge_instance.shutdown_server()
