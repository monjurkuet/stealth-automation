import asyncio
import time
from src.brain.base import BaseAutomation
from typing import Dict
import logging

# Create module-level logger
logger = logging.getLogger(__name__)


class DuckDuckGoTask(BaseAutomation):
    """
    DuckDuckGo search automation task.
    Supports paginated result extraction.
    """

    async def execute(self, query: str, **kwargs) -> Dict:
        """
        Execute DuckDuckGo search.

        Args:
            query: Search query string
            **kwargs: Additional options (max_items, max_pages, etc.)

        Returns:
            Standardized result dictionary
        """
        start_time = time.time()

        try:
            logger.info(f"Starting DuckDuckGo search: {query}")
            await self.progress.emit("task_start", {"query": query})

            url = self.config.get("base_url", "https://duckduckgo.com/")
            await self._navigate(url)

            search_input = self.config["selectors"]["search_input"]
            await self._type(search_input, query)

            await asyncio.sleep(2)

            all_results = []

            def page_callback(items):
                all_results.extend(items)
                logger.debug(f"Collected {len(items)} items from page")

            await self.iterate_results(
                strategy="pagination",
                callback=page_callback,
                max_items=kwargs.get("max_items"),
            )

            duration_ms = int((time.time() - start_time) * 1000)
            summary = {
                "query": query,
                "total_items": len(all_results),
                "pages_processed": self.pages_processed + 1,
                "duration_ms": duration_ms,
            }
            await self.storage.append_summary(self.platform, summary)

            await self.progress.emit("task_complete", summary)

            return {
                "status": "success",
                "platform": self.platform,
                "action": "search",
                "data": {"results": all_results},
                "performance": {
                    "duration_ms": duration_ms,
                    "items_per_second": len(all_results) / (duration_ms / 1000)
                    if duration_ms > 0
                    else 0,
                },
            }

        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            await self.storage.append_error(
                self.platform,
                {"code": type(e).__name__, "message": str(e), "query": query},
            )

            return {
                "status": "error",
                "platform": self.platform,
                "action": "search",
                "error": {"code": type(e).__name__, "message": str(e)},
            }
