# Creating New Automation Tasks

This guide walks you through creating a new automation task for a platform.

## Overview

Each automation task extends `BaseAutomation` and implements:
- `execute()` method - Main entry point
- Configuration YAML file
- Platform registration

## Step-by-Step Guide

### 1. Create Configuration File

Create `config/yourplatform.yaml`:

```yaml
platform: yourplatform
base_url: "https://yourplatform.com/"
selectors:
  search_input: "input[name='q']"
  search_button: "button[type='submit']"
  results_container: "div.results"
  result_item: "div.result-item"
  result_title: "h2.title"
  result_link: "a"
  result_snippet: "p.snippet"
  next_page_button: "a.next"
settings:
  iteration:
    type: pagination
    max_pages: 5
    max_items: 50
  rate_limiting:
    action_delay_ms: 500
    page_load_delay_ms: 2000
    randomize_delay: true
    max_actions_per_minute: 30
  output:
    file: "output/results/yourplatform_results.jsonl"
```

**Key Fields:**
- `platform`: Unique identifier (lowercase, no spaces)
- `base_url`: Starting URL
- `selectors`: CSS selectors for elements
- `settings`: Iteration and rate limiting

### 2. Create Task Class

Create `src/brain/tasks/yourplatform.py`:

```python
import asyncio
import logging
import time
from src.brain.base import BaseAutomation
from typing import Dict

logger = logging.getLogger(__name__)


class YourPlatformTask(BaseAutomation):
    """
    YourPlatform automation task.
    Add description here.
    """

    async def execute(self, query: str, **kwargs) -> Dict:
        """
        Execute YourPlatform automation.

        Args:
            query: Search query string
            **kwargs: Additional options (max_items, max_pages, etc.)

        Returns:
            Standardized result dictionary
        """
        start_time = time.time()

        try:
            logger.info(f"Starting YourPlatform search: {query}")
            await self.progress.emit('task_start', {'query': query})

            # 1. Navigate to platform
            url = self.config.get('base_url', 'https://yourplatform.com/')
            await self._navigate(url)

            # 2. Type search query
            search_input = self.config['selectors']['search_input']
            await self._type(search_input, query)

            # Wait for form submission
            await asyncio.sleep(2)

            # 3. Collect results using iteration strategy
            all_results = []

            def page_callback(items):
                all_results.extend(items)
                logger.debug(f"Collected {len(items)} items from page")

            await self.iterate_results(
                strategy='pagination',
                callback=page_callback,
                max_items=kwargs.get('max_items')
            )

            # 4. Save summary
            duration_ms = int((time.time() - start_time) * 1000)
            summary = {
                "query": query,
                "total_items": len(all_results),
                "pages_processed": self.pages_processed + 1,
                "duration_ms": duration_ms
            }
            await self.storage.append_summary(self.platform, summary)

            await self.progress.emit('task_complete', summary)

            return {
                "status": "success",
                "platform": self.platform,
                "action": "search",
                "data": {"results": all_results},
                "performance": {
                    "duration_ms": duration_ms,
                    "items_per_second": len(all_results) / (duration_ms / 1000) if duration_ms > 0 else 0
                }
            }

        except Exception as e:
            logger.error(f"YourPlatform search failed: {e}")
            await self.storage.append_error(self.platform, {
                "code": type(e).__name__,
                "message": str(e),
                "query": query
            })

            return {
                "status": "error",
                "platform": self.platform,
                "action": "search",
                "error": {
                    "code": type(e).__name__,
                    "message": str(e)
                }
            }
```

### 3. Register Task

Add to `src/brain/tasks/__init__.py`:

```python
from src.brain.base import BaseAutomation
from src.brain.tasks.duckduckgo import DuckDuckGoTask
from src.brain.tasks.yourplatform import YourPlatformTask  # Add import
from src.brain.factory import AutomationFactory

# Register task
AutomationFactory.register('yourplatform', YourPlatformTask)  # Add registration

__all__ = ['BaseAutomation', 'DuckDuckGoTask', 'YourPlatformTask', 'AutomationFactory']
```

### 4. Update Extension (Optional)

Add platform to popup dropdown in `extension/popup.html`:

```html
<select id="platform">
  <option value="duckduckgo">DuckDuckGo</option>
  <option value="yourplatform">Your Platform</option>
</select>
```

### 5. Test

```bash
# List platforms (should show your new platform)
python3 trigger.py list

# Test automation
python3 trigger.py yourplatform "test query"

# Check logs
tail -f native_host.log
```

## BaseAutomation Methods

### Required Methods

**`execute(query, **kwargs)`**
- Main entry point
- Must return standardized result dict

### Available Helper Methods

**Navigation & Interaction:**
- `await self._navigate(url)` - Navigate to URL
- `await self._type(selector, value)` - Type into element
- `await self._click(selector)` - Click element
- `await self._scroll_to_bottom()` - Scroll to bottom

**Extraction:**
- `await self._extract_current_page()` - Extract results from page
- `await self._extract_links()` - Extract links

**Waiting:**
- `await self._wait_for_results()` - Wait for results container

**Iteration:**
- `await self.iterate_results(strategy, callback, max_items)` - Run iteration

**Utilities:**
- `await self._with_retry(coro, retries, backoff_factor)` - Retry logic
- `await self._with_rate_limit()` - Apply rate limiting

**Content Script Commands**

If you need new content script commands, add them to `extension/content.js`:

```javascript
case 'your_custom_command':
    // Your logic here
    result = { id: command.id, status: 'success', data: ... };
    break;
```

Then call from Python:
```python
self.bridge.send_command({
    "action": "your_custom_command",
    ...
})
```

## Examples

### Simple Pagination Task

```python
async def execute(self, query: str, **kwargs) -> Dict:
    await self._navigate(self.config['base_url'])
    await self._type(self.config['selectors']['search_input'], query)
    
    results = []
    
    async def page_callback(items):
        results.extend(items)
    
    await self.iterate_results('pagination', page_callback)
    
    return {"status": "success", "data": results}
```

### Infinite Scroll Task

```python
async def execute(self, query: str, **kwargs) -> Dict:
    await self._navigate(f"{self.config['base_url']}?q={query}")
    
    results = []
    
    async def page_callback(items):
        results.extend(items)
    
    await self.iterate_results('infinite_scroll', page_callback)
    
    return {"status": "success", "data": results}
```

### Depth Traversal Task

```python
async def execute(self, query: str, **kwargs) -> Dict:
    await self._navigate(self.config['base_url'])
    
    results = []
    
    async def page_callback(items):
        results.extend(items)
    
    await self.iterate_results('depth', page_callback)
    
    return {"status": "success", "data": results}
```

## Best Practices

1. **Error Handling:** Wrap all operations in try/except
2. **Logging:** Use `logger` for debugging
3. **Progress:** Emit progress events for long operations
4. **Rate Limiting:** Use `_with_rate_limit()` between actions
5. **Validation:** Check results before processing
6. **Partial Results:** Save items as they're collected (iteration callback does this)

## Common Issues

**Selectors not found:**
- Use Chrome DevTools to find correct selectors
- Test selectors in console: `document.querySelector('selector')`

**Timeout errors:**
- Increase `page_load_delay_ms` in config
- Check if site requires login

**Rate limiting:**
- Increase delays in config
- Reduce `max_actions_per_minute`

## Testing Checklist

- [ ] Config file validates against schema
- [ ] Task appears in `python trigger.py list`
- [ ] Basic search works
- [ ] Iteration works (pagination/infinite/depth)
- [ ] Results saved to JSONL
- [ ] Progress events emitted
- [ ] Error handling works
- [ ] Logs show expected output
