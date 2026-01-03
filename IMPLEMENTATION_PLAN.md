# Stealth Automation - Multi-Platform Implementation Plan

## Overview
Refactor the stealth automation framework to support multiple platforms (Google, Facebook, etc.) using Strategy Pattern with plugin system.

---

## New Directory Structure

```
stealth-automation/
├── config/                          # Configuration files
│   ├── duckduckgo.yaml
│   ├── google.yaml
│   ├── facebook.yaml
│   └── schema.json
├── docs/                            # Documentation
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   ├── CREATING_TASKS.md
│   ├── CONFIGURATION.md
│   ├── API_REFERENCE.md
│   ├── PAGINATION_STRATEGIES.md
│   ├── JSONL_FORMAT.md
│   └── MIGRATION.md
├── extension/
│   ├── manifest.json
│   ├── background.js
│   ├── content.js
│   ├── popup.html
│   └── popup.js
├── src/
│   ├── brain/
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract base class
│   │   ├── factory.py              # Task factory
│   │   ├── main.py                 # Orchestrator
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   ├── duckduckgo.py
│   │   │   ├── google.py
│   │   │   └── facebook.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── retry.py
│   │       ├── storage.py          # JSONL storage
│   │       ├── progress.py         # Progress events
│   │       └── validation.py       # Config schema validation
│   ├── bridge/
│   │   ├── __init__.py
│   │   └── native.py
│   └── common/
│       ├── __init__.py
│       ├── config.py
│       └── logging_config.py
├── output/
│   └── results/
│       └── .gitkeep
├── main_native.py
├── trigger.py
└── requirements.txt
```

---

## Design Decisions

### 1. Task Registration
**Choice:** Explicit Factory Dict
- Pros: Explicit control, clear naming, type-safe
- Use `_tasks` registry dict in `AutomationFactory.register()`

### 2. Result Format
**Choice:** Standardized Structure
```python
{
    "status": "success" | "error",
    "platform": "duckduckgo",
    "action": "search",
    "data": { ... },
    "error": { ... },
    "performance": { "duration_ms": 1234, "retries": 0 }
}
```

### 3. Error Handling
**Choice:** Per-Task Retry Logic
- Platform-specific retry needs
- Fine-grained control with `_with_retry()` method

### 4. Configuration
**Choice:** External Config Files (YAML)
- Non-devs can update selectors
- Runtime configuration
- Schema validation with JSON schema

### 5. Pagination & Iteration
**Choice:** Multiple Strategies
- `pagination`: Traditional page 1, 2, 3...
- `infinite_scroll`: Keep loading until end
- `depth`: Visit all linked pages (same domain configurable)
- Configurable in YAML

### 6. Rate Limiting
**Choice:** Manual Control in Config
```yaml
rate_limiting:
  action_delay_ms: 500
  page_load_delay_ms: 2000
  scroll_delay_ms: 1000
  randomize_delay: true  # Add jitter
  max_actions_per_minute: 30
```

### 7. Storage
**Choice:** JSONL Format
```jsonl
{"status": "item", "platform": "duckduckgo", "timestamp": "...", "data": {...}}
{"status": "summary", "platform": "duckduckgo", "timestamp": "...", "data": {...}}
{"status": "error", "platform": "duckduckgo", "timestamp": "...", "error": {...}}
{"status": "progress", "platform": "duckduckgo", "timestamp": "...", "data": {...}}
```

---

## Implementation Phases

### Phase 1: Core Foundation Framework
1. Create `src/common/` infrastructure (config, logging)
2. Create `src/brain/base.py` with abstract class + iteration strategies
3. Create `src/brain/factory.py` with registration
4. Create `src/brain/utils/` modules (retry, storage, progress, validation)
5. Update `requirements.txt` (add pyyaml, jsonschema, python-json-logger)
6. Create `output/results/` directory

### Phase 2: Configuration System
7. Create `config/schema.json` for validation
8. Create `config/duckduckgo.yaml`
9. Create `config/google.yaml`
10. Create `config/facebook.yaml`

### Phase 3: Platform Tasks
11. Create `src/brain/tasks/duckduckgo.py` (refactored)
12. Create `src/brain/tasks/google.py`
13. Create `src/brain/tasks/facebook.py`
14. Create `src/brain/tasks/__init__.py` with registration

### Phase 4: Integration
15. Refactor `src/brain/main.py` to Orchestrator
16. Update `main_native.py`
17. Update `trigger.py`
18. Update `extension/popup.html`
19. Update `extension/popup.js`
20. Update `extension/content.js` (add new commands)

### Phase 5: Documentation
21. Write `docs/ARCHITECTURE.md`
22. Write `docs/SETUP.md`
23. Write `docs/CREATING_TASKS.md`
24. Write `docs/CONFIGURATION.md`
25. Write `docs/API_REFERENCE.md`
26. Write `docs/PAGINATION_STRATEGIES.md`
27. Write `docs/JSONL_FORMAT.md`
28. Write `docs/MIGRATION.md`
29. Update `README.md`

### Phase 6: Testing & Polish
30. Test DuckDuckGo task with pagination
31. Test Google task with pagination
32. Test Facebook task with infinite scroll
33. Test depth traversal strategy
34. Test rate limiting
35. Test JSONL output
36. Test progress events
37. Test backward compatibility
38. Create `CHANGELOG.md`

---

## Requirements

```txt
websockets>=15.0
pyyaml>=6.0
jsonschema>=4.20
python-json-logger>=2.0
```

---

## Backward Compatibility

- Old protocol (no platform) → defaults to duckduckgo
- Old `Logic` class → deprecated but kept
- Old `trigger.py` format → auto-detect
- Old popup → handles missing platform field
