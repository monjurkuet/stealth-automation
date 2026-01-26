# Configuration Reference

## Overview

All platform-specific configuration is stored in YAML files in the `config/` directory. Each config is validated against the JSON schema in `config/schema.json`.

## Configuration Structure

```yaml
platform: <platform_name>
base_url: <starting_url>
selectors:
  search_input: <css_selector>
  search_button: <css_selector>
  results_container: <css_selector>
  result_item: <css_selector>
  result_title: <css_selector>
  result_link: <css_selector>
  result_snippet: <css_selector>
  next_page_button: <css_selector>
settings:
  iteration:
    type: <strategy_type>
    max_pages: <number>
    max_items: <number>
    max_depth: <number>
    scroll_delay_ms: <number>
    same_domain_only: <boolean>
    scroll_before_next_page: <boolean> # NEW
  rate_limiting:
    action_delay_ms: <number>
    page_load_delay_ms: <number>
    scroll_delay_ms: <number>
    randomize_delay: <boolean>
    max_actions_per_minute: <number>
  timeouts: # NEW SECTION
    browser_action_s: <number> # NEW
    task_execution_s: <number> # NEW
  output:
    file: <output_path>
auth:
  required: <boolean>
  login_url: <login_url>
```

## Required Fields

### platform
- Type: string
- Description: Unique identifier for the platform
- Example: `duckduckgo`, `google`, `facebook`

### selectors
- Type: object
- Required sub-fields:
  - `search_input`: CSS selector for search input field
  - `results_container`: CSS selector for results container

### settings
- Type: object
- Required sub-fields:
  - `iteration`: Iteration strategy configuration
  - `rate_limiting`: Rate limiting configuration
  - `output`: Output file configuration

## Optional Fields

### base_url
- Type: string
- Description: Starting URL for the platform
- Required for depth traversal

### selectors (optional)

| Field | Type | Description |
|--------|-------|-------------|
| `search_button` | string | CSS selector for submit button |
| `result_item` | string | CSS selector for individual result items |
| `result_title` | string | CSS selector for result title |
| `result_link` | string | CSS selector for result link |
| `result_snippet` | string | CSS selector for result snippet/description |
| `next_page_button` | string | CSS selector for next page button |

## Iteration Settings

### type
- Type: string
- Enum: `pagination`, `infinite_scroll`, `depth`
- Description: Strategy for collecting results

**Pagination:** Page 1, 2, 3... (traditional)
```yaml
iteration:
  type: pagination
  max_pages: 5
  max_items: 50
```

**Infinite Scroll:** Keep loading until end (social media, etc.)
```yaml
iteration:
  type: infinite_scroll
  max_items: 50
  scroll_delay_ms: 1000
```

**Depth Traversal:** Visit all linked pages (crawling)
```yaml
iteration:
  type: depth
  max_depth: 2
  same_domain_only: true
```

### max_items
- Type: integer (minimum: 1)
- Description: Maximum items to collect
- Default: 50

### max_pages (pagination only)
- Type: integer (minimum: 1)
- Description: Maximum pages to navigate
- Default: 5

### max_depth (depth only)
- Type: integer (minimum: 1)
- Description: Maximum depth to follow links
- Default: 2

### scroll_delay_ms (infinite_scroll only)
- Type: integer (minimum: 100)
- Description: Delay between scrolls in milliseconds
- Default: 1000

### scroll_before_next_page (pagination only)
- Type: boolean
- Description: If true, the page will scroll to the bottom before clicking the next page/load more button. Useful for dynamically loading content.
- Default: false

### same_domain_only (depth only)
- Type: boolean
- Description: Only follow links from same domain
- Default: true

## Rate Limiting Settings

### action_delay_ms
- Type: integer (minimum: 0)
- Description: Delay between type/click actions in milliseconds
- Default: 500

### page_load_delay_ms
- Type: integer (minimum: 0)
- Description: Delay after navigation in milliseconds
- Default: 2000

### scroll_delay_ms
- Type: integer (minimum: 0)
- Description: Delay between scroll actions in milliseconds
- Default: 1000

### randomize_delay
- Type: boolean
- Description: Add +/- 20% jitter to delays for human-like behavior
- Default: true

### max_actions_per_minute
- Type: integer (minimum: 1)
- Description: Maximum actions per minute (not enforced, for config reference)
- Default: 30

## Output Settings

### file
- Type: string
- Description: Output file path (JSONL format)
- Example: `output/results/duckduckgo_results.jsonl`

Note: Actual files will have timestamps appended:
- `duckduckgo_20260103_120000.jsonl`

## Timeout Settings

### browser_action_s
- Type: integer (minimum: 1)
- Description: Timeout in seconds for individual browser commands (e.g., click, type, navigate, wait for selector). Overrides NativeBridge's default 30s.
- Default: 30

### task_execution_s
- Type: integer (minimum: 1)
- Description: Overall timeout in seconds for the entire task execution in main_native.py.
- Default: 90

## Authentication Settings (Optional)

### required
- Type: boolean
- Description: Whether platform requires authentication
- Default: false

### login_url
- Type: string
- Description: URL for login page
- Required if `required: true`

## Complete Example

```yaml
platform: example_site
base_url: "https://example.com/"
selectors:
  search_input: "input[name='q']"
  search_button: "button[type='submit']"
  results_container: "div.search-results"
  result_item: "div.result"
  result_title: "h3.title"
  result_link: "a.result-link"
  result_snippet: "p.description"
  next_page_button: "a.pagination-next"
settings:
  iteration:
    type: pagination
    max_pages: 10
    max_items: 100
    scroll_before_next_page: true # ADDED
  rate_limiting:
    action_delay_ms: 800
    page_load_delay_ms: 3000
    scroll_delay_ms: 1500
    randomize_delay: true
    max_actions_per_minute: 20
  timeouts: # ADDED
    browser_action_s: 60
    task_execution_s: 180
  output:
    file: "output/results/example_site_results.jsonl"
auth:
  required: false
```

## CSS Selector Tips

### Basic Selectors
- By ID: `#element-id`
- By class: `.class-name`
- By attribute: `[attribute='value']`
- By tag: `tagname`

### Combining Selectors
- Descendant: `.parent .child`
- Direct child: `.parent > .child`
- Multiple classes: `.class1.class2`
- Attribute with class: `[role='button'].submit-btn`

### Finding Selectors

1. Open Chrome DevTools (F12)
2. Click element inspector (Ctrl+Shift+C)
3. Right-click element → Copy → Copy selector

### Testing Selectors

In Chrome DevTools console:
```javascript
document.querySelector('your-selector')
// Returns element if found, null otherwise
```

## Validation

Configs are validated against JSON schema on load. To manually validate:

```bash
python3 -c "
import yaml
import jsonschema

# Load config
with open('config/duckduckgo.yaml') as f:
    config = yaml.safe_load(f)

# Load schema
with open('config/schema.json') as f:
    schema = json.load(f)

# Validate
jsonschema.validate(config, schema)
print('Config is valid!')
"
```

## Troubleshooting

### Config not found
```
FileNotFoundError: Config not found: config/yourplatform.yaml
```
- Ensure config file exists in `config/` directory
- Check filename matches platform name exactly

### Validation error
```
ValidationError: 'selectors' is a required property
```
- Ensure all required fields are present
- Check against schema reference above

### Selector timeout
```
TimeoutError: Timeout waiting for results: div.results
```
- Selector may be incorrect
- Page may not have loaded (increase `page_load_delay_ms` or `browser_action_s` timeout)
- Dynamic content may require different approach
