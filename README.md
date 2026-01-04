# Stealth Automation Framework

A 100% stealth browser automation framework using Chrome Native Messaging for communication between Python logic and Chrome browser actions.

## Features

- **Undetectable:** Uses Chrome Native Messaging, bypassing Content Security Policy (CSP) and avoiding network-based detection common in traditional bots.
- **Architecture:** "Brain-Bridge-Hands" model separating logic (Python) from execution (Browser Extension).
- **Multi-Platform:** Supports multiple search platforms including DuckDuckGo, with extensible task system for adding new platforms.
- **Advanced Automation:** Configurable timeouts, rate limiting, pagination strategies (including scroll-before-click), and result extraction.
- **Flexible Output:** Saves results in JSONL format with progress tracking and error handling.
- **CLI Interface:** Command-line tool supporting multiple platforms and configuration options.

## Architecture

1.  **Brain (Python):** Handles high-level logic, task management, and state.
2.  **Bridge (Python):** A `NativeBridge` class managing binary communication via stdin/stdout with the Chrome Native Host.
3.  **Hands (Chrome Extension):**
    -   **Background Script:** Service worker acting as a message router between Python and Content Scripts.
    -   **Content Script:** The "hands" executing DOM manipulations in the browser context.
    -   **Popup:** Simple UI to trigger automation manually.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/monjurkuet/stealth-automation.git
cd stealth-automation
```

### 2. Install Dependencies

Using uv (recommended):
```bash
pip install uv
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

Or using pip:
```bash
pip install -r requirements.txt
```

### 2. Chrome Extension Setup

1.  **Load Extension:**
    -   Open Chrome and navigate to `chrome://extensions/`.
    -   Enable "Developer mode" (toggle top-right).
    -   Click "Load unpacked" and select the `extension/` folder in the cloned repository.

2.  **Configure Native Host:**
    -   This extension uses Native Messaging to communicate with a Python script on your system.
    -   You need to configure the host manifest file.
    
    **Linux (Ubuntu/Debian):**
    ```bash
    ./host/install_host.sh
    ```
    -   Edit `~/.config/google-chrome/NativeMessagingHosts/com.stealth.automation.json`.
    -   Update the `"path"` to point to your full local repository path (e.g., `/home/user/dev/stealth-automation/main_native.py`).
    -   Update `"allowed_origins"` to include your Extension ID (found in `chrome://extensions/`).

    **MacOS:**
    ```bash
    mkdir -p ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts
    cp host/com.stealth.automation.json ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/
    ```
    -   Update `path` and `allowed_origins` as described above.

    **Windows:**
    -   Edit registry keys or place manifest in:
        `C:\Users\<User>\AppData\Local\Google\Chrome\User Data\Default\NativeMessagingHosts\`
    -   Update `path` (using `\\` separators) and `allowed_origins`.

## Usage

### Starting the Automation

Once installed, the automation starts automatically when you open Chrome.

1.  **Run the Native Host:**
    The browser will attempt to launch `main_native.py` automatically. If it fails (permission issues), you can run it manually:
    ```bash
    python3 main_native.py
    ```

2.  **Triggering Automation:**

    *   **Method 1: Browser Popup**
        *   Click the Stealth Automation icon in your toolbar.
        *   Select platform (e.g., "DuckDuckGo").
        *   Enter your query (e.g., "Best stealth automation tools").
        *   Click "Start".
        *   The browser will navigate, type, wait, and extract results.

    *   **Method 2: Python Trigger Script**
        *   Use the provided `trigger.py`:
        ```bash
        python3 trigger.py duckduckgo "Your Search Query"
        # List available platforms
        python3 trigger.py list
        ```

### Viewing Results

Search results are automatically saved to JSONL files in `output/results/` (e.g., `duckduckgo_results.jsonl`).

**Output Format (JSONL):**
```jsonl
{"status": "item", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:00Z", "data": {"rank": 1, "title": "Example Title", "link": "https://example.com/article", "snippet": "Example snippet text..."}}
{"status": "summary", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:05Z", "data": {"total_items": 10, "pages_processed": 2, "duration_ms": 5000}}
```

You can also view execution logs in `native_host.log`.

## Development

### Using the Monolithic Archive

For quick testing or deployment without the full file structure, use the included monolithic script.

```bash
# Generate extension files from archive (optional, if you just want the files)
python3 stealth_automation_native_archive.py --extract-extension

# Run the monolithic host (Native Host + Logic + Bridge)
python3 stealth_automation_native_archive.py
```

The archive (`stealth_automation_native_archive.py`) is a single file containing:
-   Python `NativeBridge` class.
-   Python `Logic` class.
-   Python `main()` function (Native Host entry point).
-   Embedded Chrome Extension code (`manifest.json`, `background.js`, `content.js`).
-   Embedded `trigger.py` client.

### Legacy HTTP Version

The `legacy_http/` directory contains the previous HTTP polling implementation.
-   *   **Extension:** `src/hands/userscript.js` (Tampermonkey userscript).
-   *   **Bridge:** `src/bridge/server.py` (HTTP Server).
-   *   **Brain:** `src/brain/main.py` (Logic using `HttpBridge`).

This version is provided for reference but is **not recommended** for production use due to CSP restrictions and network detectability.

## Project Structure

```
stealth-automation/
├── extension/               # Chrome Extension files
│   ├── manifest.json        # Extension configuration
│   ├── background.js       # Service worker / Router
│   ├── content.js         # DOM manipulation / Hands
│   └── popup.html          # Simple trigger UI
├── src/
│   ├── brain/             # Logic (Python)
│   │   ├── main.py          # Search logic
│   │   └── __init__.py
│   └── bridge/            # Native Bridge (Python)
│       ├── native.py       # Native Messaging implementation
│       └── __init__.py
├── host/                   # Native Host Configuration
│   ├── com.stealth.automation.json
│   └── install_host.sh
├── main_native.py           # Native Host Entry Point
├── trigger.py              # Python Trigger Client
├── stealth_automation_native_archive.py # Monolithic Archive
└── legacy_http/            # Old HTTP Polling Implementation (Archive)
```

## Requirements

-   **Python:** 3.7+
-   **Chrome:** A recent version supporting Manifest V3 and Native Messaging.
-   **OS:** Linux, macOS, or Windows.

## License

MIT License - Feel free to use this project for personal or commercial use.
