# Pagination Strategies

## Overview

Stealth Automation supports three iteration strategies for collecting results:

1. **Pagination** - Traditional page-by-page navigation
2. **Infinite Scroll** - Continuous loading until end
3. **Depth Traversal** - Visit all linked pages (crawling)

## Strategy Comparison

| Feature | Pagination | Infinite Scroll | Depth Traversal |
|---------|-------------|-----------------|------------------|
| Best For | Search engines, e-commerce | Social media, feeds | Documentation, wikis |
| Complexity | Low | Low | High |
| URL Changes | Yes (navigation) | No (same page) | Yes (navigation) |
| Memory Usage | Low | Medium | High (queue) |
| Duplicate Risk | Low | Low | High (same domain) |
| Config Fields | `max_pages` | `scroll_delay_ms` | `max_depth`, `same_domain_only` |

## Pagination

### Description
Navigates through numbered pages (1, 2, 3...) until limit reached or no more pages.

### How It Works

```
Page 1 → Extract Results → Click "Next" → Page 2 → Extract Results → Click "Next" → ...
```

### Configuration

```yaml
settings:
  iteration:
    type: pagination
    max_pages: 5          # Max pages to visit
    max_items: 50         # Max items to collect
```

### When to Use

- Traditional search engines (Google, DuckDuckGo, Bing)
- E-commerce sites with numbered pages
- Listing sites with clear pagination
- Sites with stable page URLs

### Requirements

**Selectors:**
- `results_container`: Where results are located
- `next_page_button`: Button to go to next page

**Example:**
```yaml
selectors:
  results_container: "div.search-results"
  next_page_button: "a.pagination-next"
```

### Process Flow

1. Navigate to search results page
2. Wait for results container
3. Extract all result items
4. Save items to JSONL
5. Check if max items reached
6. Look for next page button
7. If found, click it and repeat
8. If not found, stop

### Advantages

- Clear progress tracking (page X of Y)
- Easy to pause/resume
- Low memory usage
- Simple error handling

### Limitations

- Requires consistent next button selector
- Can't handle dynamic page counts
- May miss items loaded via AJAX

## Infinite Scroll

### Description
Keeps scrolling to bottom until no new items appear or max items reached.

### How It Works

```
Initial Page → Scroll → Wait → Extract → Scroll → Wait → Extract → ... (No new items) → Stop
```

### Configuration

```yaml
settings:
  iteration:
    type: infinite_scroll
    max_items: 50         # Max items to collect
    scroll_delay_ms: 1000   # Delay between scrolls
```

### When to Use

- Social media feeds (Facebook, Twitter/X, Instagram)
- News sites with continuous loading
- Sites with "load more" buttons
- AJAX-driven content

### Requirements

**Selectors:**
- `results_container`: Where items appear

**Settings:**
- `scroll_delay_ms`: How long to wait for content to load

**Example:**
```yaml
selectors:
  results_container: "[role='feed']"
settings:
  iteration:
    scroll_delay_ms: 1500
```

### Process Flow

1. Navigate to content page
2. Extract initial items
3. Scroll to bottom
4. Wait for `scroll_delay_ms`
5. Extract items again
6. Compare counts:
   - Same count 3 times → Stop (no new content)
   - Different count → Continue
7. Repeat until max items

### Advantages

- Works on modern SPA sites
- No need for pagination selectors
- Captures dynamically loaded content

### Limitations

- Harder to track progress
- Higher memory usage
- May miss items if scroll too fast
- Duplicate items possible

### Tuning

**For fast sites:**
```yaml
scroll_delay_ms: 500
```

**For slow sites:**
```yaml
scroll_delay_ms: 2000
```

**To avoid duplicates:**
Items are deduped based on position in results array.

## Depth Traversal

### Description
Breadth-first traversal visiting all linked pages to specified depth.

### How It Works

```
Start URL → Extract Results → Find Links → Visit Link 1 → Extract → Find Links → ...
                  ↓
             Visit Link 2 → Extract → Find Links → ...
```

### Configuration

```yaml
settings:
  iteration:
    type: depth
    max_depth: 2            # How deep to follow links
    max_items: 30           # Max items to collect
    same_domain_only: true   # Only visit same domain
```

### When to Use

- Documentation sites
- Wikis and knowledge bases
- Article aggregation
- Site mapping

### Requirements

**Selectors:**
- `results_container`: Where content is located
- Any link selector (default `a[href]`)

**Settings:**
- `max_depth`: How many link levels deep
- `same_domain_only`: Restrict to same domain

**Example:**
```yaml
selectors:
  results_container: "article"
settings:
  iteration:
    max_depth: 3
    same_domain_only: true
```

### Process Flow

1. Start at base URL
2. Extract items from page
3. Extract all links from page
4. Add links to BFS queue
5. Visit next link from queue
6. Track depth (distance from start)
7. Stop when:
   - Max items reached
   - Max depth exceeded
   - Queue empty
   - URL already visited

### Advantages

- Comprehensive site crawling
- Discovers hidden content
- Good for site mapping

### Limitations

- Can get stuck in loops
- High memory usage (queue)
- Slower than pagination
- Many pages to navigate

### BFS vs DFS

Current implementation uses **BFS (Breadth-First Search)**:
- Visits all pages at depth 1, then depth 2, etc.
- Guarantees finding closest items first
- Better memory management

**DFS (Depth-First Search)** would:
- Follow one path to end before backtracking
- Risk of going too deep in one direction
- Lower memory, less predictable results

### Safety Features

**Visited Set:**
- Tracks all visited URLs
- Prevents infinite loops
- Dedupes pages

**Domain Restriction:**
- `same_domain_only: true` keeps crawling on target site
- Prevents wandering to external links
- Reduces scope

## Choosing the Right Strategy

### Decision Tree

```
Has numbered pages?
  ↓ Yes
  Use Pagination
  ↓ No
Uses infinite feed?
  ↓ Yes
  Use Infinite Scroll
  ↓ No
Need to follow links?
  ↓ Yes
  Use Depth Traversal
  ↓ No
  Use Pagination (default)
```

### Examples

**Search Engine (DuckDuckGo):**
```yaml
type: pagination
```

**Social Feed (Facebook):**
```yaml
type: infinite_scroll
```

**Documentation Site (MDN):**
```yaml
type: depth
max_depth: 2
```

**E-commerce (Amazon):**
```yaml
type: pagination
```

**News Site (CNN):**
```yaml
type: infinite_scroll
```

## Advanced Configuration

### Mixed Strategies

You can implement custom strategies by extending `BaseAutomation`:

```python
async def _iterate_custom(self, callback, max_items):
    # Your custom logic here
    pass
```

### Rate Limiting by Strategy

Different strategies may need different rate limits:

```yaml
# Pagination: lower rate (page changes)
rate_limiting:
  action_delay_ms: 500
  page_load_delay_ms: 2000

# Infinite Scroll: higher rate (no page changes)
rate_limiting:
  action_delay_ms: 100
  scroll_delay_ms: 1000
```

### Progress Tracking

Each strategy emits different progress events:

**Pagination:**
```jsonl
{"status": "progress", "data": {"event_type": "page_progress", "current_page": 1, "max_pages": 5}}
```

**Infinite Scroll:**
```jsonl
{"status": "progress", "data": {"event_type": "scroll_progress", "items_so_far": 25, "max_items": 50}}
```

**Depth Traversal:**
```jsonl
{"status": "progress", "data": {"event_type": "depth_progress", "current_depth": 1, "max_depth": 2, "pages_visited": 10}}
```

## Troubleshooting

### Pagination: No next page found

**Symptom:** Stops after first page

**Solutions:**
1. Verify `next_page_button` selector
2. Check if button exists in DOM
3. Increase wait time before looking for button
4. May need to click "Load more" instead

### Infinite Scroll: Not loading new items

**Symptom:** Scrolls but no new items

**Solutions:**
1. Increase `scroll_delay_ms`
2. Scroll in smaller increments
3. Use multiple scroll commands
4. Check if site requires user interaction

### Depth Traversal: Getting stuck

**Symptom:** Infinite crawling, never stops

**Solutions:**
1. Set `max_depth` lower
2. Enable `same_domain_only: true`
3. Add visited URL tracking (already built-in)
4. Set strict `max_items` limit

### All Strategies: Selectors changing

**Symptom:** Works initially, then fails

**Solutions:**
1. Sites may use dynamic classes
2. Use more robust selectors:
   - `data-` attributes
   - Role attributes
   - Parent + child combinations
3. Add multiple fallback selectors in code

## Performance Tips

### Pagination
- Set `page_load_delay_ms` high enough for full page load
- Lower `action_delay_ms` within same page

### Infinite Scroll
- Tune `scroll_delay_ms` for site speed
- Start low, increase if missing items

### Depth Traversal
- Keep `max_depth` low (2-3)
- Always use `same_domain_only: true`
- Set reasonable `max_items` limit

## Future Enhancements

Potential improvements to consider:

1. **Hybrid Strategies** - Combine pagination + infinite scroll
2. **Adaptive Delays** - Learn optimal delays per site
3. **Content Filtering** - Skip already-seen content
4. **Resume Support** - Continue from last page/item
5. **Priority Queues** - Weight certain URLs for depth traversal
