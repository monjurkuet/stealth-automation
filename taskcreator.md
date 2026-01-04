# Guide to Creating New Automation Tasks

This document outlines the process for creating new automation tasks within the system. Tasks are designed to extend the `BaseAutomation` class, enabling interaction with web platforms through a standardized `bridge` interface and configurable settings.

## Core Components of a New Task

To create a new task, you will typically need to define three core components:

1.  **Task Python Class:**
    *   **Location:** New task Python files should be placed in `src/brain/tasks/`.
    *   **Inheritance:** Your task class **must** inherit from `src.brain.base.BaseAutomation`. This provides access to the `bridge` for browser interactions, `config` for settings, and various utility methods.
    *   **Required Method (`execute`):**
        ```python
        async def execute(self, query: str, **kwargs) -> Dict:
            """
            Main entry point for your automation task.
            Implement the specific logic for interacting with the target web platform here.
            """
            # Example: navigate, type, click, extract data using self.bridge methods
            await self._navigate(self.config['base_url'])
            # ... your task-specific logic ...
            return {"status": "success", "data": "extracted_info"}
        ```
        This `execute` method is the primary entry point for your task. It will receive a `query` string and optional `kwargs`. Within this method, you will use the methods provided by `BaseAutomation` (which in turn use `self.bridge`) to perform web interactions.

2.  **YAML Configuration File:**
    *   **Location:** Configuration files are stored in the `config/` directory.
    *   **Naming Convention:** The filename **must** be `config/<platform_name>.yaml`, where `<platform_name>` is the unique identifier for your task (e.g., `duckduckgo.yaml`).
    *   **Structure:**
        ```yaml
        platform: <platform_name>
        base_url: "https://example.com/"
        selectors:
          # CSS selectors for elements on the target website
          # e.g., search_input: "input#search-box"
          # e.g., results_container: "div.results"
          # Define all selectors needed for navigation, input, and data extraction
          your_element_1: "selector_for_element_1"
          your_element_2: "selector_for_element_2"
        settings:
          iteration:
            # Defines how to iterate through results (pagination, infinite_scroll, depth)
            type: pagination # or infinite_scroll, depth
            max_pages: 5    # Max pages for pagination/depth
            max_items: 50   # Max items to collect
            scroll_before_next_page: true  # Scroll to bottom before clicking next page (useful for "load more" buttons)
          rate_limiting:
            # Controls delays and limits to prevent overwhelming the target site
            action_delay_ms: 500      # Delay before/after actions
            page_load_delay_ms: 2000  # Delay after page navigation
            scroll_delay_ms: 1000     # Delay after scrolling for infinite scroll
            randomize_delay: true     # Add randomness to delays
            max_actions_per_minute: 30 # Max actions per minute
          output:
            file: "output/results/<platform_name>_results.jsonl"  # Output file path
        timeouts:
          browser_action_s: 30  # Timeout for individual browser operations (e.g., click, type)
          task_execution_s: 300  # Overall timeout for the entire task
        ```
        This file provides all the necessary platform-specific settings, particularly CSS selectors for interacting with the web page, and various operational parameters like iteration strategies and rate limits.

3.  **Task Registration:**
    *   **Location:** The registration happens in `src/brain/tasks/__init__.py`.
    *   **Action:**
        1.  Import your new task class:
            ```python
            from src.brain.tasks.your_new_task_module import YourNewTaskClass
            ```
        2.  Register it with the `AutomationFactory`:
            ```python
            AutomationFactory.register("your_new_task_platform_name", YourNewTaskClass)
            ```
        The `<platform_name>` used here **must** match the `platform` field in your YAML config file and the naming convention of your YAML config file (`<platform_name>.yaml`).

## Leveraging BaseAutomation Functionality

The `BaseAutomation` class provides a suite of methods to simplify web interaction. You can access these methods via `self.bridge` and directly from `self` (for helper functions like `_navigate`).

### Key Browser Interaction Methods (via `self.bridge` indirectly):

*   `await self._navigate(url: str)`: Navigates the browser to the specified URL.
*   `await self._type(selector: str, value: str)`: Types text into an element identified by a CSS selector.
*   `await self._click(selector: str)`: Clicks an element identified by a CSS selector.
*   `await self._scroll_to_bottom()`: Scrolls the current page to the bottom (useful for infinite scroll).
*   `await self._extract_current_page() -> List[Dict]`: Extracts structured data (search results) from the current page.
*   `await self._extract_links() -> List[str]`: Extracts all `href` attributes from anchor tags (`<a>`) on the current page.
*   `await self._wait_for_results()`: Waits for the `results_container` selector (defined in config) to appear.
*   `await self._click_next_page() -> bool`: Clicks the `next_page_button` (defined in config) if it exists.

### Iteration Strategies:

`BaseAutomation` offers powerful methods to handle different types of content iteration:

*   `await self.iterate_results(strategy: str, callback: Callable[[List[Dict]], None], max_items: Optional[int] = None) -> List[Dict]`
    *   `strategy`: Can be `"pagination"`, `"infinite_scroll"`, or `"depth"`. This corresponds to the `settings.iteration.type` in your config.
    *   `callback`: A function that will be called with a list of extracted items from each page/scroll.
    *   `max_items`: Optional limit on the total number of items to collect.

### Utility Methods:

*   `await self._with_retry(coro, retries: int = 3, backoff_factor: float = 1.0)`: Retries a given coroutine with exponential backoff on failure.
*   `await self._with_rate_limit()`: Applies rate-limiting delays based on settings in your YAML config.

## Step-by-Step Task Creation Process

Follow these steps to create and integrate a new automation task:

1.  **Define Task Goal & Scope:**
    *   Clearly understand what data you want to collect or what actions you want to automate.
    *   Identify the target website and the specific pages/flows involved.

2.  **Identify Web Elements & Actions:**
    *   Using browser developer tools, identify the CSS selectors for all necessary elements:
        *   Navigation links/buttons
        *   Input fields (search boxes, forms)
        *   Buttons (submit, next page)
        *   Containers for results or data to be extracted
        *   Specific data points within results (e.g., title, URL, snippet)

3.  **Create `config/<platform_name>.yaml`:**
    *   Create a new YAML file in the `config/` directory.
    *   Fill in the `platform`, `base_url`, `selectors` (using the selectors identified in step 2), and appropriate `settings` for iteration and rate limiting.

4.  **Create `src/brain/tasks/your_new_task_module.py`:**
    *   Create a new Python file in `src/brain/tasks/`.
    *   Define your task class, inheriting from `BaseAutomation`.
    *   Implement the `async def execute` method. Use the `self._navigate`, `self._type`, `self._click`, `iterate_results`, and `_extract_current_page` (or other bridge-interaction methods) as needed to achieve your task's goal. Remember to use `self.config['selectors']['your_element_name']` to access your defined selectors.

5.  **Register Task in `src/brain/tasks/__init__.py`:**
    *   Open `src/brain/tasks/__init__.py`.
    *   Add an import statement for your new task class.
    *   Add a call to `AutomationFactory.register("<platform_name>", YourNewTaskClass)`.

6.  **Test Your New Task:**
    *   Implement a testing mechanism to ensure your task performs as expected. This might involve running the main application with your new task or writing a dedicated test script that instantiates and runs your task.

## Example: DuckDuckGo Search Task

The existing `DuckDuckGoTask` in `src/brain/tasks/duckduckgo.py` and its corresponding `config/duckduckgo.yaml` serve as a practical example of these principles in action. It defines selectors for search input, results, and pagination (using "load more" button), includes configurable timeouts and scroll-before-click functionality, then uses the `_navigate`, `_type`, and `iterate_results` methods to perform a search and extract paginated results.