// background.js
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
