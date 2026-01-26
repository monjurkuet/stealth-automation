# Stealth Automation Framework

A 100% stealth browser automation framework using HTTP-based communication between Python logic and Chrome browser actions.

## Features

- **Undetectable:** Uses HTTP polling via Chrome Extension, avoiding CSP and network detection common in traditional bots
- **Architecture:** "Brain-Bridge-Hands" model separating logic (Python) from execution (Browser Extension)
- **Multi-Platform:** Supports multiple search platforms including DuckDuckGo, with extensible task system for adding new platforms
- **Advanced Automation:** Configurable timeouts, rate limiting, pagination strategies (including scroll-before-click), and result extraction
- **Flexible Output:** Saves results in JSONL format with raw HTML for debugging and progress tracking
- **CLI Interface:** Command-line tool supporting multiple platforms and configuration options
- **Result Analysis:** Built-in tools for parsing results and updating CSS selectors

## Architecture

1. **Brain (Python):** Handles high-level logic, task management, and state located in `src/brain/`
2. **Bridge (FastAPI):** HTTP server on port 9427 managing bidirectional communication with the extension
3. **Hands (Chrome Extension):**
   - **Background Script:** Service worker polling for commands via HTTP
   - **Content Script:** DOM manipulation executing browser actions
   - **Popup:** Simple UI to trigger automation manually

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/monjurkuet/stealth-automation.git
cd stealth-automation
```

### 2. Install Dependencies

Using pip:
```bash
pip install -r requirements.txt
```

Or using uv (recommended):
```bash
pip install uv
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### 3. Chrome Extension Setup

1. **Load Extension:**
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle top-right)
   - Click "Load unpacked" and select the `extension/` folder in the cloned repository

2. **Verify Extension:**
   - The extension should appear in your extensions list
   - Open a new tab and check the browser console for "Stealth Automation: Content Script Loaded"

## Usage

### Starting the Automation

1. **Start the HTTP Server:**
   ```bash
   python3 main_native.py
   ```
   The server will start on `http://127.0.0.1:9427`

2. **Triggering Automation:**

   **Method 1: Browser Popup**
   - Click the Stealth Automation icon in your toolbar
   - Select platform (e.g., "DuckDuckGo")
   - Enter your query (e.g., "Best stealth automation tools")
   - Click "Start"
   - The browser will navigate, type, wait, and extract results

   **Method 2: Python Trigger Script**
   ```bash
   python3 trigger.py duckduckgo "Your Search Query"
   # List available platforms
   python3 trigger.py list
   ```

### Viewing Results

Search results are automatically saved to JSONL files in `output/results/` (e.g., `duckduckgo_20260126_064518.jsonl`).

**Output Format (JSONL):**
```jsonl
{"status": "item", "platform": "duckduckgo", "timestamp": "2026-01-26T06:45:27.171134+00:00", "data": {"rank": 1, "title": "Example Title", "link": "https://example.com/article", "details": "Example snippet text...", "raw_html": "<article>...</article>"}}
{"status": "summary", "platform": "duckduckgo", "timestamp": "2026-01-26T06:45:27.171134+00:00", "data": {"query": "stealth automation", "total_items": 192, "pages_processed": 6, "duration_ms": 82676}}
```

### Result Analysis Tools

**parse_results.py** - Parse and analyze results:

```bash
# Show summary and all items
python3 parse_results.py --summary --items

# Inspect raw HTML for a specific item (to find CSS selectors)
python3 parse_results.py --inspect 0

# Export to CSV or JSON
python3 parse_results.py --csv results.csv
python3 parse_results.py --json results.json

# View errors
python3 parse_results.py --errors
```

**update_selectors.py** - Update CSS selectors from raw HTML:

```bash
# Inspect HTML and get selector suggestions
python3 update_selectors.py --file output/results/duckduckgo_20260126_064518.jsonl --item 0

# Update config file automatically
python3 update_selectors.py --file output/results/duckduckgo_20260126_064518.jsonl --item 0 --update config/duckduckgo.yaml
```

## Development

### Adding New Platforms

1. Create a new task class in `src/brain/tasks/`:
```python
from src.brain.base import BaseAutomation

class NewPlatformTask(BaseAutomation):
    async def execute(self, query: str, **kwargs) -> Dict:
        # Navigate to platform
        await self._navigate(self.config["base_url"])
        
        # Type query
        await self._type(self.config["selectors"]["search_input"], query)
        
        # Extract results
        results = await self._extract_current_page()
        
        return {"status": "success", "data": {"results": results}}
```

2. Register the platform in `src/brain/tasks/__init__.py`:
```python
AutomationFactory.register("newplatform", NewPlatformTask)
```

3. Create a config file `config/newplatform.yaml`:
```yaml
platform: newplatform
base_url: "https://example.com/"
selectors:
  search_input: "input#search"
  results_container: "div.results"
  result_item: "div.result"
  result_title: "h2 a"
  result_link: "h2 a"
  result_snippet: "p.snippet"
settings:
  iteration:
    type: pagination
    max_pages: 5
    max_items: 100
  rate_limiting:
    action_delay_ms: 1000
    page_load_delay_ms: 2000
  timeouts:
    browser_action_s: 30
```

### Configuration

Platform configurations are stored in `config/` directory as YAML files:

- **selectors:** CSS selectors for DOM elements
- **settings.iteration:** Pagination strategy (pagination, infinite_scroll, depth)
- **settings.rate_limiting:** Delays and rate limits
- **settings.timeouts:** Timeout values for browser actions

## Project Structure

```
stealth-automation/
├── extension/               # Chrome Extension files
│   ├── manifest.json        # Extension configuration (Manifest V3)
│   ├── background.js       # Service worker / HTTP polling
│   ├── content.js         # DOM manipulation / Hands
│   └── popup.html          # Simple trigger UI
├── src/
│   ├── brain/             # Logic (Python)
│   │   ├── main.py          # Orchestrator
│   │   ├── base.py          # Base automation class
│   │   ├── factory.py       # Task factory
│   │   ├── tasks/           # Platform-specific tasks
│   │   │   ├── __init__.py  # Task registration
│   │   │   └── duckduckgo.py
│   │   └── utils/           # Utilities
│   │       ├── progress.py  # Progress tracking
│   │       ├── retry.py     # Retry logic
│   │       ├── storage.py   # JSONL storage
│   │       └── validation.py # Config validation
│   ├── bridge/            # HTTP Bridge (Python)
│   │   ├── http.py          # FastAPI server
│   │   └── http_bridge.py   # HTTPBridge class
│   └── common/            # Shared utilities
│       ├── config.py       # Config loader
│       └── logging_config.py # Logging setup
├── config/                # Platform configurations (YAML)
│   ├── duckduckgo.yaml
│   └── schema.json
├── docs/                  # Documentation
│   ├── ARCHITECTURE.md
│   ├── CONFIGURATION.md
│   ├── JSONL_FORMAT.md
│   └── PAGINATION_STRATEGIES.md
├── output/                # Results (JSONL format)
│   └── results/
├── main_native.py         # HTTP server entry point
├── trigger.py            # Python trigger client
├── parse_results.py      # Result analysis tool
├── update_selectors.py   # CSS selector updater
├── requirements.txt      # Python dependencies
├── AGENTS.md             # Development protocol
└── README.md
```

## Requirements

- **Python:** 3.9+
- **Chrome:** A recent version supporting Manifest V3
- **OS:** Linux, macOS, or Windows

## License

MIT License - Feel free to use this project for personal or commercial use.

## Contributing

Contributions are welcome! Please read the development protocol in `AGENTS.md` before contributing.