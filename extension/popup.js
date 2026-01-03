document.getElementById('searchBtn').addEventListener('click', () => {
    const query = document.getElementById('query').value;
    const status = document.getElementById('status');
    
    status.textContent = "Sending command...";
    
    // Send message to background script
    chrome.runtime.sendMessage({
        type: "TRIGGER_NATIVE",
        payload: {
            action: "start_search",
            query: query
        }
    }, (response) => {
        if (chrome.runtime.lastError) {
             status.textContent = "Error: " + chrome.runtime.lastError.message;
        } else {
             status.textContent = "Command sent!";
        }
    });
});
