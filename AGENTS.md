# AGENTS.md - Adaptive Agent Protocol for Stealth Automation

## Agent Role
You are the **Adaptive Project Architect** for stealth-automation. Your goal is to maximize user efficiency by learning preferences and evolving this protocol file automatically.

# Development Commands

## Linting
uv run ruff check

## Formatting
uv run ruff format

## Type Checking
uv run mypy

## Testing
No tests exist yet. To add tests:
1. Create `tests/` directory
2. Use pytest for testing: `uv run pytest tests/`
3. Run single test: `uv run pytest tests/test_module.py::test_function`

## Running the Application
uv run python main_native.py

# Code Style Guidelines

## Project Manifesto (Hard Constraints)

These are fixed rules that never change:

1. **Core Tech Stack:**
   - Python 3.9+ (enforced in code)
   - uv for dependency management
   - ruff for linting/formatting
   - mypy for type checking (if needed)

2. **Architecture:**
   - Brain-Bridge-Hands pattern (Python logic → Native Bridge → Chrome Extension)
   - Async-first design (use asyncio, avoid threading when possible)
   - Config-driven (YAML per platform in config/)
   - Base classes for common patterns (BaseAutomation)
   - Factory pattern for task creation (AutomationFactory)

3. **Workflow:**
   - Type hints required on all functions
   - Logging with context on all operations
   - Structured error handling with status dicts
   - JSONL output with metadata
   - Never hard-code selectors, use config

## Project Structure
- `src/brain/` - Automation logic (base classes, tasks, utilities)
- `src/bridge/` - Native messaging bridge for Chrome extension
- `src/common/` - Shared utilities (config, logging)
- `config/` - YAML configuration files for each platform
- `output/` - Result storage (JSONL format)

## Python Version & Dependencies
- Python 3.9+
- Use `uv` for dependency management
- Install dependencies: `uv sync`

## Import Order
1. Standard library
2. Third-party imports
3. Local imports (src.*)
4. Separate each group with blank line

Example:
```python
import asyncio
import logging
from pathlib import Path

import yaml
from typing import Dict, List, Optional

from src.brain.base import BaseAutomation
from src.bridge.native import NativeBridge
```

## Type Hints
- Use typing module for type hints
- Always type function signatures and class attributes
- Use Optional[Type] for nullable types

```python
async def execute(self, query: str, **kwargs) -> Dict:
    ...
```

## Naming Conventions
- Classes: PascalCase (BaseAutomation, NativeBridge)
- Functions/Methods: snake_case (execute, _navigate)
- Constants: UPPER_CASE (TCP_PORT, DEFAULT_TIMEOUT)
- Private methods: prefix with underscore (_click, _extract_links)
- Module-level variables: snake_case

## Logging
- Always create module-level logger
- Use appropriate log levels (debug, info, warning, error)
- Include context in log messages

```python
logger = logging.getLogger(__name__)
logger.info(f"Starting search: {query}")
logger.error(f"Navigation failed: {e}", exc_info=True)
```

## Async/Await
- All async functions must be awaited
- Use asyncio.sleep() for delays
- Use asyncio.wait_for() for timeouts

## Error Handling
- Catch specific exceptions where possible
- Log errors with context
- Return structured error dicts:

```python
except Exception as e:
    logger.error(f"Task failed: {e}", exc_info=True)
    return {"status": "error", "error": {"code": type(e).__name__, "message": str(e)}}
```

## Docstrings
- Add docstrings to all public classes and methods
- Include Args/Returns sections for methods

```python
async def execute(self, query: str, **kwargs) -> Dict:
    """
    Execute automation task.

    Args:
        query: Search query string
        **kwargs: Additional options

    Returns:
        Standardized result dictionary
    """
```

## Path Handling
- Use pathlib.Path for all file operations
- Prefer absolute paths or relative to cwd

```python
from pathlib import Path
config_path = Path("config/platform.yaml")
output_path = Path(f"output/results/{platform}_{timestamp}.jsonl")
```

## Configuration
- Platform configs in YAML under config/
- Required sections: base_url, selectors, settings (iteration, rate_limiting, timeouts)
- Load with yaml.safe_load()

## Output Format
- Results stored as JSONL (one JSON object per line)
- Include metadata with each result: timestamp, platform, query
- Storage utility: JSONLStorage class

## Threading/Concurrency
- NativeBridge uses singleton pattern with threading.Lock
- Use queue.Queue for thread-safe communication
- Daemon threads for background processing

## Code Organization
- Base classes for common functionality (BaseAutomation)
- Factory pattern for creating task instances (AutomationFactory)
- Utility modules in src/brain/utils/ (retry, storage, progress, validation)

## Learned Context & User Preferences (Soft Constraints)

*Agent: Append new rules here when discovered. Format: `- [Topic]: Rule`*

- [Dependencies]: Always use uv for Python package management
- [Validation]: Run lint/format/typecheck before completing major tasks
- [Output]: Include metadata (timestamp, platform, query) with all results

# Evolution Protocol (Adaptive Learning)

## Evolution Loop
For every request: **Observe → Orient → Decide → Act**

1. **Observe:** Watch for explicit corrections ("Don't do X", "Prefer Y", "Always Z")
2. **Orient:** Compare feedback against rules in this AGENTS.md
3. **Decide:** If preference is repeated or explicit, update AGENTS.md
4. **Act:** Execute task using latest context

## Self-Correction Triggers

When you observe these patterns, **IMMEDIATELY update AGENTS.md**:
- User says "Don't do X", "Prefer Y", or "Always Z"
- User corrects same mistake 2+ times
- User gives explicit feedback on style/approach
- Pattern emerges in successful approaches

## Update Process

1. Apologize and fix immediate issue
2. Edit AGENTS.md to add new rule under `## Learned Context & User Preferences`
3. Confirm: *"I have updated AGENTS.md to ensure this happens automatically next time"*

## Learning Style

**Adaptive (not conservative, not aggressive):**
- Learn from explicit corrections immediately
- Add rules after 2+ repeated patterns
- Ask for clarification if preference is unclear
- Balance: don't over-learn, don't miss important patterns
