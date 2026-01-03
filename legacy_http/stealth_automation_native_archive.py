#!/usr/bin/env python3
"""
Stealth Automation Native Messaging Archive
===========================================

This is a monolithic archive of the Stealth Browser Automation Framework
using Chrome Native Messaging.

Usage:
1. Chrome Extension Setup:
   - Copy EXTENSION_MANIFEST content to 'manifest.json' in a new folder.
   - Copy BACKGROUND_JS content to 'background.js' in the same folder.
   - Copy CONTENT_JS content to 'content.js' in the same folder.
   - Load this folder as an 'Unpacked Extension' in Chrome (chrome://extensions/).
   - NOTE: The native host path in 'manifest.json' must be updated to point
     to THIS Python script.

2. Native Host Setup:
   - Update the 'path' in your Chrome Native Messaging Host configuration file
     (e.g., ~/.config/google-chrome/NativeMessagingHosts/com.stealth.automation.json).
   - The path should point to where you save THIS script.
   - Example path: /home/user/dev/stealth-automation/stealth_automation_native_archive.py

3. Running the System:
   - Start Chrome (the extension will start this script).
   - Run: python3 stealth_automation_native_archive.py
   - This starts the Native Host which listens for the extension.

4. Triggering Automation:
   - You can trigger a search using the built-in client below:
     python3 -c "exec(open(__file__).read())" "Your Search Query"
   - Or use the Trigger Client script content below.
"""

import sys
import os
import asyncio
import logging
import threading
import socket
import json
import struct
import queue
import time

# --- Part 1: Chrome Extension Files (Embedded as Strings) ---

EXTENSION_MANIFEST = r"""{
  "name": "Stealth Automation",
  "version": "1.0",
  "manifest_version": 3,
  "description": "Stealth automation using Native Messaging",
  "permissions": [
    "nativeMessaging",
    "tabs",
    "scripting",
    "activeTab"
  ],
  "action": {
    "default_popup": "popup.html"
  },
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"],
      "run_at": "document_start"
    }
  ]
}
"""

BACKGROUND_JS = r"""// background.js
console.log("Stealth Automation: Background Service Worker Starting...");

let nativePort = null;

// Connect to the Python Native Host
function connectToNativeHost() {
    const hostName = "com.stealth.automation";
    console.log(`Stealth Automation: Connecting to native host ${hostName}...`);
    nativePort = chrome.runtime.connectNative(hostName);

    nativePort.onMessage.addListener((message) => {
        console.log("Stealth Automation: Received from Native:", message);
        // If it's a command for the content script
        if (message.command) {
            sendMessageToActiveTab(message);
        }
    });

    nativePort.onDisconnect.addListener(() => {
        console.log("Stealth Automation: Native host disconnected.", chrome.runtime.lastError);
        nativePort = null;
    });
}

// Send message to the active tab
async function sendMessageToActiveTab(message) {
    try {
        // Query ALL active tabs in all windows
        const tabs = await chrome.tabs.query({ active: true });
        
        if (tabs.length === 0) {
            console.warn("Stealth Automation: No active tabs found.");
            return;
        }

        console.log(`Stealth Automation: Sending command to ${tabs.length} active tabs.`);
        
        for (const tab of tabs) {
             if (tab.id) {
                chrome.tabs.sendMessage(tab.id, message).catch(err => {
                     // This is normal if the active tab is a restricted page (like chrome://)
                     console.log(`Stealth Automation: Could not send to tab ${tab.id}:`, err);
                });
            }
        }
    } catch (e) {
        console.error("Stealth Automation: Error finding active tab:", e);
    }
}

// Handle messages from Content Script AND Popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // 1. Handle Trigger from Popup
    if (message.type === "TRIGGER_NATIVE") {
        console.log("Stealth Automation: Trigger received:", message.payload);
        if (nativePort) {
            nativePort.postMessage(message.payload);
            sendResponse({status: "sent"});
        } else {
            console.warn("Stealth Automation: Native port not connected. Reconnecting...");
            connectToNativeHost();
            setTimeout(() => {
                if (nativePort) {
                    nativePort.postMessage(message.payload);
                    sendResponse({status: "sent"});
                } else {
                    sendResponse({status: "error", message: "Could not connect to native host"});
                }
            }, 100);
        }
        return true; // Async response
    }

    // 2. Handle Result from Content Script (Hands)
    console.log("Stealth Automation: Received from Content:", message);
    if (nativePort) {
        nativePort.postMessage(message);
    } else {
         // ... reconnection logic if needed for results ...
    }
});

// Initial Connection
connectToNativeHost();
"""

CONTENT_JS = r"""// content.js
console.log("Stealth Automation: Content Script Loaded");

// --- UI Helper Functions (Visual Feedback) ---
let statusDiv = null;

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
    statusDiv.textContent = 'Hands: Ready (Native)';
    document.body.appendChild(statusDiv);
}

function updateStatus(text, color = '#fff') {
    if (!statusDiv) createStatusOverlay();
    if (statusDiv) {
        statusDiv.textContent = `Hands: ${text}`;
        statusDiv.style.color = color;
    }
}

if (document.body) {
    createStatusOverlay();
} else {
    window.addEventListener('DOMContentLoaded', createStatusOverlay);
}

// --- Communication ---

// Listen for commands from Background (relayed from Python)
chrome.runtime.onMessage.addListener(async (message, sender, sendResponse) => {
    console.log("Hands: Received command:", message);
    if (message.command) {
        updateStatus(`Exec: ${message.command.action}`, '#ffff00');
        await handleCommand(message.command);
    }
});

// Send result back to Background (to be relayed to Python)
function sendToBrain(data) {
    updateStatus('Sending result...', '#00ccff');
    chrome.runtime.sendMessage(data, () => {
         updateStatus('Idle (Connected)', '#00ff00');
    });
}


// --- Command Handling (Same logic as Userscript) ---
async function handleCommand(command) {
    let result = { id: command.id, status: 'error', message: 'Command not handled' };
    try {
        switch (command.action) {
            case 'navigate':
                console.log(`Hands: Navigating to ${command.url}`);
                updateStatus(`Navigating: ${command.url}`, '#ffff00');
                // Prepare result message BEFORE navigation
                result = { id: command.id, status: 'success', message: 'Navigation initiated' };

                // Attempt to send result message, and then navigate.
                // We use a callback to ensure the message is sent before the page unloads.
                chrome.runtime.sendMessage(result, (response) => {
                    if (chrome.runtime.lastError) {
                        console.error("Hands: Error sending navigation result:", chrome.runtime.lastError.message);
                    } else {
                        console.log("Hands: Navigation result acknowledged by background.");
                    }
                    // Navigate, even if sending to message failed, as the page context is lost anyway
                    window.location.href = command.url;
                });
                return; // Stop further execution in this handler

            case 'type':
                const inputElement = await waitForSelector(command.selector);
                if (inputElement) {
                    inputElement.value = command.value;
                    const parentForm = inputElement.closest('form');
                    if (parentForm) {
                        parentForm.submit();
                        result = { id: command.id, status: 'success', message: 'Typed and submitted' };
                    } else {
                        // Trigger events
                        inputElement.dispatchEvent(new Event('input', { bubbles: true }));
                        inputElement.dispatchEvent(new Event('change', { bubbles: true }));
                         // Simulate Enter key
                        inputElement.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', bubbles: true }));
                         result = { id: command.id, status: 'success', message: 'Typed and dispatched events' };
                    }
                } else {
                    result = { id: command.id, status: 'error', message: `Element not found: ${command.selector}`};
                }
                break;

            case 'click':
                const clickElement = await waitForSelector(command.selector);
                if (clickElement) {
                    clickElement.click();
                    result = { id: command.id, status: 'success', message: 'Clicked element' };
                } else {
                    result = { id: command.id, status: 'error', message: `Element not found: ${command.selector}`};
                }
                break;

            case 'wait_for_selector':
                const foundElement = await waitForSelector(command.selector, command.timeout || 10000);
                 if (foundElement) {
                    result = { id: command.id, status: 'success', message: `Element "${command.selector}" appeared.`};
                } else {
                    result = { id: command.id, status: 'error', message: `Timeout waiting for: ${command.selector}`};
                }
                break;

            case 'extract_urls':
                const links = Array.from(document.querySelectorAll(command.selector));
                const urls = links.map(link => link.href).filter(href => href && href.startsWith('http'));
                result = { id: command.id, status: 'success', data: urls };
                break;

            case 'extract_search_results':
                const results = [];
                const articles = document.querySelectorAll('article[data-testid="result"]');
                
                articles.forEach((article, index) => {
                    try {
                        const titleEl = article.querySelector('h2 a span');
                        const linkEl = article.querySelector('h2 a');
                        const snippetEl = article.querySelector('div[data-result="snippet"]');
                        
                        if (titleEl && linkEl) {
                            results.push({
                                rank: index + 1,
                                title: titleEl.textContent.trim(),
                                link: linkEl.href,
                                details: snippetEl ? snippetEl.textContent.trim() : ""
                            });
                        }
                    } catch (err) {
                        console.warn("Error parsing result:", err);
                    }
                });
                
                result = { id: command.id, status: 'success', data: results };
                break;
                
            default:
                result = { id: command.id, status: 'error', message: `Unknown command: ${command.action}`};
        }
    } catch (e) {
        console.error("Hands: Error:", e);
        result = { id: command.id, status: 'error', message: e.message };
    }
    
    sendToBrain(result);
}

async function waitForSelector(selector, timeout = 10000) {
    return new Promise((resolve) => {
        if (document.querySelector(selector)) return resolve(document.querySelector(selector));

        const observer = new MutationObserver(mutations => {
            if (document.querySelector(selector)) {
                observer.disconnect();
                resolve(document.querySelector(selector));
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        setTimeout(() => {
            observer.disconnect();
            resolve(null);
        }, timeout);
    });
}
"""

# --- Part 2: Python Host Implementation ---

# Ensure we can import from src (if this script is moved)
sys.path.insert(0, os.getcwd())

# Configure logging to file since stdout is used for communication
logging.basicConfig(
    filename="native_host.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


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

    def get_incoming_message(self, block=True, timeout=None):
        """Retrieves the next message sent by the browser (not a result)."""
        try:
            return self.incoming_messages.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    def _get_next_command_id(self):
        self.current_command_id += 1
        return self.current_command_id

    def send_command(self, command):
        """Sends a command to the Chrome Extension."""
        command_id = self._get_next_command_id()
        command["id"] = command_id

        message = {"command": command}
        self._send_message(message)
        logging.info(f"Sent command {command_id}: {command['action']}")
        return command_id

    def get_result(self, command_id, timeout=30):
        """Waits for a result for a specific command ID."""
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
        self.running = False


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
            data = result.get("data", [])
            formatted_json = json.dumps(data, indent=2)
            logging.info(f"Extracted Search Results:\n{formatted_json}")

            # If we want to save to a file for the user to see easily:
            with open("search_results.json", "w") as f:
                f.write(formatted_json)
            return data
        return []


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

    # Start of External Command Server (TCP)
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


# --- Part 3: Trigger Client Script (Embedded) ---

TRIGGER_CLIENT = r"""#!/usr/bin/env python3
import socket
import sys

def send_trigger(query):
    HOST = "127.0.0.1"
    PORT = 9999

    message = f"search:{query}"

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(message.encode())
            data = s.recv(1024)

        print(f"Sent: '{query}'")
        print(f"Response: {data.decode()}")

    except ConnectionRefusedError:
        print("Error: Could not connect to Stealth Automation.")
        print("Make sure Chrome is open and the extension is loaded.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python trigger.py "Your Search Query"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    send_trigger(query)
"""

# --- Part 4: Extraction Helper ---


def write_files_if_requested():
    """
    Utility function to extract and write the extension files to disk.
    Useful if the user wants to quickly generate the extension files from this archive.
    """
    import os

    dir_name = "stealth_automation_extension_files"
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
        print(f"Created directory '{dir_name}' for extension files.")

    # Write Manifest
    with open(os.path.join(dir_name, "manifest.json"), "w") as f:
        f.write(EXTENSION_MANIFEST)
    print(f"Wrote: {os.path.join(dir_name, 'manifest.json')}")

    # Write Background Script
    with open(os.path.join(dir_name, "background.js"), "w") as f:
        f.write(BACKGROUND_JS)
    print(f"Wrote: {os.path.join(dir_name, 'background.js')}")

    # Write Content Script
    with open(os.path.join(dir_name, "content.js"), "w") as f:
        f.write(CONTENT_JS)
    print(f"Wrote: {os.path.join(dir_name, 'content.js')}")

    # Write Trigger Client
    with open(os.path.join(dir_name, "trigger.py"), "w") as f:
        f.write(TRIGGER_CLIENT)
    print(f"Wrote: {os.path.join(dir_name, 'trigger.py')}")

    # Make trigger client executable
    os.chmod(os.path.join(dir_name, "trigger.py"), 0o755)
    print(f"Made executable: {os.path.join(dir_name, 'trigger.py')}")

    print("\nExtension files generated successfully.")
    print("Load 'stealth_automation_extension_files' folder in Chrome.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--extract-extension":
        write_files_if_requested()
        sys.exit(0)

    # Standard execution: Run the Native Host
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.critical(f"Main crashed: {e}")
