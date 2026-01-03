from abc import ABC, abstractmethod
import asyncio
import random
import yaml
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from src.bridge.native import NativeBridge
from src.brain.utils.retry import with_retry
from src.brain.utils.storage import JSONLStorage
from src.brain.utils.progress import ProgressTracker
from src.brain.utils.validation import validate_config

logger = logging.getLogger(__name__)


class BaseAutomation(ABC):
    """
    Abstract base class for all automation tasks.
    Implements common functionality: retry, rate limiting, storage, progress.
    """

    def __init__(self, bridge: NativeBridge, platform: str):
        self.bridge = bridge
        self.platform = platform
        self.config = self._load_config(platform)
        validate_config(self.config)

        output_file = self._get_output_filename()
        self.storage = JSONLStorage(output_file)
        self.progress = ProgressTracker(platform)

        self.current_url = None
        self.items_collected = 0
        self.pages_processed = 0

    def _load_config(self, platform: str) -> Dict:
        """Load configuration from YAML file."""
        config_path = Path(f"config/{platform}.yaml")
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def _get_output_filename(self) -> str:
        """Generate timestamped output filename."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"output/results/{self.platform}_{timestamp}.jsonl"
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        return filename

    @abstractmethod
    async def execute(self, query: str, **kwargs) -> Dict:
        """
        Main entry point for automation task.
        Must be implemented by all subclasses.
        """
        pass

    async def iterate_results(
        self,
        strategy: str,
        callback: Callable[[List[Dict]], None],
        max_items: Optional[int] = None,
    ) -> List[Dict]:
        """
        Execute iteration strategy (pagination, infinite_scroll, depth).
        """
        if strategy == "pagination":
            return await self._iterate_pagination(callback, max_items)
        elif strategy == "infinite_scroll":
            return await self._iterate_infinite(callback, max_items)
        elif strategy == "depth":
            return await self._iterate_depth(callback, max_items)
        else:
            raise ValueError(f"Unknown iteration strategy: {strategy}")

    async def _iterate_pagination(
        self, callback: Callable[[List[Dict]], None], max_items: Optional[int] = None
    ) -> List[Dict]:
        """Paginated iteration (page 1, 2, 3...)."""
        results = []
        max_pages = self.config["settings"]["iteration"].get("max_pages", 5)

        for page in range(1, max_pages + 1):
            await self.progress.emit(
                "page_progress",
                {
                    "current_page": page,
                    "max_pages": max_pages,
                    "items_so_far": len(results),
                },
            )

            await self._wait_for_results()
            items = await self._extract_current_page()
            if items:
                results.extend(items)

            for item in items:
                await self.storage.append_item(self.platform, item)

            if items:
                callback(items)

            max_items = max_items or self.config["settings"]["iteration"].get(
                "max_items", 50
            )
            if len(results) >= max_items:
                break

            if not await self._click_next_page():
                break

            self.pages_processed += 1
            await self._with_rate_limit()

        return results

    async def _iterate_infinite(
        self, callback: Callable[[List[Dict]], None], max_items: Optional[int] = None
    ) -> List[Dict]:
        """Infinite scroll iteration."""
        results = []
        last_count = 0
        same_count_threshold = 3
        same_count_counter = 0

        max_items = max_items or self.config["settings"]["iteration"].get(
            "max_items", 50
        )

        while len(results) < max_items:
            await self._scroll_to_bottom()
            scroll_delay = (
                self.config["settings"]["iteration"].get("scroll_delay_ms", 1000) / 1000
            )
            await asyncio.sleep(scroll_delay)

            items = await self._extract_current_page()

            if len(items) == last_count:
                same_count_counter += 1
                if same_count_counter >= same_count_threshold:
                    break
            else:
                same_count_counter = 0
                last_count = len(items)

                new_items = items[len(results) :]
                for item in new_items:
                    await self.storage.append_item(self.platform, item)

                if new_items:
                    callback(new_items)

                await self.progress.emit(
                    "scroll_progress",
                    {"items_so_far": len(items), "max_items": max_items},
                )

            results = items
            await self._with_rate_limit()

        return results[:max_items]

    async def _iterate_depth(
        self, callback: Callable[[List[Dict]], None], max_items: Optional[int] = None
    ) -> List[Dict]:
        """Depth-first traversal (visit all linked pages)."""
        from collections import deque

        results = []
        max_depth = self.config["settings"]["iteration"].get("max_depth", 2)
        same_domain_only = self.config["settings"]["iteration"].get(
            "same_domain_only", True
        )
        max_items = max_items or self.config["settings"]["iteration"].get(
            "max_items", 30
        )

        base_url = self.current_url or self.config.get("base_url", "")
        if not base_url:
            raise ValueError("base_url is required for depth traversal")

        queue = deque([(base_url, 0)])
        visited = set()

        while queue and len(results) < max_items:
            url, depth = queue.popleft()

            if url in visited or depth > max_depth:
                continue

            visited.add(url)

            if same_domain_only:
                base_domain = self._extract_domain(base_url)
                if not self._is_same_domain(url, base_domain):
                    continue

            await self._navigate(url)
            delay = (
                self.config["settings"]["rate_limiting"].get("page_load_delay_ms", 2000)
                / 1000
            )
            await asyncio.sleep(delay)

            items = await self._extract_current_page()
            if items:
                results.extend(items)

            for item in items:
                await self.storage.append_item(self.platform, item)

            if items:
                callback(items)

            await self.progress.emit(
                "depth_progress",
                {
                    "current_depth": depth,
                    "max_depth": max_depth,
                    "pages_visited": len(visited),
                    "items_so_far": len(results),
                },
            )

            if depth < max_depth:
                links = await self._extract_links()
                for link in links:
                    queue.append((link, depth + 1))

            await self._with_rate_limit()

        return results

    async def _with_retry(
        self, coro, retries: int = 3, backoff_factor: float = 1.0
    ) -> Any:
        """Retry with exponential backoff."""
        return await with_retry(coro, retries, backoff_factor)

    async def _with_rate_limit(self):
        """Apply rate limiting delays."""
        delay = (
            self.config["settings"]["rate_limiting"].get("action_delay_ms", 500) / 1000
        )

        if self.config["settings"]["rate_limiting"].get("randomize_delay", False):
            delay *= random.uniform(0.8, 1.2)

        await asyncio.sleep(delay)

    async def _wait_for_results(self):
        """Wait for results container to appear."""
        selector = self.config["selectors"].get("results_container")

        wait_id = self.bridge.send_command(
            {"action": "wait_for_selector", "selector": selector, "timeout": 10000}
        )

        result = self.bridge.get_result(wait_id)
        if result.get("status") != "success":
            raise TimeoutError(f"Timeout waiting for results: {selector}")

    async def _navigate(self, url: str):
        """Navigate to URL."""
        navigate_id = self.bridge.send_command({"action": "navigate", "url": url})

        result = self.bridge.get_result(navigate_id)
        if result.get("status") != "success":
            raise Exception(f"Navigation failed: {url}")

        self.current_url = url

        delay = (
            self.config["settings"]["rate_limiting"].get("page_load_delay_ms", 2000)
            / 1000
        )
        await asyncio.sleep(delay)

    async def _type(self, selector: str, value: str):
        """Type text into element."""
        type_id = self.bridge.send_command(
            {"action": "type", "selector": selector, "value": value}
        )

        result = self.bridge.get_result(type_id)
        if result.get("status") != "success":
            raise Exception(f"Typing failed: {selector}")

        await self._with_rate_limit()

    async def _click(self, selector: str):
        """Click element."""
        click_id = self.bridge.send_command({"action": "click", "selector": selector})

        result = self.bridge.get_result(click_id)
        if result.get("status") != "success":
            raise Exception(f"Click failed: {selector}")

        await self._with_rate_limit()

    async def _scroll_to_bottom(self):
        """Scroll page to bottom."""
        self.bridge.send_command({"action": "scroll_to_bottom"})

    async def _extract_current_page(self) -> List[Dict]:
        """Extract items from current page."""
        extract_id = self.bridge.send_command({"action": "extract_search_results"})

        result = self.bridge.get_result(extract_id)
        if result.get("status") == "success":
            data = result.get("data", [])
            if isinstance(data, list):
                return data
        return []

    async def _extract_links(self) -> List[str]:
        """Extract links from current page."""
        extract_id = self.bridge.send_command(
            {"action": "extract_urls", "selector": "a[href]"}
        )

        result = self.bridge.get_result(extract_id)
        if result.get("status") == "success":
            data = result.get("data", [])
            if isinstance(data, list):
                return data
        return []

    async def _click_next_page(self) -> bool:
        """Click next page button if exists."""
        selector = self.config["selectors"].get("next_page_button")
        if not selector:
            return False

        check_id = self.bridge.send_command(
            {"action": "wait_for_selector", "selector": selector, "timeout": 2000}
        )

        result = self.bridge.get_result(check_id)
        if result.get("status") != "success":
            return False

        await self._click(selector)
        return True

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse

        return urlparse(url).netloc

    @staticmethod
    def _is_same_domain(url: str, domain: str) -> bool:
        """Check if URL is from same domain."""
        from urllib.parse import urlparse

        return urlparse(url).netloc == domain
