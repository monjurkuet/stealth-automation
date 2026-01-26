# Setup Guide

## Prerequisites

- Python 3.7+
- Chrome (recent version supporting Manifest V3)
- Linux, macOS, or Windows
- `uv` package manager (recommended)

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/monjurkuet/stealth-automation.git
cd stealth-automation
```

### 2. Install Dependencies

Using uv (recommended):
```bash
# Install uv if not already installed
pip install uv

# Create virtual environment and install dependencies
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### 3. Chrome Extension Setup

#### Load Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle top-right)
3. Click "Load unpacked"
4. Select the `extension/` folder in the cloned repository

#### Configure Native Host

The extension uses Native Messaging to communicate with Python scripts.

**Linux (Ubuntu/Debian):**
```bash
./host/install_host.sh
```

Then edit `~/.config/google-chrome/NativeMessagingHosts/com.stealth.automation.json`:
```json
{
  "name": "com.stealth.automation",
  "description": "Stealth Automation Native Host",
  "path": "/home/youruser/dev/stealth-automation/main_native.py",
  "type": "stdio",
  "allowed_origins": ["chrome-extension://YOUR_EXTENSION_ID/"]
}
```

**MacOS:**
```bash
mkdir -p ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts
cp host/com.stealth.automation.json ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/
```

Update `path` and `allowed_origins` as described above.

**Windows:**
Edit registry or place manifest in:
```
C:\Users\<User>\AppData\Local\Google\Chrome\User Data\Default\NativeMessagingHosts\
```

Update `path` (using `\\` separators) and `allowed_origins`.

#### Find Extension ID

1. Go to `chrome://extensions/`
2. Copy the extension ID from the card

## Usage

### Starting the Native Host

The browser will attempt to launch `main_native.py` automatically. If it fails:

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run the native host
python3 main_native.py
```

### Triggering Automation

#### Method 1: Browser Popup

1. Click the Stealth Automation icon in your toolbar
2. Select platform (e.g., "DuckDuckGo")
3. Enter your query (e.g., "Best Python automation tools")
4. Click "Start"

#### Method 2: CLI Trigger

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run automation
python3 trigger.py duckduckgo "your search query"

# List available platforms
python3 trigger.py list
```

### Viewing Results

Results are saved to JSONL files in `output/results/`:

```bash
# View latest results
cat output/results/duckduckgo_*.jsonl
```

Output format:
```jsonl
{"status": "item", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:00Z", "data": {"rank": 1, "title": "...", "link": "..."}}
{"status": "summary", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:05Z", "data": {"total_items": 10}}
```

### Viewing Logs

Logs are written to `native_host.log`:

```bash
tail -f native_host.log
```

## Configuration

### Platform Configuration

Each platform has a YAML config file in `config/`:

**Example: `config/duckduckgo.yaml`**
```yaml
platform: duckduckgo
base_url: "https://duckduckgo.com/"
selectors:
  search_input: "input#searchbox_input"
  search_button: "button[type='submit']"
  results_container: "ol.react-results--main"
  result_item: "article[data-testid='result']"
  result_title: "h2 a[data-testid='result-title-a']"
  result_link: "h2 a[data-testid='result-title-a']"
  result_snippet: "div[data-result='snippet']"
  next_page_button: "button#more-results"
settings:
  iteration:
    type: pagination
    max_pages: 5
    max_items: 50
    scroll_before_next_page: true
  rate_limiting:
    action_delay_ms: 500
    page_load_delay_ms: 2000
    randomize_delay: true
    max_actions_per_minute: 30
  output:
    file: "output/results/duckduckgo_results.jsonl"
timeouts:
  browser_action_s: 30
  task_execution_s: 300
```

### Rate Limiting

Control delays between actions in config:

```yaml
rate_limiting:
  action_delay_ms: 500      # Delay between type/click
  page_load_delay_ms: 2000  # Delay after navigation
  randomize_delay: true     # Add +/- 20% jitter
  max_actions_per_minute: 30  # Rate limit
```

### Iteration Strategies

Choose how results are collected:

```yaml
iteration:
  type: pagination      # Page 1, 2, 3...
  max_pages: 5
```

Or:

```yaml
iteration:
  type: infinite_scroll  # Keep loading until end
  max_items: 50
  scroll_delay_ms: 1000
```

Or:

```yaml
iteration:
  type: depth          # Visit all linked pages
  max_depth: 2
  same_domain_only: true
```

## Troubleshooting

### Extension not connecting

1. Check extension ID matches in manifest
2. Verify native host path is correct
3. Check `native_host.log` for errors

### Port 9999 busy

```bash
# Find process using port
lsof -i :9999

# Kill process
kill -9 <PID>
```

### Config validation errors

```bash
# Validate config manually
python3 -c "import yaml, jsonschema; yaml.safe_load(open('config/duckduckgo.yaml'))"
```

### Selector not found

1. Use Chrome DevTools to inspect elements
2. Update selector in `config/*.yaml`
3. Restart native host

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for system overview
- Read [CREATING_TASKS.md](CREATING_TASKS.md) to add new platforms
- Read [CONFIGURATION.md](CONFIGURATION.md) for detailed config options
