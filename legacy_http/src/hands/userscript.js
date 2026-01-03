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
