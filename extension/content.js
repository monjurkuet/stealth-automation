// content.js
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

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log("Hands: Received command:", message);
    if (message.action || message.id) {
        updateStatus(`Exec: ${message.action}`, '#ffff00');
        handleCommand(message).then(response => sendResponse(response));
        return true;
    }
    if (message.command) {
        updateStatus(`Exec: ${message.command.action}`, '#ffff00');
        handleCommand(message.command).then(response => sendResponse(response));
        return true;
    }
});

// Send result back to Background (to be relayed to Python)
function sendToBrain(data) {
    updateStatus('Sending result...', '#00ccff');
    chrome.runtime.sendMessage(data, () => {
         updateStatus('Idle (Connected)', '#00ff00');
    });
}


async function handleCommand(command) {
    let result = { id: command.id, status: 'error', message: 'Command not handled' };
    try {
        switch (command.action) {
            case 'navigate':
                console.log(`Hands: Navigating to ${command.url}`);
                updateStatus(`Navigating: ${command.url}`, '#ffff00');
                result = { id: command.id, status: 'success', message: 'Navigation initiated', data: { url: command.url } };
                setTimeout(() => {
                    window.location.href = command.url;
                }, 100);
                return result;

            case 'type':
                const inputElement = await waitForSelector(command.selector);
                if (inputElement) {
                    inputElement.value = command.value;
                    const parentForm = inputElement.closest('form');
                    if (parentForm) {
                        parentForm.submit();
                        result = { id: command.id, status: 'success', message: 'Typed and submitted' };
                    } else {
                        inputElement.dispatchEvent(new Event('input', { bubbles: true }));
                        inputElement.dispatchEvent(new Event('change', { bubbles: true }));
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
                result = { id: command.id, status: 'success', data: urls};
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
                                details: snippetEl ? snippetEl.textContent.trim() : "",
                                raw_html: article.outerHTML
                            });
                        }
                    } catch (err) {
                        console.warn("Error parsing result:", err);
                    }
                });
                
                result = { id: command.id, status: 'success', data: { results: results, page_html: document.documentElement.outerHTML.substring(0, 50000) } };
                break;

            case 'extract_html':
                const html = document.documentElement.outerHTML;
                const truncated = html.length > 100000 ? html.substring(0, 100000) : html;
                result = { id: command.id, status: 'success', data: { html: truncated, total_length: html.length, truncated: html.length > 100000 } };
                break;
                
            case 'scroll_to_bottom':
                console.log("Hands: Scrolling to bottom");
                window.scrollTo(0, document.body.scrollHeight);
                result = { id: command.id, status: 'success', message: 'Scrolled to bottom' };
                break;

            default:
                result = { id: command.id, status: 'error', message: `Unknown command: ${command.action}`};
        }
    } catch (e) {
        console.error("Hands: Error:", e);
        result = { id: command.id, status: 'error', message: e.message };
    }
    
    return result;
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
