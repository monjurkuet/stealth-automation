// background.js
console.log("Stealth Automation: Background Service Worker Starting...");

let pollingInterval = null;

function startPolling() {
    if (pollingInterval) return;
    
    pollingInterval = setInterval(async () => {
        try {
            const response = await fetch("http://127.0.0.1:9427/get_command");
            const data = await response.json();
            
            if (data.status === "success" && data.command) {
                console.log("Stealth Automation: Received command:", data.command);
                await executeCommand(data.command);
            }
        } catch (error) {
            console.error("Stealth Automation: Polling error:", error);
        }
    }, 100);
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

async function executeCommand(command) {
    try {
        const tabs = await chrome.tabs.query({ active: true });
        if (tabs.length === 0 || !tabs[0].id) {
            console.warn("Stealth Automation: No active tab found");
            await fetch("http://127.0.0.1:9427/command_result", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id: command.id, status: "error", message: "No active tab found" })
            });
            return;
        }

        const tab = tabs[0];
        console.log(`Stealth Automation: Sending command to tab ${tab.id} (${tab.url}):`, command);
        
        chrome.tabs.sendMessage(tab.id, command, (response) => {
            if (chrome.runtime.lastError) {
                console.error("Stealth Automation: Content script error:", chrome.runtime.lastError.message);
                fetch("http://127.0.0.1:9427/command_result", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ id: command.id, status: "error", message: chrome.runtime.lastError.message })
                });
                return;
            }
            
            const result = {
                id: command.id,
                status: response?.status || "success",
                message: response?.message,
                data: response?.data
            };
            
            fetch("http://127.0.0.1:9427/command_result", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(result)
            });
            
            console.log("Stealth Automation: Command result sent:", result);
        });
    } catch (error) {
        console.error("Stealth Automation: Command execution error:", error);
        const errorResult = {
            id: command.id,
            status: "error",
            message: error.message
        };
        
        await fetch("http://127.0.0.1:9427/command_result", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(errorResult)
        });
    }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "TRIGGER_NATIVE") {
        console.log("Stealth Automation: Trigger received:", message.payload);
        
        fetch("http://127.0.0.1:9427/execute", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(message.payload)
        })
        .then(response => response.json())
        .then(data => {
            console.log("Stealth Automation: Received from Native:", data);
            sendResponse({status: "sent", data: data});
        })
        .catch(error => {
            console.error("Stealth Automation: HTTP request failed:", error);
            sendResponse({status: "error", message: error.message});
        });
        
        return true;
    }

    console.log("Stealth Automation: Received from Content:", message);
    fetch("http://127.0.0.1:9427/command_result", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(message)
    })
    .catch(error => {
        console.error("Stealth Automation: Failed to send result:", error);
    });
});

chrome.runtime.onStartup.addListener(() => {
    console.log("Stealth Automation: Browser starting up");
    startPolling();
});

chrome.runtime.onSuspend.addListener(() => {
    console.log("Stealth Automation: Service worker suspending");
    stopPolling();
});

startPolling();