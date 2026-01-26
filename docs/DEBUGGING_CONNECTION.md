# Debugging Native Host Connection Issues

## Current Status Analysis

From the logs, I can see:

1. **Single Instance Working**: ✅
   - PID 9462 is already running
   - New instances are correctly rejected with "Instance already running" warnings
   - This is the expected behavior

2. **Connection Issue**: ❌
   - Extension is trying to connect but failing
   - Navigation timeout errors suggest the native host isn't responding to Chrome's connection attempts
   - TCP server (port 9999) works fine for trigger.py

## Root Cause

The issue is that **Chrome Native Messaging** is failing to connect to the existing native host instance, even though it's running. This suggests:

1. **Native Host Process Issue**: The existing instance (PID 9462) may have a broken stdin connection
2. **Chrome Extension Issue**: The extension may not be properly connecting to the existing instance
3. **Communication Protocol Issue**: The native messaging protocol may have issues

## Debugging Steps

### Step 1: Verify Native Host Health

```bash
# Check if the process is actually responsive
ps aux | grep 9462 | grep main_native.py

# Check if it's listening on stdin (should be)
lsof -p 9462 | grep main_native.py

# Test TCP server (should work)
telnet 127.0.0.1 9999
```

### Step 2: Test Native Messaging Directly

```bash
# Kill the existing instance and start fresh
pkill -f main_native.py
rm -f /tmp/stealth_automation.pid

# Start new instance
source .venv/bin/activate && python main_native.py

# In another terminal, test with Chrome extension
```

### Step 3: Check Extension Connection

```javascript
// In Chrome DevTools Console (on any page)
chrome.runtime.sendMessage({type: "HEALTH_CHECK"}, (response) => {
    console.log("Health:", response);
});
```

### Step 4: Monitor Connection Attempts

```bash
# Watch logs in real-time
tail -f native_host.log | grep -E "(connect|disconnect|message|command)"

# Look for these patterns:
# - "Connecting to native host"
# - "Native host disconnected"
# - "Received from Native"
# - "Sent command"
```

## Potential Issues

### Issue 1: Broken Stdin Connection

The existing instance may have a broken stdin connection from previous Chrome sessions.

**Fix**: Restart the native host completely.

### Issue 2: Chrome Extension ID Mismatch

The extension ID in the native host manifest may not match the actual extension ID.

**Fix**: Verify the extension ID and update the native host manifest.

### Issue 3: Native Host Process State

The process may be in a zombie state where it's running but not responding.

**Fix**: Kill and restart the process.

## Quick Fix

The simplest solution is to restart the native host completely:

```bash
# Kill all instances
pkill -f main_native.py

# Clean up PID file
rm -f /tmp/stealth_automation.pid

# Start fresh instance
source .venv/bin/activate && python main_native.py
```

## Expected Behavior After Fix

1. **Extension Auto-Connects**: Should connect automatically when Chrome starts
2. **No Instance Conflicts**: Only one instance should run
3. **Commands Work**: Both trigger.py and extension popup should work
4. **Keep-Alive Working**: Pings should be sent every 20 seconds

## If Issue Persists

If the problem continues after restart:

1. **Check Extension ID**: Verify the extension ID matches the native host manifest
2. **Check Permissions**: Ensure the extension has nativeMessaging permission
3. **Check Native Host Path**: Verify the path in the manifest is correct
4. **Check Chrome Logs**: Look for native messaging errors in Chrome's console

## Long-Term Solution

The current implementation should handle this automatically with:
- Service worker keep-alive
- Automatic reconnection
- Health monitoring
- Process lifecycle management

If issues persist, it may indicate a deeper problem with the Chrome Native Messaging setup.