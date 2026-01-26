# JSONL Format

## Overview

Stealth Automation uses **JSONL** (JSON Lines) format for storing results. JSONL is an append-only format where each line is a valid JSON object.

## Format Specification

### Line Structure

Each line in a JSONL file is a JSON object:
```
{"field1": "value1", "field2": "value2"}
{"field1": "value3", "field2": "value4"}
```

### Key Characteristics

- **One JSON object per line**
- **Newline-delimited** (no commas between lines)
- **Append-only** (new data added to end)
- **Streaming-friendly** (can read line by line)
- **Partial recovery** (if task fails, collected items are saved)

## Entry Types

There are four entry types in the JSONL format:

### 1. Item Entry

Represents a single collected item (search result, post, etc.).

```jsonl
{"status": "item", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:00Z", "data": {"rank": 1, "title": "Example Title", "link": "https://example.com", "details": "..."}}
```

**Fields:**
- `status`: Always `"item"`
- `platform`: Platform name
- `timestamp`: ISO 8601 timestamp (UTC)
- `data`: Platform-specific result data

### 2. Summary Entry

Represents task completion summary.

```jsonl
{"status": "summary", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:05Z", "data": {"query": "test", "total_items": 10, "duration_ms": 5000}}
```

**Fields:**
- `status`: Always `"summary"`
- `platform`: Platform name
- `timestamp`: ISO 8601 timestamp (UTC)
- `data`: Summary statistics

### 3. Error Entry

Represents an error that occurred.

```jsonl
{"status": "error", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:06Z", "error": {"code": "TIMEOUT", "message": "Element not found", "query": "test"}}
```

**Fields:**
- `status`: Always `"error"`
- `platform`: Platform name
- `timestamp`: ISO 8601 timestamp (UTC)
- `error`: Error details

### 4. Progress Entry

Represents a progress event during execution.

```jsonl
{"status": "progress", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:01Z", "data": {"event_type": "page_progress", "current_page": 1, "max_pages": 5}}
```

**Fields:**
- `status`: Always `"progress"`
- `platform`: Platform name
- `timestamp`: ISO 8601 timestamp (UTC)
- `data`: Progress event data

## Example File

Here's a complete example of a DuckDuckGo search JSONL file:

```jsonl
{"status": "progress", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:00Z", "data": {"event_type": "task_start", "query": "python automation", "elapsed_seconds": 0}}
{"status": "progress", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:01Z", "data": {"event_type": "page_progress", "current_page": 1, "max_pages": 5, "items_so_far": 0, "elapsed_seconds": 1}}
{"status": "item", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:02Z", "data": {"rank": 1, "title": "Selenium - Web Browser Automation", "link": "https://www.selenium.dev/", "details": "Selenium automates browsers."}}
{"status": "item", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:02Z", "data": {"rank": 2, "title": "Puppeteer - Node.js library", "link": "https://pptr.dev/", "details": "Puppeteer provides a high-level API to control Chrome."}}
{"status": "progress", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:03Z", "data": {"event_type": "page_progress", "current_page": 2, "max_pages": 5, "items_so_far": 20, "elapsed_seconds": 3}}
{"status": "item", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:04Z", "data": {"rank": 21, "title": "Playwright for Python", "link": "https://playwright.dev/python/", "details": "Playwright enables reliable end-to-end testing."}}
{"status": "summary", "platform": "duckduckgo", "timestamp": "2026-01-03T12:00:05Z", "data": {"query": "python automation", "total_items": 50, "pages_processed": 5, "duration_ms": 5000}}
```

## File Naming Convention

JSONL files are named with timestamps:

```
{platform}_{timestamp}.jsonl
```

Examples:
- `duckduckgo_20260103_120000.jsonl`
- `facebook_20260103_153045.jsonl`
- `google_20260103_180000.jsonl`

Timestamp format: `YYYYMMDD_HHMMSS` (UTC)

## Location

All JSONL files are stored in:

```
output/results/
```

## Reading JSONL Files

### Command Line

```bash
# View entire file
cat output/results/duckduckgo_20260103_120000.jsonl

# View specific entry types
grep '"status": "item"' output/results/*.jsonl

# Count items
grep -c '"status": "item"' output/results/*.jsonl

# View only data fields
jq -r '.data' output/results/*.jsonl
```

### Python

```python
import json

with open('output/results/duckduckgo_20260103_120000.jsonl', 'r') as f:
    for line in f:
        entry = json.loads(line)
        if entry['status'] == 'item':
            print(entry['data'])
```

### jq (JSON processor)

```bash
# Extract all items
jq 'select(.status == "item") | .data' output/results/*.jsonl

# Get summary
jq 'select(.status == "summary") | .data' output/results/*.jsonl

# Count by status
jq -r '.status' output/results/*.jsonl | sort | uniq -c
```

## Writing to JSONL

The `JSONLStorage` class handles all writing:

```python
from src.brain.utils.storage import JSONLStorage

storage = JSONLStorage("output/results/test.jsonl")

# Append an item
await storage.append_item("duckduckgo", {"title": "Test", "link": "..."})

# Append a summary
await storage.append_summary("duckduckgo", {"total_items": 10})

# Append an error
await storage.append_error("duckduckgo", {"code": "TIMEOUT"})
```

## Benefits of JSONL

### 1. Append-Only
- Never need to read/rewrite entire file
- Safe for concurrent writes
- Natural for streaming collection

### 2. Partial Recovery
If a task fails after collecting 90% of items:
- All 90% are already saved
- Can resume or analyze partial results
- No data loss

### 3. Streaming-Friendly
- Process line by line
- Low memory footprint
- Can pipe to other tools:
  ```bash
  cat results.jsonl | jq '.data' | gzip > processed.json.gz
  ```

### 4. Human Readable
- Still valid JSON per line
- Easy to inspect with `cat`, `less`
- No need for special viewers

### 5. Version Control Friendly
- Each run produces new file (timestamped)
- Easy to track changes
- Git diff works per line

## Comparison with Other Formats

| Feature | JSONL | JSON Array | CSV |
|---------|--------|------------|------|
| Append-only | ✅ | ❌ | ✅ |
| Partial recovery | ✅ | ❌ | ✅ |
| Streaming | ✅ | ⚠️ | ✅ |
| Human readable | ✅ | ⚠️ | ✅ |
| Structured | ✅ | ✅ | ❌ |
| Schema validation | ✅ | ✅ | ❌ |
| File size | Smaller | Larger | Smallest |

## Schema Validation

Each line follows a JSON schema:

### Common Fields (all entries)
```json
{
  "status": "item" | "summary" | "error" | "progress",
  "platform": "string",
  "timestamp": "ISO 8601 string"
}
```

### Item Entry Schema
```json
{
  "status": "item",
  "platform": "string",
  "timestamp": "string",
  "data": {
    // Platform-specific
    "rank": "number",
    "title": "string",
    "link": "string",
    "details": "string"
  }
}
```

### Summary Entry Schema
```json
{
  "status": "summary",
  "platform": "string",
  "timestamp": "string",
  "data": {
    "query": "string",
    "total_items": "number",
    "duration_ms": "number",
    "pages_processed": "number"
  }
}
```

### Error Entry Schema
```json
{
  "status": "error",
  "platform": "string",
  "timestamp": "string",
  "error": {
    "code": "string",
    "message": "string",
    // Optional context
    "query": "string"
  }
}
```

### Progress Entry Schema
```json
{
  "status": "progress",
  "platform": "string",
  "timestamp": "string",
  "data": {
    "event_type": "string",
    // Event-specific fields
    "current_page": "number",
    "items_so_far": "number"
  }
}
```

## File Size Management

JSONL files can grow large. Strategies:

### 1. Per-Run Files
- Current approach: timestamped files
- Easy to archive/delete old runs
- No merging needed

### 2. Compress Old Files
```bash
# Compress files older than 7 days
find output/results/ -name "*.jsonl" -mtime +7 -exec gzip {} \;
```

### 3. Rotate Files
```bash
# Keep only last 10 files per platform
ls -t output/results/duckduckgo_*.jsonl | tail -n +11 | xargs rm
```

## Importing JSONL

### To Python DataFrame (pandas)

```python
import pandas as pd
import json

records = []
with open('output/results/duckduckgo_20260103_120000.jsonl', 'r') as f:
    for line in f:
        entry = json.loads(line)
        if entry['status'] == 'item':
            records.append(entry['data'])

df = pd.DataFrame(records)
print(df.head())
```

### To Database (SQLite)

```python
import sqlite3
import json

conn = sqlite3.connect('results.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS results (
        platform TEXT,
        title TEXT,
        link TEXT,
        timestamp TEXT
    )
''')

with open('output/results/duckduckgo_20260103_120000.jsonl', 'r') as f:
    for line in f:
        entry = json.loads(line)
        if entry['status'] == 'item':
            cursor.execute('''
                INSERT INTO results (platform, title, link, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (
                entry['platform'],
                entry['data'].get('title'),
                entry['data'].get('link'),
                entry['timestamp']
            ))

conn.commit()
```

## Best Practices

### 1. Always Use JSONLStorage
```python
# Good
await storage.append_item(platform, data)

# Bad (no error handling, no append guarantee)
with open('results.jsonl', 'a') as f:
    f.write(json.dumps(data) + '\n')
```

### 2. Validate Before Writing
```python
# Ensure data is serializable
try:
    json.dumps(data)
except TypeError as e:
    logger.error(f"Data not JSON serializable: {e}")
    return
```

### 3. Check File Size Periodically
```python
import os

file_size = os.path.getpathsize(storage.get_filepath())
if file_size > 100_000_000:  # 100MB
    logger.warning(f"Large file: {file_size / 1_000_000:.1f}MB")
```

### 4. Use ISO 8601 Timestamps
```python
# Good
datetime.now(timezone.utc).isoformat()

# Bad (ambiguous)
datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

## Troubleshooting

### File Not Created

**Symptom:** No JSONL file after task

**Check:**
1. `output/results/` directory exists
2. Write permissions
3. Check `native_host.log` for errors

### Empty File

**Symptom:** File created but no entries

**Check:**
1. Did task run to completion?
2. Were items found on page?
3. Check error entries in file

### Malformed JSON

**Symptom:** Can't read line

**Check:**
```bash
# Validate JSONL
python3 -c "
import json, sys
for line in sys.stdin:
    json.loads(line)
" < output/results/test.jsonl
"
```

### Duplicate Entries

**Symptom:** Same item appears multiple times

**Cause:** Task retried and appended twice

**Solution:** Check logs, disable duplicate appends in code
