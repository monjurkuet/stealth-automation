# Stealth Automation - Architecture

## Overview

Stealth Automation is a browser automation framework using Chrome Native Messaging for communication between Python logic and Chrome browser actions. It follows a **Brain-Bridge-Hands** architecture pattern.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                         │
│  ┌──────────────┐         ┌──────────────┐                │
│  │  Extension   │         │  CLI Trigger │                │
│  │    Popup     │         │   trigger.py │                │
│  └──────┬───────┘         └──────┬───────┘                │
└─────────┼──────────────────────────┼─────────────────────────┘
          │                          │
          ▼                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     main_native.py                              │
│              (Native Host Entry Point)                          │
│  - TCP Server for external triggers                           │
│  - Message routing & Configurable Task Timeouts                                           │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Orchestrator                                │
│            (src/brain/main.py)                              │
│  - Dispatches tasks to platforms                             │
│  - Manages task lifecycle                                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                 AutomationFactory                             │
│              (src/brain/factory.py)                          │
│  - Task registration                                         │
│  - Task instance creation                                   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│               BaseAutomation (Abstract)                          │
│               (src/brain/base.py)                             │
│  - Common iteration strategies                                │
│  - Retry logic                                              │
│  - Rate limiting                                            │
│  - Progress tracking                                         │
│  - JSONL storage                                           │
└──────────────────────┬──────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ DuckDuckGo   │ │    Google    │ │   Facebook   │
│    Task      │ │    Task      │ │    Task      │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   NativeBridge                                │
│              (src/bridge/native.py)                           │
│  - Binary stdin/stdout communication                         │
│  - Command/Result pattern                                   │
│  - Threading for I/O                                       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        Native Messaging (Binary JSON)
                       │
┌──────────────────────┴──────────────────────────────────────────┐
│                Chrome Extension                                │
│  ┌─────────────┐          ┌─────────────┐                │
│  │  Background │◄────────►│  Content    │                │
│  │  Script     │  Router  │   Script    │                │
│  │             │          │   (Hands)   │                │
│  └─────────────┘          └─────────────┘                │
└─────────────────────────────────────────────────────────────────┘

## Components

### 1. Brain (Python Logic)

**Entry Point:** `main_native.py`

**Orchestrator:** `src/brain/main.py`
- Receives messages with platform + query
- Uses factory to create task instances
- Executes tasks and returns results
- Handles errors and partial results

**Task Factory:** `src/brain/factory.py`
- Explicit task registration
- Creates task instances
- Lists available platforms and their detailed configuration, including 'task_execution_s'.

**Base Automation:** `src/brain/base.py`
- Abstract base class for all tasks
- Common iteration strategies (pagination now supports pre-click scroll for 'load more')
- Retry logic with exponential backoff
- Rate limiting with configurable delays
- Progress event emission
- JSONL result storage
- Browser action timeouts are configurable via task settings ('browser_action_s')

**Platform Tasks:** `src/brain/tasks/*.py`
- `DuckDuckGoTask`: DuckDuckGo search automation
- More platforms can be added by extending `BaseAutomation`

### 2. Bridge (Communication)

**NativeBridge:** `src/bridge/native.py`
- Manages stdin/stdout communication with Chrome
- Implements command/result pattern with IDs
- Threading for non-blocking I/O
- Queue-based message handling

### 3. Hands (Browser Extension)

**Background Script:** `extension/background.js`
- Service worker router
- Connects to Python Native Host
- Routes messages between Python and Content Scripts

**Content Script:** `extension/content.js`
- Executes DOM manipulations
- Handles commands: navigate, type, click, wait, scroll (now fully implemented), extract
- Shows status overlay for visual feedback

**Popup:** `extension/popup.html/js`
- UI for triggering automation
- Platform selector
- Query input

### 4. Utilities

**Storage:** `src/brain/utils/storage.py`
- JSONL (JSON Lines) file storage
- Append-only format for streaming
- Partial result recovery

**Progress:** `src/brain/utils/progress.py`
- Event emission for task progress
- Real-time updates to bridge

**Retry:** `src/brain/utils/retry.py`
- Exponential backoff retry
- Configurable attempts

**Validation:** `src/brain/utils/validation.py`
- JSON schema validation for configs
- Early error detection

### 5. Configuration

**Platform Configs:** `config/*.yaml`
- YAML files per platform defining:
  - CSS selectors
  - Iteration settings (e.g., pagination type, max pages/items, scroll-before-next-page)
  - Rate limiting settings (e.g., delays, randomization)
  - Timeout settings (e.g., browser_action_s for individual commands, task_execution_s for overall task)

**Schema:** `config/schema.json`
- JSON Schema for validation
- Ensures config correctness

## Data Flow

### Task Execution Flow

1. **User triggers** via popup or CLI
   ```
   Platform: "duckduckgo"
   Query: "python automation"
   ```

2. **Orchestrator** receives message
   ```
   message = {
     "action": "start_task",
     "platform": "duckduckgo",
     "query": "python automation"
   }
   ```

3. **Factory** creates task instance
   ```python
   task = AutomationFactory.create("duckduckgo", bridge)
   ```

4. **Task** loads config and initializes
   - Loads `config/duckduckgo.yaml`
   - Creates JSONL storage with timestamp
   - Initializes progress tracker

5. **Task** executes automation
   - Navigate to URL
   - Type search query
   - Extract results using iteration strategy

6. **Results** saved to JSONL
   ```jsonl
   {"status": "item", "platform": "duckduckgo", "timestamp": "...", "data": {...}}
   {"status": "summary", "platform": "duckduckgo", "timestamp": "...", "data": {...}}
   ```

7. **Progress** events emitted
   - Task start, page progress, task complete
   - Sent to bridge for real-time updates

8. **Result** returned to caller
   ```python
   {
     "status": "success",
     "platform": "duckduckgo",
     "action": "search",
     "data": {"results": [...]},
     "performance": {"duration_ms": 5000}
   }
   ```

### Command Flow (Native Messaging)

1. **Python → Bridge → Chrome:**
   ```python
   bridge.send_command({
     "id": 1,
     "action": "navigate",
     "url": "https://duckduckgo.com/"
   })
   ```

2. **Chrome → Bridge → Python:**
   ```python
   result = bridge.get_result(1)
   # Returns: {"id": 1, "status": "success"}
   ```

## Design Patterns

1. **Strategy Pattern:** Different iteration strategies
2. **Factory Pattern:** Task creation and registration
3. **Singleton:** NativeBridge instance
4. **Template Method:** BaseAutomation with hooks
5. **Observer:** Progress event emission

## Key Features

- **Undetectable:** Uses Chrome Native Messaging
- **Configurable:** YAML-based configuration
- **Extensible:** Easy to add new platforms
- **Resilient:** Retry logic and error handling
- **Observable:** Progress events
- **Partial Recovery:** JSONL append-only storage
