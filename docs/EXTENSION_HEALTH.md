# Extension Health Check

This document explains how to verify the Chrome extension's connection to the native host.

## Health Check Features

### 1. Automatic Health Check
The popup now performs an automatic health check before sending commands:
- Verifies native host connection status
- Shows error if not connected
- Prevents failed command attempts

### 2. Health Check API
You can manually check the extension's health:

```javascript
// In browser console
chrome.runtime.sendMessage({type: "HEALTH_CHECK"}, (response) => {
    console.log(response.health);
});
```

### 3. Health Check Response

```json
{
    "health": {
        "connected": true,
        "lastActivity": 1640995200000,
        "reconnectAttempts": 0,
        "state": {
            "isConnected": true,
            "lastActivity": 1640995200000,
            "reconnectScheduled": false
        }
    }
}
```

### 4. Status Indicators

**Connected:**
- ✅ Green status in popup
- Commands sent successfully
- Keep-alive pings working

**Disconnected:**
- ❌ Red status in popup
- Error message shown
- Automatic reconnection in progress

### 5. Troubleshooting

**If health check fails:**
1. Check if `main_native.py` is running
2. Look for connection errors in `native_host.log`
3. Try refreshing the extension
4. Verify native host configuration

**Common Issues:**
- Port 9999 conflicts
- Extension ID mismatch
- Native host process crashed

### 6. Keep-Alive Monitoring

The extension sends ping messages every 20 seconds to maintain the connection:
- Pings logged in `native_host.log`
- Failed pings trigger reconnection
- Service worker stays active

### 7. Reconnection Logic

Automatic reconnection with exponential backoff:
- Attempt 1: 1 second delay
- Attempt 2: 2 seconds delay
- Attempt 3: 4 seconds delay
- Attempt 4: 8 seconds delay
- Attempt 5: 16 seconds delay
- Max 5 attempts, then reset

### 8. Service Worker State

The extension tracks service worker state:
- Connection status
- Last activity timestamp
- Reconnection attempts
- Scheduled reconnections

### 9. Debug Information

Enable debug logging in `native_host.log`:
```bash
tail -f native_host.log | grep "Health\|State\|Reconnect"
```

### 10. Manual Testing

Test health check manually:
```bash
# 1. Start native host
python main_native.py

# 2. Open extension popup
# 3. Click any button (performs health check)

# 4. Check logs
tail -f native_host.log
```

## Implementation Details

### Service Worker Events
- `onStartup`: Connects when Chrome starts
- `onInstalled`: Connects when extension updates
- `onClicked`: Connects when icon clicked
- `onUpdated`: Connects when tabs update
- `onCreated`: Connects when windows created

### Keep-Alive Mechanism
- Sends ping every 20 seconds
- Handles pong responses
- Reconnects on ping failures

### Error Recovery
- Exponential backoff retry
- Connection health monitoring
- Graceful degradation
- State persistence

This health check system ensures reliable communication between the extension and native host.