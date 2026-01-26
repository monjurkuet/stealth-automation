# Migration Guide

## Overview

This guide helps you migrate from the old single-platform architecture to the new multi-platform system.

## What Changed

### Old Architecture (Single Platform)

```
main_native.py → Logic class → DuckDuckGo (hardcoded)
```

**Key Files:**
- `src/brain/main.py`: Single `Logic` class
- `search_results.json`: Fixed output file
- Hardcoded DuckDuckGo selectors

### New Architecture (Multi-Platform)

```
main_native.py → Orchestrator → AutomationFactory → DuckDuckGoTask (configurable)
                                                    → GoogleTask (future)
                                                    → FacebookTask (future)
```

**Key Files:**
- `src/brain/main.py`: `Orchestrator` + `Logic` (deprecated)
- `config/*.yaml`: Platform-specific configs
- `output/results/*.jsonl`: Timestamped JSONL files
- `src/brain/tasks/*.py`: One task per platform

## Migration Checklist

### Step 1: Update Dependencies

```bash
# Install new dependencies
source .venv/bin/activate
uv pip install -r requirements.txt
```

New dependencies:
- `pyyaml` - Configuration files
- `jsonschema` - Config validation

### Step 2: Reload Extension

1. Go to `chrome://extensions/`
2. Click refresh button on Stealth Automation
3. Old extension is now updated

### Step 3: Update Native Host

No changes needed if already configured.

### Step 4: Update CLI Usage

**Old format:**
```bash
python trigger.py "search query"
```

**New format:**
```bash
python trigger.py duckduckgo "search query"
```

**Backward compatibility:** Old format still works (defaults to DuckDuckGo).

### Step 5: Update Output File Location

**Old:**
```bash
cat search_results.json
```

**New:**
```bash
ls output/results/
cat output/results/duckduckgo_20260103_120000.jsonl
```

### Step 6: Update Code (if using Python API)

**Old way:**
```python
from src.brain.main import Logic
from src.bridge.native import NativeBridge

bridge = NativeBridge()
logic = Logic(bridge)
await logic.search_duckduckgo("query")
```

**New way:**
```python
from src.brain.main import Orchestrator
from src.bridge.native import NativeBridge

bridge = NativeBridge()
orchestrator = Orchestrator(bridge)
result = await orchestrator.dispatch({
    "action": "start_task",
    "platform": "duckduckgo",
    "query": "query"
})
```

**Deprecated but still works:** Old `Logic` class kept for compatibility.

## Backward Compatibility

### What Still Works

1. **Old trigger.py format:**
   ```bash
   python trigger.py "search query"  # Still defaults to duckduckgo
   ```

2. **Old Logic class:**
   ```python
   logic = Logic(bridge)
   await logic.search_duckduckgo("query")
   ```

3. **Old output format:**
   - `search_results.json` kept for reference
   - New format is JSONL in `output/results/`

### What Changed

1. **Extension popup** - Now has platform dropdown
2. **Output location** - `output/results/` instead of root
3. **Result format** - JSONL instead of JSON array
4. **Configuration** - YAML file instead of hardcoded

## Code Migration Examples

### Example 1: Simple Search

**Old Code:**
```python
from src.brain.main import Logic
from src.bridge.native import NativeBridge

bridge = NativeBridge()
logic = Logic(bridge)
results = await logic.search_duckduckgo("python automation")
```

**New Code:**
```python
from src.brain.main import Orchestrator
from src.bridge.native import NativeBridge

bridge = NativeBridge()
orchestrator = Orchestrator(bridge)
result = await orchestrator.dispatch({
    "action": "start_task",
    "platform": "duckduckgo",
    "query": "python automation"
})
results = result['data']['results']
```

### Example 2: Reading Results

**Old Code:**
```python
import json

with open('search_results.json', 'r') as f:
    results = json.load(f)
    for item in results:
        print(item['title'])
```

**New Code:**
```python
import json

# Find latest file
import glob
files = glob.glob('output/results/duckduckgo_*.jsonl')
latest = max(files, key=os.path.getctime)

with open(latest, 'r') as f:
    for line in f:
        entry = json.loads(line)
        if entry['status'] == 'item':
            print(entry['data']['title'])
```

### Example 3: Custom Task

**Old way:** Modify `src/brain/main.py` directly

**New way:** Create new task file:

```python
# src/brain/tasks/mytask.py
from src.brain.base import BaseAutomation

class MyTask(BaseAutomation):
    async def execute(self, query: str, **kwargs) -> Dict:
        # Your implementation
        pass

# src/brain/tasks/__init__.py
from src.brain.tasks.mytask import MyTask
from src.brain.factory import AutomationFactory

AutomationFactory.register('mytask', MyTask)
```

## Configuration Migration

### Old Hardcoded Selectors

In `src/brain/main.py`:
```python
search_selector = "input#searchbox_input"
```

### New YAML Config

In `config/duckduckgo.yaml`:
```yaml
selectors:
  search_input: "input#searchbox_input"
```

### Benefits of New Approach

1. **No code changes needed** - Update selector in YAML
2. **Version control** - Track config changes separately
3. **Multiple environments** - Different configs for dev/prod
4. **Non-technical users** - Can update selectors

## Data Migration

### Converting Old JSON to New JSONL

If you have old `search_results.json` files:

```python
import json
from datetime import datetime, timezone

# Read old JSON
with open('search_results.json', 'r') as f:
    old_results = json.load(f)

# Write new JSONL
timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
output_file = f"output/results/duckduckgo_{timestamp}.jsonl"

with open(output_file, 'w') as f:
    for item in old_results:
        entry = {
            "status": "item",
            "platform": "duckduckgo",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": item
        }
        f.write(json.dumps(entry) + '\n')

print(f"Converted {len(old_results)} items to {output_file}")
```

## Testing Migration

### Test 1: Basic Functionality

```bash
# Start native host
python main_native.py

# In another terminal
python trigger.py duckduckgo "test query"

# Check output
cat output/results/duckduckgo_*.jsonl
```

### Test 2: Backward Compatibility

```bash
# Old format should still work
python trigger.py "test query"
```

### Test 3: Extension

1. Open Chrome
2. Click extension popup
3. Verify platform dropdown shows "DuckDuckGo"
4. Run a search

### Test 4: New Features

```bash
# List platforms
python trigger.py list
```

## Rollback Plan

If issues arise:

### Option 1: Git Revert

```bash
git checkout old-implementation-branch
```

### Option 2: Keep Both

Keep old `src/brain/main.py` backup:
```bash
cp src/brain/main.py src/brain/main.py.backup
```

### Option 3: Use Old Interface

New code still supports old `Logic` class for compatibility.

## Common Issues

### Issue: Config Not Found

**Error:**
```
FileNotFoundError: Config not found: config/duckduckgo.yaml
```

**Solution:**
```bash
# Create config directory
mkdir -p config

# Copy example config or create new one
```

### Issue: Unknown Platform

**Error:**
```
ValueError: Unknown platform: 'DuckDuckGo'
```

**Solution:**
```bash
# Use lowercase
python trigger.py duckduckgo "query"  # Good
python trigger.py DuckDuckGo "query"  # Bad
```

### Issue: Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'yaml'
```

**Solution:**
```bash
# Activate venv and install
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Issue: JSONL Files Not Created

**Error:** No files in `output/results/`

**Solution:**
```bash
# Create directory
mkdir -p output/results

# Check permissions
chmod 755 output/results
```

## Next Steps

After migration:

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) for system overview
2. Read [CONFIGURATION.md](CONFIGURATION.md) for YAML config options
3. Consider adding new platforms (see [CREATING_TASKS.md](CREATING_TASKS.md))

## Support

If you encounter issues during migration:

1. Check logs: `tail -f native_host.log`
2. Review docs in `docs/` directory
3. Compare with example files
4. Open GitHub issue with details
