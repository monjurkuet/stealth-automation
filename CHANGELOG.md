# Changelog

All notable changes to the Stealth Automation project.

## [1.2] - 2026-01-03

### Fixed
- **Service Worker Auto-Connection**: Extension now automatically connects to native host on Chrome startup
- **Service Worker Lifecycle Management**: Added proper activation events (`onStartup`, `onInstalled`, `onClicked`, `onUpdated`, `onCreated`)
- **Keep-Alive Mechanism**: Implemented 20-second ping interval to prevent service worker suspension
- **Connection Health Monitoring**: Added health check API and automatic connection validation
- **Exponential Backoff Retry**: Implemented robust reconnection logic with 5-attempt limit
- **Process Lifecycle Management**: Added single instance enforcement with PID file and signal handlers
- **Port Reuse**: Added `reuse_address=True` to prevent port conflicts
- **Enhanced Error Handling**: Improved connection error recovery and logging
- **Extension Health Check**: Added automatic health verification in popup before sending commands
- **Module Import Issues**: Fixed logging imports in task modules
- **Documentation**: Added comprehensive connection status and debugging guides

### Changed
- `extension/background.js` - Complete rewrite with service worker lifecycle management
- `extension/manifest.json` - Updated to v1.1, added `storage` permission, `type: "module"`
- `src/bridge/native.py` - Added connection health monitoring and signal handlers
- `main_native.py` - Added process management, PID file, signal handlers, port reuse
- `extension/popup.js` - Added automatic health check before commands
- `docs/EXTENSION_HEALTH.md` - New documentation for health check features

### Dependencies
- No new dependencies required

## [1.0] - 2026-01-03

### Added
- Multi-platform architecture using Factory Pattern
- Support for multiple iteration strategies (pagination, infinite_scroll, depth)
- YAML-based configuration system with JSON Schema validation
- JSONL (JSON Lines) output format with timestamped files
- Progress event tracking with real-time updates
- Retry logic with exponential backoff
- Configurable rate limiting with randomized delays
- Comprehensive documentation in `docs/` directory:
  - ARCHITECTURE.md - System architecture overview
  - SETUP.md - Installation and setup guide
  - CREATING_TASKS.md - Step-by-step task creation
  - CONFIGURATION.md - Configuration reference
  - API_REFERENCE.md - API documentation
  - PAGINATION_STRATEGIES.md - Iteration strategies guide
  - JSONL_FORMAT.md - JSONL format specification
  - MIGRATION.md - Migration from old architecture

### Changed
- `src/brain/main.py` - Now `Orchestrator` class with factory-based dispatch
- `main_native.py` - Updated to use `Orchestrator`, new message protocol
- `trigger.py` - Now supports platform parameter (`python trigger.py <platform> <query>`)
- `extension/popup.html` - Added platform dropdown selector
- `extension/popup.js` - Added platform handling
- `extension/content.js` - Added `scroll_to_bottom` and `progress_update` commands

### Deprecated
- Old `Logic` class (kept for backward compatibility)
- `search_results.json` fixed output file (use JSONL format now)

### Fixed
- Improved error handling with partial result recovery
- Better logging with structured format
- Type hints for better IDE support

### Dependencies
- Added `pyyaml>=6.0` - For YAML configuration
- Added `jsonschema>=4.20` - For config validation
- Existing `websockets>=15.0` - No changes

## [Previous] - Original Implementation

### Features
- Single DuckDuckGo search automation
- Chrome Native Messaging for undetectable automation
- Brain-Bridge-Hands architecture
- Basic pagination support
- Simple JSON output format (`search_results.json`)
