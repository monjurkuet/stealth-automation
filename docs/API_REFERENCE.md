# API Reference

## Core Classes

### Orchestrator

Main orchestrator for automation tasks.

#### Methods

**`__init__(bridge: NativeBridge)`**
- Initialize orchestrator with NativeBridge instance

**`async dispatch(message: Dict) -> Dict`**
- Dispatch task based on message content
- Returns: Standardized result dict

**`async list_platforms() -> Dict`**
- List all available platforms
- Returns: Platform info dict

### AutomationFactory

Factory for creating task instances.

#### Class Methods

**`@classmethod register(platform: str, task_class: Type[BaseAutomation])`**
- Register a task class for a platform
- Raises warning if already registered

**`@classmethod create(platform: str, bridge, **kwargs) -> BaseAutomation`**
- Create task instance for platform
- Raises: `ValueError` if platform unknown

**`@classmethod list_available() -> list`**
- Return list of registered platform names

**`@classmethod get_platform_info(platform: str) -> Dict`**
- Get detailed info about a platform
- Returns: Platform info dict

### BaseAutomation

Abstract base class for all automation tasks.

#### Constructor

**`__init__(bridge: NativeBridge, platform: str)`**
- Initialize task with bridge and platform name
- Loads configuration from YAML
- Creates JSONL storage and progress tracker

#### Abstract Methods

**`async execute(query: str, **kwargs) -> Dict`**
- Main entry point for task execution
- Must be implemented by subclasses

#### Protected Methods

**`async _navigate(url: str)`**
- Navigate browser to URL
- Raises: `Exception` on navigation failure

**`async _type(selector: str, value: str)`**
- Type text into element
- Raises: `Exception` on failure

**`async _click(selector: str)`**
- Click element
- Raises: `Exception` on failure

**`async _scroll_to_bottom()`**
- Scroll page to bottom

**`async _wait_for_results()`**
- Wait for results container to appear
- Raises: `TimeoutError` if not found

**`async _extract_current_page() -> List[Dict]`**
- Extract results from current page
- Returns: List of result dicts

**`async _extract_links() -> List[str]`**
- Extract links from current page
- Returns: List of URL strings

**`async _click_next_page() -> bool`**
- Click next page button
- Returns: True if clicked, False if not found

**`async iterate_results(strategy: str, callback: Callable, max_items: Optional[int]) -> List[Dict]`**
- Execute iteration strategy
- Strategy: 'pagination', 'infinite_scroll', or 'depth'
- Callback: Function called for each page
- Returns: All collected results

**`async _with_retry(coro, retries: int, backoff_factor: float)`**
- Execute coroutine with exponential backoff retry
- Returns: Coroutine result

**`async _with_rate_limit()`**
- Apply configured rate limiting delay

### NativeBridge

Singleton bridge for Native Messaging communication.

#### Constructor

**`__init__()`**
- Initialize bridge (singleton pattern)
- Starts read thread for stdin

#### Methods

**`send_command(command: Dict) -> int`**
- Send command to Chrome extension
- Returns: Command ID for matching results

**`get_result(command_id: int, timeout: int = 30) -> Dict`**
- Wait for result by command ID
- Returns: Result dict or error on timeout

**`get_incoming_message(block: bool = True, timeout: Optional[int] = None) -> Optional[Dict]`**
- Retrieve next message from browser
- Returns: Message dict or None

**`shutdown()`**
- Signal bridge to stop

### JSONLStorage

Append-only JSONL file storage.

#### Constructor

**`__init__(filepath: str)`**
- Initialize storage with output filepath
- Creates parent directories if needed

#### Methods

**`async append_item(platform: str, data: Dict)`**
- Append a single item entry to file

**`async append_summary(platform: str, summary: Dict)`**
- Append a summary entry to file

**`async append_error(platform: str, error: Dict)`**
- Append an error entry to file

**`async append_progress(platform: str, progress: Dict)`**
- Append a progress event to file

**`get_filepath() -> str`**
- Get current output filepath

### ProgressTracker

Track and emit progress events.

#### Constructor

**`__init__(platform: str, bridge: Optional[NativeBridge] = None)`**
- Initialize tracker with platform and optional bridge

#### Methods

**`async emit(event_type: str, data: Optional[Dict] = None)`**
- Emit progress event
- Sends to bridge if available

**`get_summary() -> Dict`**
- Get progress summary statistics
- Returns: Dict with duration, event counts

## Data Structures

### Standardized Result Format

All tasks must return this format:

```python
{
    "status": "success" | "error",
    "platform": "duckduckgo",
    "action": "search",
    "data": {
        # Platform-specific data
        "results": [...]
    },
    "error": {
        # Only if status is "error"
        "code": "TIMEOUT",
        "message": "..."
    },
    "performance": {
        "duration_ms": 5000,
        "items_per_second": 10.5,
        "retries": 0
    }
}
```

### Message Formats

#### Python → Chrome (Commands)

```python
{
    "command": {
        "id": 1,
        "action": "navigate",
        "url": "https://duckduckgo.com/"
    }
}
```

#### Chrome → Python (Results)

```python
{
    "id": 1,
    "status": "success",
    "message": "Navigation initiated"
}
```

#### Trigger Messages (External/Popup → Python)

```python
{
    "action": "start_task",
    "platform": "duckduckgo",
    "query": "your search query"
}
```

### JSONL Entry Format

```jsonl
{"status": "item", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:00Z", "data": {"rank": 1, ...}}
{"status": "summary", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:05Z", "data": {"total_items": 10}}
{"status": "error", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:06Z", "error": {"code": "...", ...}}
{"status": "progress", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:01Z", "data": {"event_type": "task_start", ...}}
```

## Content Script Commands

Commands available in `extension/content.js`:

### navigate
Navigate to URL.

```javascript
{
    "action": "navigate",
    "url": "https://example.com/"
}
```

### type
Type text into element.

```javascript
{
    "action": "type",
    "selector": "input#search",
    "value": "search query"
}
```

### click
Click element.

```javascript
{
    "action": "click",
    "selector": "button.submit"
}
```

### wait_for_selector
Wait for element to appear.

```javascript
{
    "action": "wait_for_selector",
    "selector": "div.results",
    "timeout": 10000
}
```

### extract_search_results
Extract search results from page.

```javascript
{
    "action": "extract_search_results"
}
```

### extract_urls
Extract URLs from elements.

```javascript
{
    "action": "extract_urls",
    "selector": "a[href]"
}
```

### scroll_to_bottom
Scroll page to bottom.

```javascript
{
    "action": "scroll_to_bottom"
}
```

### progress_update
Log progress event.

```javascript
{
    "action": "progress_update",
    "event": {...}
}
```

## Constants

### src/common/config.py

```python
TCP_HOST = "127.0.0.1"
TCP_PORT = 9999
DEFAULT_TIMEOUT = 30
POLL_INTERVAL = 0.1
OUTPUT_DIR = "output/results"
LOG_FILE = "native_host.log"
```

## Error Codes

Common error codes returned by tasks:

| Code | Description |
|-------|-------------|
| `INVALID_PLATFORM` | Unknown platform name |
| `EXECUTION_ERROR` | General execution failure |
| `TIMEOUT` | Operation timed out |
| `ELEMENT_NOT_FOUND` | Selector not found |
| `CONFIG_ERROR` | Invalid configuration |

## Progress Event Types

Events emitted by `ProgressTracker.emit()`:

| Event Type | Description |
|-------------|-------------|
| `task_start` | Task started execution |
| `task_complete` | Task completed successfully |
| `page_progress` | Pagination page change |
| `scroll_progress` | Infinite scroll progress |
| `depth_progress` | Depth traversal progress |
| `retry` | Retry attempt occurred |
